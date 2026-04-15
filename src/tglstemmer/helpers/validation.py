from .alphabet import VOWELS, CONSONANTS


def is_valid(token: str, valid_words: set = None) -> bool:
    return is_acceptable(token)


def is_acceptable(token: str) -> bool:
    if not token:
        return False

    first_char = token[0]
    length = len(token)

    if is_vowel(first_char):
        if length == 2 or (length >= 3 and any(is_consonant(c) for c in token)):
            return True
    elif is_consonant(first_char):
        if length == 3 or (length >= 4 and any(is_vowel(c) for c in token)):
            return True

    return False


def is_vowel(s: str) -> bool:
    return all(c in VOWELS for c in s)


def is_consonant(s: str) -> bool:
    return all(c in CONSONANTS for c in s)
