"""Client léger pour l'API Sefaria (https://www.sefaria.org).

Objectif : donner à l'application un accès direct aux ressources Sefaria,
notamment aux traductions françaises de la Bible hébraïque — en particulier
la **Bible du Rabbinat 1899** (domaine public, version Sefaria « Bible du
Rabbinat 1899 [fr] », source fr.wikisource.org) — pour enrichir la
traduction française des sens par binyan (``binyan_senses_fr_en.json``).

Sefaria ne fournit **aucun lexique hébreu→français** (BDB, Jastrow, Klein,
Sefer HaShorashim… sont tous en anglais ou en hébreu) : l'interfaçage passe
donc par les traductions françaises du texte biblique, utilisées comme
contexte d'occurrence des racines verbales.

Caractéristiques :
  - uniquement la bibliothèque standard (``urllib.request``, ``json``) ;
  - cache disque (JSON) pour éviter de re-télécharger les versets ;
  - délai d'attente et erreurs réseau tolérés : hors-ligne, le client
    renvoie ``None`` sans lever d'exception (les fonctions de l'app
    retombent sur les sources locales) ;
  - respect de l'API : une seule requête HTTP par chapitre demandé.

Usage :
    from bhsa_grammar.sefaria_client import fetch_verse_fr, clear_cache

    verse = fetch_verse_fr("Genesis", 1, 1)
    # -> "Au commencement, Dieu créa le ciel et la terre."
"""

import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request

# Traduction française de référence sur Sefaria : la Bible du Rabbinat
# 1899, la seule version française **domaine public** de la plateforme.
# (Les autres versions FR — Chouraqui, Zadoc Kahn, Cahen — y sont aussi
# présentes mais leur licence est inconnue ou restrictive.)
RABBINAT_TITLE = "Bible du Rabbinat 1899 [fr]"

# Base de l'API v3 de Sefaria (format ``language|versionTitle`` pour
# demander une version précise d'un texte).
_API_BASE = "https://www.sefaria.org/api/v3/texts/"

# Délai d'attente réseau par défaut (secondes).
DEFAULT_TIMEOUT = 15.0

# Racine du cache disque : ``SEFARIA_CACHE`` surchargeable via
# l'environnement, sinon un dossier temporaire dédié.
def _cache_path():
    env = os.environ.get("SEFARIA_CACHE")
    if env:
        return env
    return os.path.join(tempfile.gettempdir(), "analyse_hebreu_sefaria_cache")


# Correspondance nom BHSA (forme latine) -> titre Sefaria du livre.
BHSA_TO_SEFARIA = {
    "Genesis": "Genesis",
    "Exodus": "Exodus",
    "Leviticus": "Leviticus",
    "Numeri": "Numbers",
    "Deuteronomium": "Deuteronomy",
    "Josua": "Joshua",
    "Judices": "Judges",
    "Samuel_I": "1 Samuel",
    "Samuel_II": "2 Samuel",
    "Reges_I": "1 Kings",
    "Reges_II": "2 Kings",
    "Jesaia": "Isaiah",
    "Jeremia": "Jeremiah",
    "Ezechiel": "Ezekiel",
    "Hosea": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadia": "Obadiah",
    "Jona": "Jonah",
    "Micha": "Micah",
    "Nahum": "Nahum",
    "Habakuk": "Habakkuk",
    "Zephania": "Zephaniah",
    "Haggai": "Haggai",
    "Sacharia": "Zechariah",
    "Maleachi": "Malachi",
    "Psalmi": "Psalms",
    "Iob": "Job",
    "Proverbia": "Proverbs",
    "Ruth": "Ruth",
    "Canticum": "Song of Songs",
    "Ecclesiastes": "Ecclesiastes",
    "Threni": "Lamentations",
    "Esther": "Esther",
    "Daniel": "Daniel",
    "Esra": "Ezra",
    "Nehemia": "Nehemiah",
    "Chronica_I": "1 Chronicles",
    "Chronica_II": "2 Chronicles",
}


class SefariaError(RuntimeError):
    """Erreur d'accès à l'API Sefaria (réseau, format, version absente)."""


