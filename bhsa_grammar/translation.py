"""Chargement d'une traduction française indexée par référence.

La traduction est stockée dans un fichier texte plat (UTF-8), un verset par
ligne, au format :

    <nom BHSA>\t<chapitre>\t<verset>\t<texte français>

Exemples :

    Genesis\t1\t1\tAu commencement, Dieu créa les cieux et la terre.
    Reges_I\t22\t53\tIl servit Baal et se prosterna devant lui…

Le nom de livre doit être le nom BHSA (forme latine : Genesis, Exodus,
Reges_I, Psalmi…). Une conversion depuis les noms français est possible via
``bhsa_grammar.reference.normalize_book``.

Le module accepte aussi le format JSON Louis Segond 1910 (structure
``Testaments → Books → Chapters → Verses``) tel que distribué par
juliend2/data-bible (domaine public).

Localisation du fichier (priorité) :
  1. variable d'environnement ``TRANSLATION_DATA`` ;
  2. ``data/louis_segond_1910.txt`` à côté du paquet ;
  3. ``data/louis_segond_1910.json`` à côté du paquet.
"""

import json
import os

from .reference import normalize_book


class TranslationNotFoundError(RuntimeError):
    """Levée quand aucun fichier de traduction n'est trouvé."""


def _candidate_paths():
    paths = []
    env = os.environ.get("TRANSLATION_DATA")
    if env:
        paths.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(here), "data")
    for name in ("louis_segond_1910.txt", "louis_segond_1910.json"):
        paths.append(os.path.join(data_dir, name))
    paths.append(os.path.join(here, "data", name))
    return paths


def _parse_flat(path):
    index = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            book, chap, verse, text = parts[0], parts[1], parts[2], parts[3]
            try:
                chap_i, verse_i = int(chap), int(verse)
            except ValueError:
                continue
            index.setdefault(book, {}).setdefault(chap_i, {})[verse_i] = text
    return index


def _parse_json(path):
    data = json.load(open(path, encoding="utf-8"))
    index = {}
    for t in data.get("Testaments", []):
        for b in t.get("Books", []):
            fr_name = b.get("Text", "")
            bhsa = normalize_book(fr_name)
            for ci, ch in enumerate(b.get("Chapters", []), start=1):
                for vi, v in enumerate(ch.get("Verses", []), start=1):
                    text = (v.get("Text") or "").replace("\t", " ").strip()
                    if text:
                        index.setdefault(bhsa, {}).setdefault(ci, {})[vi] = text
    return index


def load_translation(path=None):
    """Charge et renvoie un index {(book_bhsa): {chap: {verse: texte}}}.

    Si ``path`` est None, cherche automatiquement un fichier de traduction.
    Lève ``TranslationNotFoundError`` si rien n'est trouvé.
    """
    if path:
        candidates = [path]
    else:
        candidates = _candidate_paths()

    for cand in candidates:
        if not cand or not os.path.isfile(cand):
            continue
        if cand.lower().endswith(".json"):
            return _parse_json(cand)
        return _parse_flat(cand)

    raise TranslationNotFoundError(
        "Aucun fichier de traduction trouvé. Placez data/louis_segond_1910.txt "
        "(ou .json) à côté du paquet, ou définissez TRANSLATION_DATA."
    )


def get_translation(index, book, chapter, verse):
    """Renvoie le texte français d'un verset, ou None si absent."""
    book_map = index.get(book)
    if not book_map:
        return None
    return book_map.get(chapter, {}).get(verse)


def has_book(index, book):
    """Indique si la traduction couvre un livre donné."""
    return book in index
