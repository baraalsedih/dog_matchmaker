import pandas as pd
import numpy as np
from utils.normalize import normalize_for_folder

def load_breeds(path='data/breed_traits.csv'):
    df = pd.read_csv(path)
    # Ensure numeric columns exist as ints
    numeric_cols = ['Energy Level','Trainability Level','Good With Young Children',
                    'Shedding Level','Coat Grooming Frequency','Drooling Level',
                    'Openness To Strangers','Playfulness Level','Barking Level',
                    'Affectionate With Family','Adaptability Level','Mental Stimulation Needs',
                    'Watchdog/Protective Nature','Good With Other Dogs']
    for col in numeric_cols:
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
        'Drooling Level':'drooling',
        'Good For Apartment':'good_for_apartment',
        'Barking Level':'barking',
        'Playfulness Level':'playfulness',
        'Affectionate With Family':'affection',
        'Adaptability Level':'adaptability',
        'Mental Stimulation Needs':'mental_needs',
        'Openness To Strangers':'openness',
        'Watchdog/Protective Nature':'watchdog',
        'Good With Other Dogs':'good_with_dogs'
    })
    # If hypoallergenic info isn't available, derive from low shedding
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
      - shedding_tolerance: 1..5 (1=low tolerance, 5=high tolerance)
      - grooming_tolerance: 1..5 (1=low maintenance, 5=high maintenance)
      - drooling_tolerance: 1..5 (1=low tolerance, 5=high tolerance)
      - barking_tolerance: 1..5 (1=quiet preferred, 5=ok with barking)
      - playfulness_pref: 1..5 (1=calm, 5=very playful)
      - affection_pref: 1..5 (1=independent, 5=very affectionate)
      - other_dogs: True/False (have other dogs)
      - openness_pref: 1..5 (1=protective, 5=friendly to strangers)
      - mental_stimulation: 1..5 (1=low needs, 5=high needs)
    """
    if weights is None:
        weights = {
            'activity': 3.0,
            'home': 2.0,
            'children': 2.0,
            'allergies': 2.5,
            'training_time': 2.0,
            'size': 1.0,
            'shedding': 1.5,
            'grooming': 1.5,
            'drooling': 2.0,  # High CV feature - very useful for matching
            'barking': 1.5,
            'playfulness': 1.5,
            'affection': 1.5,
            'other_dogs': 2.0,
            'openness': 1.0,
            'mental_stimulation': 1.0
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

        # shedding tolerance
        if prefs.get('shedding_tolerance') is not None:
            user_tolerance = prefs['shedding_tolerance']  # 1=low tolerance, 5=high tolerance
            breed_shedding = r.get('shedding', 3)
            # If user has low tolerance (1-2), prefer low shedding (1-2)
            # If user has high tolerance (4-5), any shedding is fine
            if user_tolerance <= 2:
                s_shed = max(0, 1 - abs(breed_shedding - 1) / 4.0)
            else:
                s_shed = 1.0 - (breed_shedding - 1) / 4.0 * 0.3  # slight preference for lower
            s += s_shed * weights['shedding']
            wsum += weights['shedding']

        # grooming tolerance
        if prefs.get('grooming_tolerance') is not None:
            user_tolerance = prefs['grooming_tolerance']  # 1=low maintenance, 5=high maintenance
            breed_grooming = r.get('grooming', 3)
            diff = abs(user_tolerance - breed_grooming)
            s_groom = max(0, 1 - diff / 4.0)
            s += s_groom * weights['grooming']
            wsum += weights['grooming']

        # drooling tolerance (high CV feature - very useful for matching)
        if prefs.get('drooling_tolerance') is not None:
            user_tolerance = prefs['drooling_tolerance']  # 1=low tolerance, 5=high tolerance
            breed_drooling = r.get('drooling', 3)
            # If user has low tolerance (1-2), prefer low drooling (1-2)
            # If user has high tolerance (4-5), any drooling is fine
            if user_tolerance <= 2:
                s_drool = max(0, 1 - abs(breed_drooling - 1) / 4.0)
            else:
                s_drool = 1.0 - (breed_drooling - 1) / 4.0 * 0.3  # slight preference for lower
            s += s_drool * weights['drooling']
            wsum += weights['drooling']

        # barking tolerance
        if prefs.get('barking_tolerance') is not None:
            user_tolerance = prefs['barking_tolerance']  # 1=quiet preferred, 5=ok with barking
            breed_barking = r.get('barking', 3)
            # If user wants quiet (1-2), prefer low barking (1-2)
            # If user is ok with barking (4-5), any level is fine
            if user_tolerance <= 2:
                s_bark = max(0, 1 - abs(breed_barking - 1) / 4.0)
            else:
                s_bark = 1.0 - (breed_barking - 1) / 4.0 * 0.2
            s += s_bark * weights['barking']
            wsum += weights['barking']

        # playfulness preference
        if prefs.get('playfulness_pref') is not None:
            user_pref = prefs['playfulness_pref']
            breed_play = r.get('playfulness', 3)
            diff = abs(user_pref - breed_play)
            s_play = max(0, 1 - diff / 4.0)
            s += s_play * weights['playfulness']
            wsum += weights['playfulness']

        # affection preference
        if prefs.get('affection_pref') is not None:
            user_pref = prefs['affection_pref']
            breed_affection = r.get('affection', 3)
            diff = abs(user_pref - breed_affection)
            s_aff = max(0, 1 - diff / 4.0)
            s += s_aff * weights['affection']
            wsum += weights['affection']

        # other dogs
        if prefs.get('other_dogs') is not None:
            if prefs['other_dogs']:
                s_dogs = r.get('good_with_dogs', 3) / 5.0
            else:
                s_dogs = 1.0  # no preference if no other dogs
            s += s_dogs * weights['other_dogs']
            wsum += weights['other_dogs']

        # openness to strangers
        if prefs.get('openness_pref') is not None:
            user_pref = prefs['openness_pref']  # 1=protective, 5=friendly
            breed_openness = r.get('openness', 3)
            diff = abs(user_pref - breed_openness)
            s_open = max(0, 1 - diff / 4.0)
            s += s_open * weights['openness']
            wsum += weights['openness']

        # mental stimulation needs
        if prefs.get('mental_stimulation') is not None:
            user_needs = prefs['mental_stimulation']
            breed_needs = r.get('mental_needs', 3)
            diff = abs(user_needs - breed_needs)
            s_mental = max(0, 1 - diff / 4.0)
            s += s_mental * weights['mental_stimulation']
            wsum += weights['mental_stimulation']

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