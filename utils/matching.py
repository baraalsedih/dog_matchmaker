import pandas as pd
import numpy as np
from utils.normalize import normalize_for_folder

def load_breeds(path='data/breed_traits.csv'):
    df = pd.read_csv(path)
    # Ensure numeric columns exist as ints
    for col in ['Energy Level','Trainability Level','Good With Young Children','Shedding Level','Coat Grooming Frequency','Good For Apartment','Playfulness Level','Barking Level','Affectionate With Family','Adaptability Level','Mental Stimulation Needs']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(3).astype(int)
    # normalize/alias names for the app
    df = df.rename(columns={
        'Breed':'breed',
        'Energy Level':'energy',
        'Trainability Level':'trainability',
        'Good With Young Children':'good_with_kids',
        'Shedding Level':'shedding',
        'Coat Grooming Frequency':'grooming',
        'Good For Apartment':'good_for_apartment',
        'Barking Level':'barking',
        'Playfulness Level':'playfulness',
        'Affectionate With Family':'affection',
        'Adaptability Level':'adaptability',
        'Mental Stimulation Needs':'mental_needs'
    })
    # If hypoallergenic info isn't available, derive from low shedding + grooming high? (approx)
    if 'hypoallergenic' not in df.columns:
        df['hypoallergenic'] = df['shedding'] <= 2
    return df

def score_breeds(df, prefs, weights=None):
    """
    prefs: dict
      - activity_level: 1..5
      - home: 'apartment' or 'house'
      - children: True/False
      - allergies: True/False
      - time_for_training: 1..5
      - size_pref: 'small'/'medium'/'large'/None
      - shedding_tolerance: 'low'/'med'/'high'/None
    """
    if weights is None:
        weights = {
            'activity': 3.0,
            'home': 2.0,
            'children': 2.0,
            'allergies': 2.5,
            'training_time': 2.0,
            'size': 1.0
        }

    scores = []
    for _, r in df.iterrows():
        s = 0.0
        wsum = 0.0

        # activity
        if prefs.get('activity_level') is not None:
            diff = abs(prefs['activity_level'] - r['energy'])
            s_act = max(0, 1 - diff / 4.0)
            s += s_act * weights['activity']
            wsum += weights['activity']

        # home/apartment
        if prefs.get('home') is not None:
            want_apartment = (prefs['home']=='apartment')
            apt_score = r.get('good_for_apartment', 3)/5.0
            s_home = apt_score if want_apartment else (1 - apt_score + 0.5)  # houses prefer higher-yard breeds
            s += s_home * weights['home']
            wsum += weights['home']

        # children
        if prefs.get('children') is not None:
            if prefs['children']:
                s_child = r.get('good_with_kids',3)/5.0
            else:
                s_child = 1.0
            s += s_child * weights['children']
            wsum += weights['children']

        # allergies
        if prefs.get('allergies') is not None:
            if prefs['allergies']:
                s_allergy = 1.0 if r.get('hypoallergenic',False) else (0.6 if r.get('shedding',3)<=2 else 0.1)
            else:
                s_allergy = 1.0
            s += s_allergy * weights['allergies']
            wsum += weights['allergies']

        # training time
        if prefs.get('time_for_training') is not None:
            # if user has high time -> prefer high trainability
            t = prefs['time_for_training']
            train_score = r.get('trainability',3)/5.0
            if t >= 4:
                s_train = train_score
            elif t >= 3:
                s_train = 0.8*train_score + 0.2*(1-train_score)
            else:
                # user low time -> prefer moderate-low trainability (less demanding)
                s_train = 1 - 0.6*train_score
            s += s_train * weights['training_time']
            wsum += weights['training_time']

        # size pref
        if prefs.get('size_pref') is not None and 'Size' in r.index:
            size = r.get('Size','medium').lower()
            s_size = 1.0 if prefs['size_pref']==size else 0.5
            s += s_size * weights['size']
            wsum += weights['size']

        # final normalized score
        final = s/(wsum+1e-9)
        scores.append(final)

    df_scores = df.copy()
    df_scores['score'] = scores
    df_scores = df_scores.sort_values('score', ascending=False)
    return df_scores

def top_k_matches(df, prefs, k=3):
    scored = score_breeds(df, prefs)
    return scored.head(k)