class _ChapterCache:
    """Cache disque JSON : (titre de version, livre, chapitre) -> versets."""

    def __init__(self, root=None):
        self.root = root or _cache_path()
        os.makedirs(self.root, exist_ok=True)

    def _file(self, version_title, book, chapter):
        key = f"{version_title}|{book}|{chapter}"
        import hashlib

        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.root, f"chap_{digest}.json")

    def get(self, version_title, book, chapter):
        path = self._file(version_title, book, chapter)
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    def put(self, version_title, book, chapter, verses):
        path = self._file(version_title, book, chapter)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(verses, fh, ensure_ascii=False)
        os.replace(tmp, path)


_CACHE = None


def _get_cache():
    global _CACHE
    if _CACHE is None:
        _CACHE = _ChapterCache()
    return _CACHE


def clear_cache():
    """Vide le cache disque des chapitres déjà téléchargés."""
    global _CACHE
    if _CACHE is not None:
        _CACHE = None
    root = _cache_path()
    if os.path.isdir(root):
        for name in os.listdir(root):
            if name.startswith("chap_") and name.endswith(".json"):
                try:
                    os.remove(os.path.join(root, name))
                except OSError:
                    pass


def _fetch_chapter_json(book_sefaria, chapter, version_title, timeout):
    """Récupère le JSON d'un chapitre entier via l'API v3 de Sefaria."""
    ref = f"{book_sefaria} {chapter}"
    version = urllib.parse.quote(f"french|{version_title}")
    url = (f"{_API_BASE}{urllib.parse.quote(ref)}"
           f"?version={version}&return_format=text_only")
    req = urllib.request.Request(url, headers={"User-Agent": "analyse_hebreu/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    versions = data.get("versions") or []
    if not versions:
        raise SefariaError(
            f"Version « {version_title} » absente de Sefaria pour {ref}"
        )
    return versions[0].get("text") or []


def fetch_chapter_verses_fr(book, chapter, version_title=RABBINAT_TITLE,
                             timeout=DEFAULT_TIMEOUT, use_cache=True):
    """Renvoie la liste des versets français d'un chapitre (index 0 = v. 1).

    ``book`` est un nom BHSA (Genesis, Reges_I…) ou un titre Sefaria.
    Renvoie ``None`` si le chapitre est indisponible (hors-ligne, erreur
    réseau, livre non couvert) — jamais d'exception.
    """
    book_sefaria = BHSA_TO_SEFARIA.get(book, book)
    cache = _get_cache()
    if use_cache and cache:
        cached = cache.get(version_title, book_sefaria, chapter)
        if cached is not None:
            return cached
    try:
        verses = _fetch_chapter_json(book_sefaria, chapter, version_title,
                                     timeout)
    except (SefariaError, OSError, ValueError, urllib.error.URLError):
        return None
    flat = []
    for item in verses:
        if isinstance(item, str):
            flat.append(item)
        elif isinstance(item, list):
            flat.extend(s for s in item if isinstance(s, str))
        # les segments non-chaînes (notes de bas de page) sont ignorés
    if use_cache and cache:
        cache.put(version_title, book_sefaria, chapter, flat)
    return flat


def fetch_verse_fr(book, chapter, verse, version_title=RABBINAT_TITLE,
                    timeout=DEFAULT_TIMEOUT, use_cache=True):
    """Renvoie le texte français d'un verset, ou ``None``.

    Le chapitre entier est récupéré en une requête puis mis en cache :
    les versets suivants du même chapitre ne déclenchent pas de nouvel
    appel réseau.
    """
    verses = fetch_chapter_verses_fr(book, chapter, version_title,
                                     timeout, use_cache)
    if not verses or not (1 <= verse <= len(verses)):
        return None
    text = verses[verse - 1]
    if not isinstance(text, str) or not text.strip():
        return None
    return text.strip()


def offline():
    """Renvoie True si l'API Sefaria est actuellement injoignable."""
    verses = fetch_chapter_verses_fr("Genesis", 1, use_cache=False)
    return verses is None
