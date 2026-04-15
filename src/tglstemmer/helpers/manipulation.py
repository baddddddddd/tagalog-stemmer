def replace_letter(token_str: str, index: int, letter: str) -> str:
    """Replaces a letter in a string."""
    return (
        token_str[:index] + letter + token_str[index + 1 :]
        if index != -1
        else token_str[:-1] + letter
    )


def swap_letters(token_str: str, index1: int, index2: int) -> str:
    """Swaps two letters in a string efficiently."""
    token_list = list(token_str)
    token_list[index1], token_list[index2] = token_list[index2], token_list[index1]
    return "".join(token_list)
