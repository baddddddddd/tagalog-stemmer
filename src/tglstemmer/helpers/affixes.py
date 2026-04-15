import os

script_dir = os.path.dirname(os.path.realpath(__file__))


def get_affixes(
    affix_type: str, folder_path=os.path.join(script_dir, "../resources/affixes/")
) -> tuple:
    try:
        with open(
            os.path.join(folder_path, f"{affix_type}fixes.txt"), "r", encoding="utf-8"
        ) as in_file:
            # Sort by length descending to match longest affixes first
            return tuple(
                sorted(
                    [affix.strip() for affix in in_file if affix.strip()],
                    key=len,
                )
            )
    except FileNotFoundError:
        return ()


PREFIXES = get_affixes("pre")
INFIXES = get_affixes("in")
SUFFIXES = get_affixes("suf")
CONTRACTIONS = frozenset(["ng", "g", "'t", "'y"])
