import os
from collections import defaultdict

script_dir = os.path.dirname(os.path.realpath(__file__))


def get_words(file_path=os.path.join(script_dir, "../resources/wordlist.txt")) -> set:
    try:
        with open(file_path, "r", encoding="utf-8") as in_file:
            return {word.strip().lower() for word in in_file}
    except FileNotFoundError:
        return set()


def get_roots(
    file_path=os.path.join(script_dir, "../resources/rootlist.txt")
) -> defaultdict:
    res = defaultdict(float)
    try:
        with open(file_path, "r", encoding="utf-8") as in_file:
            for line in in_file:
                line = line.strip()
                if not line:
                    continue
                word, score = line.split()
                res[word.strip().lower()] = float(score)
    except FileNotFoundError:
        pass
    return res
