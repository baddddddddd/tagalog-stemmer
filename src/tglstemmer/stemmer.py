"""This module provides functions to perform Tagalog stemming on word/s."""

import os
import re
import heapq
from functools import lru_cache
from tabulate import tabulate
from typing import Optional

from .helpers.alphabet import VOWELS, CONSONANTS
from .helpers.validation import is_valid, is_acceptable, is_vowel, is_consonant
from .helpers.manipulation import swap_letters
from .helpers.affixes import PREFIXES, INFIXES, SUFFIXES, CONTRACTIONS

from .stem import Stem, valid_words, root_words

script_dir = os.path.dirname(os.path.realpath(__file__))

WORD_SPLIT_PATTERN = r"[\w']+(?:-\w+)*|[^\w\s]|\n"
word_split_regex = re.compile(WORD_SPLIT_PATTERN, re.UNICODE)


def _split_to_words(text: str) -> list[str]:
    return word_split_regex.findall(text)


def prune(tokens: list[Stem], k: int = 10) -> list[Stem]:
    if len(tokens) <= k:
        return sorted(tokens, key=lambda x: x.get_sorting_key())
    return heapq.nsmallest(k, tokens, key=lambda x: x.get_sorting_key())


def get_stems(
    text: str, valid_words_list: Optional[set[str]] = valid_words
) -> list[str]:
    return [get_stem(token).word for token in _split_to_words(text)]


@lru_cache(maxsize=1_000_000)
def get_stem(token_str: str) -> Stem:
    cleaned_word = token_str.strip().lower()
    token = Stem(cleaned_word)

    candidates = get_stem_candidates(cleaned_word)
    if not candidates:
        return token

    return prune(candidates, 1)[0]


def get_stem_candidates(word: str) -> list[Stem]:
    token = Stem(word, original_word=word)

    if word in root_words:
        return [token]

    stems = [token]

    stems = apply_stemming(
        functions=(
            stem_dup,
            stem_pre,
            stem_rep,
            stem_inf,
            stem_rep,
            stem_suf,
            stem_dup,
        ),
        tokens=stems,
    )

    return stems if stems else [token]


def apply_stemming(functions: tuple, tokens: list[Stem]) -> list[Stem]:
    for f in functions:
        new_tokens = []
        new_tokens.extend(f(tokens))
        tokens = prune(tokens + new_tokens)
    return tokens


def stem_pre(tokens: list[Stem]) -> list[Stem]:
    stems = []
    for token in tokens:
        word = token.word
        for prefix in PREFIXES:
            if len(word) <= len(prefix) or not word.startswith(prefix):
                continue

            stem_word = word[len(prefix) :]
            if stem_word.startswith("-"):
                stem_word = stem_word[1:]

            if len(stem_word) <= 1:
                continue

            stem = token.copy_with(word=stem_word, pre=prefix)
            stems.append(stem)

            # Phoneme change (d/r)
            if stem_word[0] == "r" and is_vowel(stem_word[1]) and is_vowel(prefix[-1]):
                stems.append(
                    stem.copy_with(word="d" + stem_word[1:], phoneme_change="pre: d/r")
                )

            if not is_vowel(stem_word[0]) or not is_acceptable(stem_word):
                continue

            # Assimilation
            if prefix.endswith("ng"):
                stems.append(
                    stem.copy_with(word="k" + stem_word, assimilation="k/null")
                )
                stems.append(
                    stem.copy_with(word="p" + stem_word, assimilation="p/null")
                )

                if (
                    len(stem_word) >= 4
                    and stem_word[1:3] == "ng"
                    and stem_word[0] == stem_word[3]
                ):
                    stems.append(stem.copy_with(word=stem_word[3:], rep=stem_word[:3]))
                    if is_acceptable(stem_word[3:]):
                        stems.append(
                            stem.copy_with(
                                word="k" + stem_word[3:],
                                rep=stem_word[:3],
                                assimilation="k/null",
                            )
                        )
                        # stems.append(
                        #     stem.copy_with(
                        #         word="p" + stem_word[3:],
                        #         rep=stem_word[:3],
                        #         assimilation="p/null",
                        #     )
                        # )

            elif prefix.endswith("m"):
                for l in "bp":
                    stems.append(
                        stem.copy_with(word=l + stem_word, assimilation=f"b/p: {l}")
                    )
                if (
                    len(stem_word) >= 3
                    and stem_word[1] == "m"
                    and stem_word[0] == stem_word[2]
                ):
                    for l in "bp":
                        stems.append(
                            stem.copy_with(
                                word=l + stem_word[2:],
                                rep=stem_word[:3],
                                assimilation=f"b/p: {l}",
                            )
                        )

            elif prefix.endswith("n"):
                for l in "st":
                    stems.append(
                        stem.copy_with(word=l + stem_word, assimilation=f"s/t: {l}")
                    )
                if (
                    len(stem_word) >= 3
                    and stem_word[1] == "n"
                    and stem_word[0] == stem_word[2]
                ):
                    for l in "st":
                        stems.append(
                            stem.copy_with(
                                word=l + stem_word[2:],
                                rep=stem_word[:3],
                                assimilation=f"s/t: {l}",
                            )
                        )

            if prefix in ("na", "ma", "ka") and stem_word.startswith("ng"):
                stems.append(
                    stem.copy_with(word="pa" + stem_word, assimilation="ng/pang")
                )

    return stems


