# utils/normalize.py
import re
import unicodedata

def normalize_for_folder(name: str) -> str:
    """
    Normalize a breed name into the folder format used in your images directory.
    Example: "Labrador Retriever" -> "labrador retriever dog"
    """
    if name is None:
        return ""
    # remove accents
    s = unicodedata.normalize('NFKD', str(name)).encode('ascii','ignore').decode('ascii')
    s = s.lower().strip()

    # handle some known patterns and plurals (add more rules here as needed)
    s = re.sub(r'\bretrievers\b', 'retriever', s)
    s = re.sub(r'\bdogs\b', 'dog', s)
    s = re.sub(r'\bterriers\b', 'terrier', s)
    s = re.sub(r'\bpointers\b', 'pointer', s)
    # fix parenthesis like "Retrievers (Labrador)" -> "labrador retriever"
    s = re.sub(r'retrievers?\s*\(\s*labrador\s*\)', 'labrador retriever', s)
    s = re.sub(r'retrievers?\s*\(\s*golden\s*\)', 'golden retriever', s)

    # remove punctuation except hyphen and spaces (some folders have hyphens)
    s = re.sub(r'[^\w\s\-]', '', s)

    # collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()

    # ensure trailing " dog" when not present (most folders have it)
    if not s.endswith(' dog'):
        s = s + ' dog'
    return s
