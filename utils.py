"""
utils.py
"""

def persian_to_english(text: str) -> str:
    """
    Convert Persian digits in text to English digits.
    """
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    converted = text.translate(translation_table)
    return ''.join(c for c in converted if c.isdigit())