def stem_inf(tokens: list[Stem]) -> list[Stem]:
    stems = []
    for token in tokens:
        word = token.word
        if len(word) < 4:
            continue

        for infix in INFIXES:
            stem_word = None
            if word.startswith(infix) and is_vowel(word[2]):
                stem_word = word[2:]
            elif is_consonant(word[0]) and word[1:3] == infix:
                stem_word = word[0] + word[3:]
            elif (
                len(word) > 4
                and word[2:4] == infix
                and is_consonant(word[:2])
                and is_vowel(word[4])
            ):
                stem_word = word[0:2] + word[4:]
            elif (
                len(word) > 5
                and word[3:5] == infix
                and is_consonant(word[:3])
                and is_vowel(word[5])
            ):
                stem_word = word[0:3] + word[5:]

            if stem_word:
                stems.append(token.copy_with(word=stem_word, inf=infix))
    return stems


def stem_suf(tokens: list[Stem]) -> list[Stem]:
    stems = []
    for token in tokens:
        word = token.word
        for suffix in SUFFIXES:
            if len(word) <= len(suffix) or not word.endswith(suffix):
                continue

            stem_word = word[: -len(suffix)]
            possibilities = [stem_word]

            if (
                len(stem_word) >= 2
                and is_vowel(suffix[0])
                and stem_word[-1] in ("n", "h")
                and is_vowel(stem_word[-2])
            ):
                possibilities.append(stem_word[:-1])

            for sw in possibilities:
                is_contraction = len(suffix) <= 2 and suffix in CONTRACTIONS
                if is_contraction:
                    if suffix == "g" and sw[-1] != "n":
                        continue
                    if not is_vowel(sw[-1]) and suffix in ("'t", "'y"):
                        continue
                    base_stem = token.copy_with(word=sw, contraction=suffix)
                else:
                    base_stem = token.copy_with(word=sw, suf=suffix)

                stems.append(base_stem)

                last_vowel_idx = next(
                    (i for i in range(len(sw) - 1, -1, -1) if is_vowel(sw[i])), -1
                )

                if last_vowel_idx != -1:
                    if sw[last_vowel_idx] == "u":
                        stems.append(
                            base_stem.copy_with(
                                word=sw[:last_vowel_idx]
                                + "o"
                                + sw[last_vowel_idx + 1 :],
                                phoneme_change="suf: o/u",
                            )
                        )
                    elif sw[last_vowel_idx] == "i":
                        stems.append(
                            base_stem.copy_with(
                                word=sw[:last_vowel_idx]
                                + "e"
                                + sw[last_vowel_idx + 1 :],
                                phoneme_change="suf: e/i",
                            )
                        )

                if sw[-1] == "r" and suffix in ("in", "an"):
                    dr_word = sw[:-1] + "d"
                    dr_stem = base_stem.copy_with(
                        word=dr_word, phoneme_change="suf: d/r"
                    )
                    stems.append(dr_stem)

                    last_v_idx_dr = next(
                        (
                            i
                            for i in range(len(dr_word) - 1, -1, -1)
                            if is_vowel(dr_word[i])
                        ),
                        -1,
                    )
                    if last_v_idx_dr != -1 and dr_word[last_v_idx_dr] == "u":
                        stems.append(
                            dr_stem.copy_with(
                                word=dr_word[:last_v_idx_dr]
                                + "o"
                                + dr_word[last_v_idx_dr + 1 :],
                                phoneme_change="suf: d/r, o/u",
                            )
                        )

                if sw[-1] == "n" and suffix in ("in", "an"):
                    hn_stem = base_stem.copy_with(
                        word=sw[:-1] + "h", phoneme_change="suf: h/n"
                    )
                    stems.append(hn_stem)
                    stems.extend(stem_vowel_loss([hn_stem]))

                    # Phoneme change for ng/n (fixes dinatnan -> dating)
                    ng_stem = base_stem.copy_with(
                        word=sw[:-1] + "ng", phoneme_change="suf: ng/n"
                    )
                    stems.append(ng_stem)
                    stems.extend(stem_vowel_loss([ng_stem]))

                if sw.endswith("ngg"):
                    stems.append(
                        base_stem.copy_with(
                            word=sw[:-3] + "nig", phoneme_change="ngg/nig"
                        )
                    )

                if len(sw) < 2 or not is_acceptable(sw):
                    continue

                stems.extend(stem_vowel_loss([base_stem]))

                mtts_word = swap_letters(sw, -1, -2)
                mtts_stem = base_stem.copy_with(word=mtts_word, metathesis=True)
                if is_valid(mtts_word, valid_words):
                    stems.append(mtts_stem)
                else:
                    stems.extend(stem_vowel_loss([mtts_stem]))

    return stems


