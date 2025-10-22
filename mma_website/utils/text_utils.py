import unicodedata

def row_to_dict(row):
    """Convert SQLAlchemy row to dictionary"""
    return {key: value for key, value in row._mapping.items()}

def normalize_ascii(text):
    """Normalize text to ASCII for search functionality"""
    if text is None:
        return ""
    
    # First normalize using unicodedata
    text = unicodedata.normalize('NFKD', text)
    
    # Custom character mappings for common non-ASCII characters
    char_map = {
        'ł': 'l', 'Ł': 'L',  # Polish ł
        'ć': 'c', 'Ć': 'C',  # Polish ć
        'ś': 's', 'Ś': 'S',  # Polish ś
        'ź': 'z', 'Ź': 'Z',  # Polish ź
        'ż': 'z', 'Ż': 'Z',  # Polish ż
        'ą': 'a', 'Ą': 'A',  # Polish ą
        'ę': 'e', 'Ę': 'E',  # Polish ę
        'ó': 'o', 'Ó': 'O',  # Polish ó
        'ń': 'n', 'Ń': 'N',  # Polish ń
        'č': 'c', 'Č': 'C',  # Czech č
        'ć': 'c', 'Ć': 'C',  # Serbian ć
        'đ': 'd', 'Đ': 'D',  # Serbian đ
        'š': 's', 'Š': 'S',  # Serbian š
        'ž': 'z', 'Ž': 'Z',  # Serbian ž
    }
    
    # Replace special characters
    for special, ascii_char in char_map.items():
        text = text.replace(special, ascii_char)
    
    # Convert to ASCII and lowercase
    return text.encode('ascii', 'ignore').decode('ascii').lower() 