"""Analyseur grammatical de l'hébreu biblique fondé sur la base BHSA (ETCBC).

Usage rapide :

    from bhsa_grammar import load_corpus, analyze_verse_by_reference, format_text
    api = load_corpus()
    analyse = analyze_verse_by_reference(api, "Genèse 1:1")
    print(format_text(analyse))
"""

from .loader import load_corpus, DataNotFoundError
from .reference import parse_reference, find_verse, book_list, book_list_fr, book_french
from .rules import analyze_verse
from .binyan_diag import binyan_diagnostics
from .report import to_text, to_json, to_summary
from .word_analyzer import analyze_word, search_word
from .phrase_analyzer import analyze_phrase
from .report import word_to_text, word_to_json, phrase_to_text, phrase_to_json

__all__ = [
    "load_corpus",
    "DataNotFoundError",
    "parse_reference",
    "find_verse",
    "book_list",
    "book_list_fr",
    "book_french",
    "analyze_verse",
    "analyze_verse_by_reference",
    "binyan_diagnostics",
    "analyze_word",
    "search_word",
    "analyze_phrase",
    "normalize_word",
    "format_text",
    "format_json",
    "format_summary",
    "format_word",
    "format_word_json",
    "format_phrase",
    "format_phrase_json",
]

__version__ = "1.0.0"


def analyze_verse_by_reference(api, reference):
    """Analyse un verset désigné par sa référence (ex. « Genèse 1:1 »)."""
    parsed = parse_reference(reference)
    if parsed is None:
        raise ValueError(f"Référence invalide : {reference!r}")
    book, chapter, verse = parsed
    F, L, T = api.F, api.L, api.T
    node = find_verse(F, L, book, chapter, verse)
    if node is None:
        raise ValueError(
            f"Verset introuvable : {book} {chapter}:{verse}. "
            f"Vérifiez le nom du livre (disponibles : {', '.join(book_list(F))})."
        )
    return analyze_verse(F, L, T, node)


def format_text(analysis, verbose_words=True):
    return to_text(analysis, verbose_words=verbose_words)


def format_json(analysis, indent=2):
    return to_json(analysis, indent=indent)


def format_summary(analysis):
    return to_summary(analysis)


def normalize_word(form):
    """Normalise un mot hébreu (retire les teamim, NFC) hors chargement de base."""
    from .word_analyzer import _normalize
    return _normalize(form)


def format_word(word_analysis):
    return word_to_text(word_analysis)


def format_word_json(word_analysis, indent=2):
    return word_to_json(word_analysis, indent=indent)


def format_phrase(phrase_analysis):
    return phrase_to_text(phrase_analysis)


def format_phrase_json(phrase_analysis, indent=2):
    return phrase_to_json(phrase_analysis, indent=indent)
