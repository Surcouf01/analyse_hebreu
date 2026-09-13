"""Résolution d'une référence de verset en nœud Text-Fabric.

Accepte les formes usuelles : "Genèse 1:1", "Genèse 1.1", "Genesis 1:1",
"Gen 1:1", "Gen 1,1", "Gn 1:1", ou les noms anglais/latins des livres.
"""

import re

# Alias de livres : français, abrégés français, anglais, latin, hébreu.
_BOOK_ALIASES = {
    # Genesis
    "genese": "Genesis", "genèse": "Genesis", "genese": "Genesis",
    "gen": "Genesis", "gn": "Genesis", "genesis": "Genesis",
    "bereshit": "Genesis", "בראשית": "Genesis",
    # Exodus
    "exode": "Exodus", "ex": "Exodus", "exod": "Exodus", "exodus": "Exodus",
    "shemot": "Exodus", "שמות": "Exodus",
    # Leviticus
    "levitique": "Leviticus", "lévitique": "Leviticus", "lev": "Leviticus",
    "lv": "Leviticus", "leviticus": "Leviticus", "wayyiqra": "Leviticus",
    "ויקרא": "Leviticus",
    # Numbers
    "nombres": "Numbers", "nb": "Numbers", "num": "Numbers",
    "numbers": "Numbers", "bemidbar": "Numbers", "במדבר": "Numbers",
    # Deuteronomy
    "deuteronomique": "Deuteronomy", "deutéronome": "Deuteronomy",
    "deuteronome": "Deuteronomy", "dt": "Deuteronomy", "de": "Deuteronomy",
    "deut": "Deuteronomy", "deuteronomy": "Deuteronomy", "devarim": "Deuteronomy",
    "דברים": "Deuteronomy",
    # Joshua
    "josue": "Joshua", "josué": "Joshua", "jos": "Joshua", "joshua": "Joshua",
    "yehoshua": "Joshua", "יהושע": "Joshua",
    # Judges
    "juges": "Judges", "jg": "Judges", "judg": "Judges", "judges": "Judges",
    "shofetim": "Judges", "שופטים": "Judges",
    # Samuel
    "samuel": "Samuel_I", "1 samuel": "Samuel_I", "1sam": "Samuel_I",
    "1s": "Samuel_I", "i samuel": "Samuel_I", "1 s": "Samuel_I",
    "2 samuel": "Samuel_II", "2sam": "Samuel_II", "2s": "Samuel_II",
    "ii samuel": "Samuel_II", "2 s": "Samuel_II",
    # Kings
    "1 rois": "Kings_I", "1roi": "Kings_I", "1k": "Kings_I", "1r": "Kings_I",
    "i rois": "Kings_I", "1 k": "Kings_I", "kings_i": "Kings_I",
    "2 rois": "Kings_II", "2roi": "Kings_II", "2k": "Kings_II", "2r": "Kings_II",
    "ii rois": "Kings_II", "2 k": "Kings_II", "kings_ii": "Kings_II",
    # Isaiah
    "esaie": "Isaiah", "ésaïe": "Isaiah", "es": "Isaiah", "isa": "Isaiah",
    "isaiah": "Isaiah", "yeshayahu": "Isaiah", "ישעיה": "Isaiah",
    # Jeremiah
    "jeremie": "Jeremiah", "jérémie": "Jeremiah", "jer": "Jeremiah",
    "jeremiah": "Jeremiah", "yirmiyahu": "Jeremiah", "ירמיה": "Jeremiah",
    # Ezekiel
    "ezechiel": "Ezekiel", "ézéchiel": "Ezekiel", "ez": "Ezekiel",
    "ezek": "Ezekiel", "ezekiel": "Ezekiel", "yechezkel": "Ezekiel",
    "יחזקאל": "Ezekiel",
    # Psalms
    "psaumes": "Psalms", "psaume": "Psalms", "ps": "Psalms", "psalm": "Psalms",
    "psalms": "Psalms", "tehillim": "Psalms", "תהילים": "Psalms",
    # Proverbs
    "proverbes": "Proverbs", "prov": "Proverbs", "pr": "Proverbs",
    "proverbs": "Proverbs", "mishle": "Proverbs", "משלי": "Proverbs",
    # Job
    "job": "Job", "iyov": "Job", "איוב": "Job",
    # Song
    "cantique": "Song_of_Songs", "cant": "Song_of_Songs", "cantique_des_cantiques": "Song_of_Songs",
    "song": "Song_of_Songs", "song_of_songs": "Song_of_Songs",
    # Ruth
    "ruth": "Ruth", "rut": "Ruth", "רות": "Ruth",
    # Lamentations
    "lamentations": "Lamentations", "lam": "Lamentations",
    "lamentations": "Lamentations", "eikha": "Lamentations", "איכה": "Lamentations",
    # Ecclesiastes
    "ecclesiaste": "Ecclesiastes", "ecclésiaste": "Ecclesiastes",
    "eccl": "Ecclesiastes", "qo": "Ecclesiastes", "qohelet": "Ecclesiastes",
    "ecclesiastes": "Ecclesiastes", "קהלת": "Ecclesiastes",
    # Esther
    "esther": "Esther", "est": "Esther", "es": "Esther", "אסתר": "Esther",
    # Daniel
    "daniel": "Daniel", "da": "Daniel", "dan": "Daniel", "דניאל": "Daniel",
    # Ezra / Nehemiah
    "esdras": "Ezra", "ezr": "Ezra", "ezra": "Ezra", "עזרא": "Ezra",
    "nehemie": "Nehemiah", "néhémie": "Nehemiah", "ne": "Nehemiah",
    "neh": "Nehemiah", "nehemiah": "Nehemiah", "נחמיה": "Nehemiah",
    # Chronicles
    "1 chroniques": "Chronicles_I", "1chr": "Chronicles_I", "1ch": "Chronicles_I",
    "1chroniques": "Chronicles_I", "i chroniques": "Chronicles_I",
    "2 chroniques": "Chronicles_II", "2chr": "Chronicles_II", "2ch": "Chronicles_II",
    "2chroniques": "Chronicles_II", "ii chroniques": "Chronicles_II",
    # Minor prophets
    "oshee": "Hosea", "osee": "Hosea", "os": "Hosea", "ho": "Hosea",
    "hosea": "Hosea", "hoshéa": "Hosea", "הושע": "Hosea",
    "joel": "Joel", "jo": "Joel", "jl": "Joel", "joël": "Joel", "יואל": "Joel",
    "amos": "Amos", "am": "Amos", "עמוס": "Amos",
    "abdias": "Obadiah", "ob": "Obadiah", "obad": "Obadiah", "obadiah": "Obadiah",
    "jonas": "Jonah", "jon": "Jonah", "jonah": "Jonah", "יונה": "Jonah",
    "michee": "Micah", "michée": "Micah", "mi": "Micah", "micah": "Micah",
    "mic": "Micah", "מיכה": "Micah",
    "nahum": "Nahum", "na": "Nahum", "nah": "Nahum", "נחום": "Nahum",
    "habacuc": "Habakkuk", "hab": "Habakkuk", "habakkuk": "Habakkuk",
    "חבקוק": "Habakkuk",
    "sophonie": "Zephaniah", "soph": "Zephaniah", "zep": "Zephaniah",
    "zephaniah": "Zephaniah", "צפניה": "Zephaniah",
    "aggée": "Haggai", "aggee": "Haggai", "ag": "Haggai", "hag": "Haggai",
    "haggai": "Haggai", "חגי": "Haggai",
    "zacharie": "Zechariah", "zc": "Zechariah", "zech": "Zechariah",
    "zechariah": "Zechariah", "זכריה": "Zechariah",
    "malachie": "Malachi", "mal": "Malachi", "malachi": "Malachi", "מלאכי": "Malachi",
}

