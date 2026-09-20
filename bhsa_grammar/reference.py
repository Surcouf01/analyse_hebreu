"""Résolution d'une référence de verset en nœud Text-Fabric.

Accepte les formes usuelles : "Genèse 1:1", "Genèse 1.1", "Genesis 1:1",
"Gen 1:1", "Gen 1,1", "Gn 1:1", ou les noms anglais/latins des livres.
"""

import re

# Alias de livres : français, abrégés français, anglais, latin, hébreu.
# Toutes les cibles sont les noms BHSA réels (forme latine, cf. base ETCBC).
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
    # Numbers -> Numeri
    "nombres": "Numeri", "nb": "Numeri", "num": "Numeri",
    "numbers": "Numeri", "numeri": "Numeri", "bemidbar": "Numeri",
    "במדבר": "Numeri",
    # Deuteronomy -> Deuteronomium
    "deuteronomique": "Deuteronomium", "deutéronome": "Deuteronomium",
    "deuteronome": "Deuteronomium", "dt": "Deuteronomium", "de": "Deuteronomium",
    "deut": "Deuteronomium", "deuteronomy": "Deuteronomium",
    "deuteronomium": "Deuteronomium", "devarim": "Deuteronomium",
    "דברים": "Deuteronomium",
    # Joshua -> Josua
    "josue": "Josua", "josué": "Josua", "jos": "Josua", "joshua": "Josua",
    "josua": "Josua", "yehoshua": "Josua", "יהושע": "Josua",
    # Judges -> Judices
    "juges": "Judices", "jg": "Judices", "judg": "Judices",
    "judges": "Judices", "judices": "Judices", "shofetim": "Judices",
    "שופטים": "Judices",
    # Samuel (déjà correct)
    "samuel": "Samuel_I", "1 samuel": "Samuel_I", "1sam": "Samuel_I",
    "1s": "Samuel_I", "i samuel": "Samuel_I", "1 s": "Samuel_I",
    "samuel_i": "Samuel_I",
    "2 samuel": "Samuel_II", "2sam": "Samuel_II", "2s": "Samuel_II",
    "ii samuel": "Samuel_II", "2 s": "Samuel_II", "samuel_ii": "Samuel_II",
    # Kings -> Reges
    "1 rois": "Reges_I", "1roi": "Reges_I", "1k": "Reges_I", "1r": "Reges_I",
    "i rois": "Reges_I", "1 k": "Reges_I", "kings_i": "Reges_I",
    "reges_i": "Reges_I",
    "2 rois": "Reges_II", "2roi": "Reges_II", "2k": "Reges_II", "2r": "Reges_II",
    "ii rois": "Reges_II", "2 k": "Reges_II", "kings_ii": "Reges_II",
    "reges_ii": "Reges_II",
    # Isaiah -> Jesaia
    "esaie": "Jesaia", "ésaïe": "Jesaia", "es": "Jesaia", "isa": "Jesaia",
    "isaiah": "Jesaia", "jesaia": "Jesaia", "yeshayahu": "Jesaia",
    "ישעיה": "Jesaia",
    # Jeremiah -> Jeremia
    "jeremie": "Jeremia", "jérémie": "Jeremia", "jer": "Jeremia",
    "jeremiah": "Jeremia", "jeremia": "Jeremia", "yirmiyahu": "Jeremia",
    "ירמיה": "Jeremia",
    # Ezekiel -> Ezechiel (déjà correct)
    "ezechiel": "Ezechiel", "ézéchiel": "Ezechiel", "ez": "Ezechiel",
    "ezek": "Ezechiel", "ezekiel": "Ezechiel", "yechezkel": "Ezechiel",
    "יחזקאל": "Ezechiel",
    # Psalms -> Psalmi
    "psaumes": "Psalmi", "psaume": "Psalmi", "ps": "Psalmi",
    "psalm": "Psalmi", "psalms": "Psalmi", "psalmi": "Psalmi",
    "tehillim": "Psalmi", "תהילים": "Psalmi",
    # Proverbs -> Proverbia
    "proverbes": "Proverbia", "prov": "Proverbia", "pr": "Proverbia",
    "proverbs": "Proverbia", "proverbia": "Proverbia", "mishle": "Proverbia",
    "משלי": "Proverbia",
    # Job -> Iob
    "job": "Iob", "iyov": "Iob", "iob": "Iob", "איוב": "Iob",
    # Song of Songs -> Canticum
    "cantique": "Canticum", "cant": "Canticum",
    "cantique_des_cantiques": "Canticum", "song": "Canticum",
    "song_of_songs": "Canticum", "canticum": "Canticum", "shir_hashirim": "Canticum",
    "שיר השירים": "Canticum", "שיר_השירים": "Canticum",
    # Ruth (déjà correct)
    "ruth": "Ruth", "rut": "Ruth", "רות": "Ruth",
    # Lamentations -> Threni
    "lamentations": "Threni", "lam": "Threni", "threni": "Threni",
    "eikha": "Threni", "איכה": "Threni",
    # Ecclesiastes (déjà correct)
    "ecclesiaste": "Ecclesiastes", "ecclésiaste": "Ecclesiastes",
    "eccl": "Ecclesiastes", "qo": "Ecclesiastes", "qohelet": "Ecclesiastes",
    "ecclesiastes": "Ecclesiastes", "קהלת": "Ecclesiastes",
    # Esther (déjà correct)
    "esther": "Esther", "est": "Esther", "es": "Esther", "אסתר": "Esther",
    # Daniel (déjà correct)
    "daniel": "Daniel", "da": "Daniel", "dan": "Daniel", "דניאל": "Daniel",
    # Ezra -> Esra
    "esdras": "Esra", "ezr": "Esra", "ezra": "Esra", "esra": "Esra",
    "עזרא": "Esra",
    # Nehemiah -> Nehemia
    "nehemie": "Nehemia", "néhémie": "Nehemia", "ne": "Nehemia",
    "neh": "Nehemia", "nehemiah": "Nehemia", "nehemia": "Nehemia",
    "נחמיה": "Nehemia",
    # Chronicles -> Chronica
    "1 chroniques": "Chronica_I", "1chr": "Chronica_I", "1ch": "Chronica_I",
    "1chroniques": "Chronica_I", "i chroniques": "Chronica_I",
    "chronicles_i": "Chronica_I", "chronica_i": "Chronica_I",
    "2 chroniques": "Chronica_II", "2chr": "Chronica_II", "2ch": "Chronica_II",
    "2chroniques": "Chronica_II", "ii chroniques": "Chronica_II",
    "chronicles_ii": "Chronica_II", "chronica_ii": "Chronica_II",
    # Minor prophets
    "oshee": "Hosea", "osee": "Hosea", "os": "Hosea", "ho": "Hosea",
    "hosea": "Hosea", "hoshéa": "Hosea", "הושע": "Hosea",
    "joel": "Joel", "jo": "Joel", "jl": "Joel", "joël": "Joel",
    "יואל": "Joel",
    "amos": "Amos", "am": "Amos", "עמוס": "Amos",
    # Obadiah -> Obadia
    "abdias": "Obadia", "ob": "Obadia", "obad": "Obadia",
    "obadiah": "Obadia", "obadia": "Obadia", "עובדיה": "Obadia",
    # Jonah -> Jona
    "jonas": "Jona", "jon": "Jona", "jonah": "Jona", "jona": "Jona",
    "יונה": "Jona",
    # Micah -> Micha
    "michee": "Micha", "michée": "Micha", "mi": "Micha", "micah": "Micha",
    "mic": "Micha", "micha": "Micha", "מיכה": "Micha",
    # Nahum (déjà correct)
    "nahum": "Nahum", "na": "Nahum", "nah": "Nahum", "נחום": "Nahum",
    # Habakkuk -> Habakuk
    "habacuc": "Habakuk", "hab": "Habakuk", "habakkuk": "Habakuk",
    "habakuk": "Habakuk", "חבקוק": "Habakuk",
    # Zephaniah -> Zephania (déjà correct)
    "sophonie": "Zephania", "soph": "Zephania", "zep": "Zephania",
    "zephaniah": "Zephania", "zephania": "Zephania", "צפניה": "Zephania",
    # Haggai (déjà correct)
    "aggée": "Haggai", "aggee": "Haggai", "ag": "Haggai", "hag": "Haggai",
    "haggai": "Haggai", "חגי": "Haggai",
    # Zechariah -> Sacharia
    "zacharie": "Sacharia", "zc": "Sacharia", "zech": "Sacharia",
    "zechariah": "Sacharia", "sacharia": "Sacharia", "זכריה": "Sacharia",
    # Malachi -> Maleachi
    "malachie": "Maleachi", "mal": "Maleachi", "malachi": "Maleachi",
    "maleachi": "Maleachi", "מלאכי": "Maleachi",
}

