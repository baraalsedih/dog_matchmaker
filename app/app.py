import streamlit as st
import json
from pathlib import Path
import sys
from PIL import Image
# add project root (one level up from this file) to sys.path so `utils` imports resolve
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from utils.matching import load_breeds, top_k_matches
from utils.normalize import normalize_for_folder

# CONFIG: match this to where your images are stored
# Use absolute paths based on ROOT to ensure they work on Streamlit Cloud
IMAGES_DIR = ROOT / "data" / "images"
MAPPING_FILE = ROOT / "data" / "breed_to_folder.json"

st.set_page_config(page_title="Dog Matchmaker", layout="wide")
st.title("🐕 Dog Matchmaker — find your perfect pup")

# load mapping
if MAPPING_FILE.exists():
    mapping = json.load(open(MAPPING_FILE, encoding="utf8"))
else:
    mapping = {}

# load breeds dataframe
df = load_breeds(str(ROOT / 'data' / 'breed_traits.csv'))

def is_valid_image(img_path):
    """
    Check if a file is a valid image that can be opened by PIL.
    Returns True if valid, False otherwise.
    """
    if not img_path or not img_path.exists():
        return False
    try:
        # Try to open and verify the image
        with Image.open(img_path) as img:
            img.verify()  # Verify it's a valid image (this closes the file)
        # Reopen for actual use (verify() closes the file)
        with Image.open(img_path) as img:
            img.load()  # Load the image data to ensure it's readable
        return True
    except Exception:
        return False

def get_first_image_for_breed(breed):
    """
    Returns Path object of the first image for the given breed or None.
    Uses data/breed_to_folder.json mapping, then normalization fallback.
    """
    folder_name = mapping.get(breed)
    if not folder_name:
        folder_name = normalize_for_folder(breed)

    folder_path = IMAGES_DIR / folder_name
    if not folder_path.exists():
        # try without ' dog'
        alt = folder_name.replace(' dog','')
        folder_path = IMAGES_DIR / alt
        if not folder_path.exists():
            return None

    # Check for images with case-insensitive matching (Linux is case-sensitive)
    # Try all case variations of common image extensions
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG', 
                  '*.Jpg', '*.Jpeg', '*.Png', '*.JpG', '*.JpEg', '*.PnG']
    for ext in extensions:
        files = sorted(folder_path.glob(ext))
        for file in files:
            if is_valid_image(file):
                return file
    # Fallback: try to find any image file if exact patterns don't match
    all_files = list(folder_path.iterdir())
    image_files = [f for f in all_files if f.is_file() and 
                   f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    for file in sorted(image_files):
        if is_valid_image(file):
            return file
    return None

# Simple UI: form for preferences (keep your previous form or replace with this)
with st.form("pref_form"):
    st.header("Tell me about your lifestyle")
    activity = st.slider("Activity level (1 = couch, 5 = very active)", 1, 5, 3)
    home = st.selectbox("Home type", ['apartment','house'])
    children = st.radio("Young children in home?", ['No','Yes']) == 'Yes'
    allergies = st.radio("Any dog allergies in home?", ['No','Yes']) == 'Yes'
    time_train = st.slider("Time/effort for training (1 = little, 5 = lots)",1,5,3)
    size = st.selectbox("Preferred size (optional)", ['no preference','small','medium','large'])
    submitted = st.form_submit_button("Find my matches")

if submitted:
    prefs = {
        'activity_level': activity,
        'home': home,
        'children': children,
        'allergies': allergies,
        'time_for_training': time_train,
        'size_pref': None if size=='no preference' else size
    }
    results = top_k_matches(df, prefs, k=3)
    st.subheader("Top matches for you")
    cols = st.columns(3)
    for i, (_, row) in enumerate(results.iterrows()):
        col = cols[i]
        col.markdown(f"### {row['breed']}  — score {row['score']:.2f}")
        img_path = get_first_image_for_breed(row['breed'])
        if img_path and img_path.exists():
            try:
                # Use absolute path string for Streamlit
                col.image(str(img_path.resolve()), use_column_width=True)
            except Exception as e:
                # If image fails to load, show placeholder instead of crashing
                col.write("_Image unavailable for this breed._")
        else:
            col.write("_No image found — check mapping for this breed._")
        # short bullets
        reasons = []
        reasons.append(f"Energy: {row['energy']} / 5")
        reasons.append(f"Trainability: {row['trainability']} / 5")
        reasons.append(f"Good with kids: {row.get('good_with_kids',3)} / 5")
        col.write('\n'.join(f"- {r}" for r in reasons))
