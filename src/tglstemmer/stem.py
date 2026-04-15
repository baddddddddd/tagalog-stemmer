"""This module provides a fast data structure to store Tagalog stems."""

from typing import Optional
from .helpers.words import get_words, get_roots
from .helpers.validation import is_consonant, is_vowel

valid_words = get_words()
valid_words.add("split")
root_words = get_roots()


class Stem:
    """A lightweight slot-based class to represent stem candidates."""

    __slots__ = [
        "word",
        "original_word",
        "pre",
        "inf",
        "suf",
        "rep",
        "dup",
        "contraction",
        "phoneme_change",
        "assimilation",
        "vowel_loss",
        "metathesis",
    ]

    def __init__(
        self,
        word: str,
        original_word: Optional[str] = None,
        pre: str = "",
        inf: str = "",
        suf: str = "",
        rep: str = "",
        dup: str = "",
        contraction: str = "",
        phoneme_change: str = "",
        assimilation: str = "",
        vowel_loss: str = "",
        metathesis: bool = False,
    ):
        self.word = word
        self.original_word = original_word if original_word is not None else word
        self.pre = pre
        self.inf = inf
        self.suf = suf
        self.rep = rep
        self.dup = dup
        self.contraction = contraction
        self.phoneme_change = phoneme_change
        self.assimilation = assimilation
        self.vowel_loss = vowel_loss
        self.metathesis = metathesis

    def copy_with(self, word=None, **kwargs):
        """Creates a fast copy of the current stem with updated attributes."""
        return Stem(
            word=word if word is not None else self.word,
            original_word=self.original_word,
            pre=kwargs.get("pre", self.pre),
            inf=kwargs.get("inf", self.inf),
            suf=kwargs.get("suf", self.suf),
            rep=kwargs.get("rep", self.rep),
            dup=kwargs.get("dup", self.dup),
            contraction=kwargs.get("contraction", self.contraction),
            phoneme_change=kwargs.get("phoneme_change", self.phoneme_change),
            assimilation=kwargs.get("assimilation", self.assimilation),
            vowel_loss=kwargs.get("vowel_loss", self.vowel_loss),
            metathesis=kwargs.get("metathesis", self.metathesis),
        )

    def count_affix_length(self) -> int:
        return len(self.pre) + len(self.inf) + len(self.suf) + len(self.contraction)

    def count_redup_length(self) -> int:
        return len(self.rep)

    def is_weird_prefix(self) -> bool:
        if not self.pre:
            return False
        if is_consonant(self.pre[-1]) and is_vowel(self.word[0]):
            return self.pre + "-" not in self.original_word
        return False

    def is_missed_redup(self) -> bool:
        if self.rep or not self.pre:
            return False
        return self.pre[-2:] == self.word[:2]

    def is_weird_short_word(self) -> bool:
        n = len(self.word)
        if n >= 4:
            return False
        if n <= 1:
            return True
        vowels = sum(1 for c in self.word if is_vowel(c))
        consonants = n - vowels
        return consonants >= vowels if n <= 2 else consonants > vowels

    def get_sorting_key(self) -> tuple:
        return (
            self.word not in valid_words,
            bool(self.metathesis),
            bool(self.vowel_loss),
            bool(self.assimilation),
            -root_words.get(self.word, 0.0),
            self.is_weird_prefix(),
            self.is_missed_redup(),
            self.is_weird_short_word(),
            -self.count_affix_length(),
            -self.count_redup_length(),
            bool(self.phoneme_change),
            abs(len(self.word) - 4),
            self.word,
        )

    def __str__(self):
        return self.word

    def __repr__(self):
        return f"Stem({self.word})"