_REF_RE = re.compile(
    r"""^\s*
    (?P<book>.*?)              # nom du livre (peut commencer par "1"/"2"/"I"/"II")
    \s+
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


# Nom français usuel associé à chaque nom BHSA (forme latine).
_BOOK_FR = {
    "Genesis": "Genèse", "Exodus": "Exode", "Leviticus": "Lévitique",
    "Numeri": "Nombres", "Deuteronomium": "Deutéronome",
    "Josua": "Josué", "Judices": "Juges",
    "Samuel_I": "1 Samuel", "Samuel_II": "2 Samuel",
    "Reges_I": "1 Rois", "Reges_II": "2 Rois",
    "Jesaia": "Ésaïe", "Jeremia": "Jérémie", "Ezechiel": "Ézéchiel",
    "Hosea": "Osée", "Joel": "Joël", "Amos": "Amos", "Obadia": "Abdias",
    "Jona": "Jonas", "Micha": "Michée", "Nahum": "Nahum",
    "Habakuk": "Habacuc", "Zephania": "Sophonie", "Haggai": "Aggée",
    "Sacharia": "Zacharie", "Maleachi": "Malachie",
    "Psalmi": "Psaumes", "Iob": "Job", "Proverbia": "Proverbes",
    "Ruth": "Ruth", "Canticum": "Cantique des Cantiques",
    "Ecclesiastes": "Ecclésiaste", "Threni": "Lamentations",
    "Esther": "Esther", "Daniel": "Daniel", "Esra": "Esdras",
    "Nehemia": "Néhémie",
    "Chronica_I": "1 Chroniques", "Chronica_II": "2 Chroniques",
}


def book_french(bhsa_name):
    """Renvoie le nom français usuel d'un livre BHSA, ou le nom BHSA lui-même."""
    return _BOOK_FR.get(bhsa_name, bhsa_name)


def book_list(F):
    """Renvoie la liste des noms de livres disponibles dans la base."""
    return sorted({F.book.v(b) for b in F.otype.s("book")})


def book_list_fr(F):
    """Renvoie une liste ordonnée de (nom BHSA, nom français) pour chaque livre."""
    names = sorted({F.book.v(b) for b in F.otype.s("book")})
    return [(n, book_french(n)) for n in names]