_REF_RE = re.compile(
    r"""^\s*
    (?P<book>[^0-9]+?)         # nom du livre (y compris "1 ")
    \s*
    (?P<chapter>\d+)
    \s*[:\.,]\s*
    (?P<verse>\d+)
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)


def normalize_book(raw):
    """Normalise un nom de livre vers le nom BHSA attendu."""
    key = raw.strip().lower()
    key = re.sub(r"\s+", " ", key)
    # Gestion des préfixes "1"/"2"/"I"/"II" collés : "1samuel" -> "1 samuel"
    m = re.match(r"^([12]|i{1,2})\s*(.+)", key)
    if m and key not in _BOOK_ALIASES:
        prefix = m.group(1)
        rest = m.group(2)
        prefix_map = {"1": "1", "2": "2", "i": "1", "ii": "2"}
        key = f"{prefix_map[prefix]} {rest}"
    if key in _BOOK_ALIASES:
        return _BOOK_ALIASES[key]
    # Cas : nom BHSA direct (anglais) comme "Genesis"
    titled = raw.strip().title()
    return titled


def parse_reference(ref):
    """Analyse une référence et renvoie (book_bhsa, chapter, verse) ou None."""
    m = _REF_RE.match(ref)
    if not m:
        return None
    book = normalize_book(m.group("book"))
    chapter = int(m.group("chapter"))
    verse = int(m.group("verse"))
    return book, chapter, verse


def find_verse(F, L, book, chapter, verse):
    """Renvoie le nœud de verset correspondant, ou None."""
    for v in F.otype.s("verse"):
        if F.chapter.v(v) == chapter and F.verse.v(v) == verse:
            book_node = L.u(v, "book")[0]
            if F.book.v(book_node) == book:
                return v
    return None


def book_list(F):
    """Renvoie la liste des noms de livres disponibles dans la base."""
    return sorted({F.book.v(b) for b in F.otype.s("book")})