def stem_vowel_loss(tokens: list[Stem]) -> list[Stem]:
    stems = []
    for token in tokens:
        word = token.word
        for vowel in VOWELS:
            if len(word) > 1:
                cand = word + vowel
                if is_valid(cand, valid_words):
                    stems.append(token.copy_with(word=cand, vowel_loss=vowel))
            if len(word) > 2:
                cand = word[:-1] + vowel + word[-1]
                if is_valid(cand, valid_words):
                    stems.append(token.copy_with(word=cand, vowel_loss=vowel))
    return stems


def stem_rep(tokens: list[Stem]) -> list[Stem]:
    stems = []
    for token in tokens:
        word = token.word.replace("-", "")

        # Starts with a vowel (V-V) (e.g. aalis => alis)
        if len(word) > 2 and word[0] == word[1] and is_vowel(word[0:2]):
            stems.append(token.copy_with(word=word[1:], rep=word[0]))

        # d/r repetition (e.g. darating => dating)
        elif (
            len(word) > 4
            and word[0] == "d"
            and word[2] == "r"
            and word[1] == word[3]
            and is_vowel(word[1])
        ):
            stems.append(
                token.copy_with(
                    word=word[0] + word[3:], rep=word[:2], phoneme_change="rep: d/r"
                )
            )

        # Starts with a consonant-vowel (CV-CV) (e.g. bibili => bili)
        elif len(word) > 4 and word[0:2] == word[2:4] and is_consonant(word[0]):
            stems.append(token.copy_with(word=word[2:], rep=word[:2]))

        # Taglish 2-consonant clusters
        elif len(word) > 5:
            # CV-CCV (e.g. cecheck)
            if (
                word[0] == word[2]
                and word[1] == word[4]
                and is_consonant(word[0])
                and is_vowel(word[1])
            ):
                stems.append(token.copy_with(word=word[2:], rep=word[:2]))

            # CC-CCV (e.g. chcheck => check)
            elif (
                word[0:2] == word[2:4] and is_consonant(word[0:2]) and is_vowel(word[4])
            ):
                stems.append(token.copy_with(word=word[2:], rep=word[:2]))

            # CCV-CCV (e.g. checheck => check)
            elif (
                word[0:2] == word[3:5] and is_consonant(word[0:2]) and is_vowel(word[2])
            ):
                stems.append(token.copy_with(word=word[3:], rep=word[:3]))

    return stems


def stem_dup(tokens: list[Stem]) -> list[Stem]:
    stems = []
    for token in tokens:
        arr = token.word.split("-")
        if len(arr) != 2:
            continue

        first, second = arr
        first_len, second_len = len(first), len(second)
        if first_len <= 1 or second_len <= 1 or first_len < second_len:
            continue

        len_diff = first_len - second_len
        if len_diff > 2:
            continue

        contraction = ""
        if len_diff == 2 and first[-2:] in ("ng", "'t"):
            contraction, first = first[-2:], first[:-2]
        elif len_diff == 1 and first[-1] == "t":
            contraction, first = "'t", first[:-1]

        phoneme_change = token.phoneme_change
        if first[-1] == "u" and second[-1] == "o":
            first = first[:-1] + "o"
            phoneme_change = "dup: o/u"

        if first == second:
            stems.append(
                token.copy_with(
                    word=first,
                    dup=first,
                    contraction=contraction,
                    phoneme_change=phoneme_change,
                )
            )

    return stems
