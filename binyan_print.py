#!/usr/bin/env python3
"""Impression d'un paradigme de binyan (onglet Binyanim) avec aperçu.

Construit un document imprimable A4 pour UN binyan d'un résultat
d'analyse --binyanim (structure produite par parse_binyanim_text),
le met en pages via Pillow, l'affiche en aperçu (Tkinter) puis
l'imprime ou l'exporte en PDF.

Le rendu de l'hébreu s'adapte au moteur de Pillow : avec libraqm
(Windows, macOS, wheels récentes), la chaîne logique est transmise
telle quelle — raqm applique le bidi et ancre le nikkud sur sa
consonne ; sans raqm (certaines installations Linux), le texte est
converti en ordre visuel (bidi_display.to_visual), Pillow dessinant
les caractères un à un de gauche à droite.
"""

import os
import re
import subprocess
import sys
import tempfile

import bidi_display

# Marques de directionnalité : utiles au widget Tkinter (ordre visuel
# stable), sans effet au dessin Pillow — retirées avant rendu.
_BIDI_MARKS_RE = re.compile("[\u200e\u200f\u202a-\u202e\u2066-\u2069]")

# Moteur de rendu Pillow : avec libraqm (Windows, macOS, wheels récentes),
# le texte logique est mis en forme par raqm (bidi + shaping + ancrage
# correct du nikkud) — le pré-traitement en ordre visuel serait une
# double inversion. Sans raqm (certaines installations Linux), Pillow
# dessine les caractères un à un de gauche à droite : la conversion
# préalable en ordre visuel (bidi_display) reste alors nécessaire.
def _has_raqm():
    try:
        import PIL.features
        return bool(PIL.features.check("raqm"))
    except Exception:
        return False


_RAQM = _has_raqm()

# Ligne de paradigme du texte marqué : «    <libellé>  <forme> »
_ROW_RE = re.compile(r"^ {4}(\S.*?)\s{2,}(\S.*)$")

# Ordre pédagogique des temps (cf. binyanim_to_text).
_TENSE_ORDER = ("perf", "impf", "impv", "juss", "coh")


def _is_mark(ch):
    """Marque combinante hébraïque (nikkud, dagesh…) à largeur nulle."""
    return 0x0591 <= ord(ch) <= 0x05C7 and ch not in ("\u05be", "\u05c0", "\u05c3", "\u05c6")


# Points shin/sin : leur position latérale sur le ש distingue שׁ/שׂ —
# ils ne doivent PAS être recentrés.
_LATERAL_DOTS = ("\u05c1", "\u05c2")


# Encre réelle d'un glyphe : (nom_police, taille, glyphe) -> (x_min, x_max)
# mesurée par rendu (getbbox de la police est trompeur pour certains
# glyphes étroits, ex. le vav dont la chasse dépasse largement l'encre).
_INK_BBOX_CACHE = {}


def _ink_bbox(glyph, font):
    """Bounding box d'encre horizontale d'un glyphe, par rendu (cache).

    Rendu sur une image temporaire et scan des pixels non blancs :
    les métriques getbbox de la police couvrent la chasse complète,
    pas l'encre réelle (le vav est étroit mais sa chasse est large) ;
    centrer sur la chasse posait le shuruq (וּ) à droite du corps du
    vav.
    """
    from PIL import Image, ImageDraw
    key = (getattr(font, "path", None), getattr(font, "size", None), glyph)
    cached = _INK_BBOX_CACHE.get(key)
    if cached is not None:
        return cached
    size = max(8, int(getattr(font, "size", 16)))
    pad = size
    img = Image.new("L", (size * 4 + 2 * pad, size * 3), 255)
    draw = ImageDraw.Draw(img)
    draw.text((pad, size), glyph, font=font, fill=0)
    px = img.load()
    w, h = img.size
    xs = [x for x in range(w) for y in range(h) if px[x, y] < 160]
    if not xs:
        result = (0.0, 0.0)
    else:
        result = (min(xs) - pad, max(xs) - pad)
    _INK_BBOX_CACHE[key] = result
    return result


# Ancrages GPOS de la police : chemin -> {base: {marque: (dx, dy)}} en
# unités upem, indexés par CARACTÈRE (résolus via la cmap de la police :
# les noms de glyphes ne sont pas normalisés — « uni05D5 » dans DejaVu,
# autrement nommé dans Arial, etc.). C'est la position officielle de
# chaque marque (ce qu'HarfBuzz/raqm appliquent) ; sans elle, le repli
# est le centrage d'encre (cf. _mark_offset).
_GPOS_CACHE = {}


def _gpos_path(font):
    """Chemin de fichier de la police (clé de cache), ou None."""
    path = getattr(font, "path", None)
    return path if isinstance(path, str) and path else None


def _gpos_anchors(font):
    """Ancrages mark->base (MarkBasePos) de la police, en upem.

    Renvoie {base: {mark: (dx, dy)}} — dx/dy = décalage de dessin de
    la marque relativement à l'origine de sa consonne (ancre base
    moins ancre marque). None si fontTools est absent, si la police
    n'a pas de table GPOS exploitable ou au premier échec (cache
    négatif : {}).
    """
    path = _gpos_path(font)
    if path is None:
        return None
    if path in _GPOS_CACHE:
        return _GPOS_CACHE[path] or None
    anchors = None
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(path, lazy=False)
        if "GPOS" in tt:
            cmap = tt.getBestCmap()
            gpos = tt["GPOS"].table
            # Lookups mark-to-base du script hébreu, comme HarfBuzz les
            # sélectionne (feature « mark » du script « hebr », repli
            # « DFLT »). Prendre TOUS les lookups de type 4 attraperait
            # des ancrages d'autres scripts/contexts, avec des positions
            # fausses pour l'hébreu.
            feature_indices = []
            for tag in ("hebr", "DFLT"):
                for srec in gpos.ScriptList.ScriptRecord:
                    if srec.ScriptTag != tag:
                        continue
                    default = srec.Script.DefaultLangSys
                    if default:
                        feature_indices = list(default.FeatureIndex)
                        for lrec in (srec.Script.LangSysRecord or []):
                            feature_indices += list(lrec.LangSys.FeatureIndex)
                    break
                if feature_indices:
                    break
            lookup_indices = set()
            for fi in feature_indices:
                if fi >= len(gpos.FeatureList.FeatureRecord):
                    continue
                frec = gpos.FeatureList.FeatureRecord[fi]
                if frec.FeatureTag == "mark":
                    lookup_indices.update(frec.Feature.LookupListIndex)
            lookups = [gpos.LookupList.Lookup[i]
                       for i in sorted(lookup_indices)
                       if i < len(gpos.LookupList.Lookup)]
            if not lookups:
                lookups = [lk for lk in gpos.LookupList.Lookup
                           if lk.LookupType == 4]
            table = {}
            for lookup in lookups:
                if lookup.LookupType != 4:  # MarkBasePos
                    continue
                for sub in lookup.SubTable:
                    marks = sub.MarkCoverage.glyphs
                    bases = sub.BaseCoverage.glyphs
                    for mi, rec in enumerate(sub.MarkArray.MarkRecord):
                        mark = marks[mi] if mi < len(marks) else None
                        if mark is None:
                            continue
                        am = rec.MarkAnchor
                        klass = rec.Class
                        for bi, base in enumerate(bases):
                            recs = sub.BaseArray.BaseRecord
                            if bi >= len(recs):
                                continue
                            ab = recs[bi].BaseAnchor[klass]
                            if ab is None or am is None:
                                continue
                            # Première ancre rencontrée prioritaire (une
                            # même paire peut apparaître dans plusieurs
                            # lookups, l'ordre de HarfBuzz va du plus
                            # spécifique au plus général).
                            table.setdefault(base, {}).setdefault(mark, (
                                ab.XCoordinate - am.XCoordinate,
                                ab.YCoordinate - am.YCoordinate))
            # Indexer par caractère : cmap inverse (glyphe -> codepoint).
            glyph_to_cp = {}
            for cp, gname in cmap.items():
                glyph_to_cp.setdefault(gname, cp)
            anchors = {}
            for base_g, marks_d in table.items():
                bcp = glyph_to_cp.get(base_g)
                if bcp is None:
                    continue
                for mark_g, off in marks_d.items():
                    mcp = glyph_to_cp.get(mark_g)
                    if mcp is None:
                        continue
                    anchors.setdefault(chr(bcp), {})[chr(mcp)] = off
            anchors = anchors or {}
    except Exception:
        anchors = {}
    _GPOS_CACHE[path] = anchors
    return anchors or None


def _mark_offsets(base, marks, font):
    """Décalages (dx, dy) de dessin de CHAQUE marque sur sa consonne.

    Priorité : ancrages GPOS officiels de la police (via fontTools,
    déjà présent avec Pillow) ; sinon centrage de l'encre des marques
    sur celle de la consonne (mesuré par rendu, cf. _ink_bbox).
    Les points shin/sin ne sont jamais déplacés (position latérale).

    Chaque marque reçoit son propre ancrage : dessiner la chaîne
    complète à un offset unique reviendrait à SOMMER les ancres (le
    daguesh U+05BC a une ancre très à gauche, ex. -296 upem sur le
    kaf dans DejaVu) et déporter les voyelles hors de la consonne
    quand un daguesh lene est présent (ex. כְּ) ; HarfBuzz/raqm
    posent chaque marque indépendamment sur la base.
    """
    out = []
    anchors = _gpos_anchors(font)
    entry = anchors.get(base) if anchors and base else None
    scale = getattr(font, "size", 16) / _font_upem(font)
    for ch in marks:
        if ch in _LATERAL_DOTS or not base:
            out.append((ch, 0.0, 0.0))
        elif entry and entry.get(ch) is not None:
            dx, dy = entry[ch]
            out.append((ch, dx * scale, -dy * scale))
        else:
            out.append((ch, None, None))
    if entry and all(off is not None for _ch, off, _dy in out):
        return out
    # Repli : centrage horizontal sur l'encre (comportement précédent).
    centered = "".join(ch for ch in marks if ch not in _LATERAL_DOTS)
    bx0, bx1 = _ink_bbox(base, font)
    mx0, mx1 = _ink_bbox(centered, font)
    base_ink_w = bx1 - bx0
    marks_ink_w = mx1 - mx0
    target = 0.0
    if base and base_ink_w > 0 and marks_ink_w >= 0:
        target = bx0 + (base_ink_w - marks_ink_w) / 2 - mx0
    return [(ch, target, 0.0) for ch in marks]


def _mark_offset(base, marks, font):
    """Décalage (dx, dy) unique du blob de marques (rétro-compatibilité)."""
    centered = "".join(ch for ch in marks if ch not in _LATERAL_DOTS)
    if not centered or not base:
        return 0.0, 0.0
    anchors = _gpos_anchors(font)
    if anchors:
        entry = anchors.get(base)
        if entry:
            dx = dy = None
            for ch in centered:
                off = entry.get(ch)
                if off is not None:
                    dx = off[0] if dx is None else dx + off[0]
                    dy = off[1] if dy is None else dy + off[1]
            if dx is not None:
                scale = getattr(font, "size", 16) / _font_upem(font)
                return dx * scale, -dy * scale
    # Repli : centrage horizontal sur l'encre (comportement précédent).
    bx0, bx1 = _ink_bbox(base, font)
    mx0, mx1 = _ink_bbox(centered, font)
    base_ink_w = bx1 - bx0
    marks_ink_w = mx1 - mx0
    if base_ink_w <= 0 or marks_ink_w < 0:
        return 0.0, 0.0
    target = bx0 + (base_ink_w - marks_ink_w) / 2 - mx0
    return target, 0.0


def _font_upem(font):
    """Unités par em de la police (1000 par défaut), via fontTools."""
    path = _gpos_path(font)
    if path is None:
        return 1000
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(path, lazy=True, fontNumber=0)
        return tt["head"].unitsPerEm or 1000
    except Exception:
        return 1000


def _split_clusters(s):
    """Découpe une chaîne en clusters (consonne + marques qui la portent).

    Renvoie une liste de chaînes ; les marques non combinantes (maqqef,
    nun inversé, grande alef…) et tout ce qui n'est pas une marque
    forment leur propre cluster.
    """
    out = []
    cur = ""
    for ch in s:
        if _is_mark(ch):
            cur += ch
        else:
            if cur:
                out.append(cur)
            cur = ch
    if cur:
        out.append(cur)
    return out


def _is_hebrew_cluster(cluster):
    return any(0x05D0 <= ord(ch) <= 0x05EA for ch in cluster)


def _hebrew_runs(text):
    """Découpe en runs « hébreu » / « autre », dans l'ordre logique.

    Chaque run hébreu est la concaténation de clusters contenant des
    lettres hébraïques ; tout le reste (latin, chiffres, ponctuation,
    espaces) forme des runs « autre ».
    """
    clusters = _split_clusters(text)
    runs = []
    cur = ""
    cur_heb = None
    for cluster in clusters:
        heb = _is_hebrew_cluster(cluster)
        if cur_heb is None or heb == cur_heb:
            cur += cluster
            cur_heb = heb
        else:
            runs.append((cur_heb, cur))
            cur = cluster
            cur_heb = heb
    if cur:
        runs.append((cur_heb, cur))
    return runs


def _run_width(draw, run, font):
    if not run:
        return 0.0
    return sum(draw.textlength("".join(ch for ch in cluster
                                       if not _is_mark(ch))
                                or cluster, font=font)
               for cluster in _split_clusters(run))


def _draw_hebrew_run(draw, x_left, y, run, font, fill):
    """Dessine un run hébreu : clusters de droite à gauche.

    ``x_left`` est le bord GAUCHE du run ; le premier cluster logique
    se pose au bord droit. Retourne rien — largeur via _run_width.
    """
    x = x_left + _run_width(draw, run, font)
    for cluster in _split_clusters(run):
        base = "".join(ch for ch in cluster if not _is_mark(ch))
        marks = "".join(ch for ch in cluster if _is_mark(ch))
        if base:
            x -= draw.textlength(base, font=font)
            draw.text((x, y), base, font=font, fill=fill)
            for ch, dx, dy in _mark_offsets(base, marks, font):
                draw.text((x + dx, y + dy), ch, font=font, fill=fill)
        elif marks:
            draw.text((x, y), marks, font=font, fill=fill)


def _draw_text(draw, xy, text, font, fill):
    """Dessine un texte hébreu/mixte avec ancrage correct du nikkud.

    Sans raqm, Pillow dessine chaque caractère à la position du curseur
    et l'avance : le nikkud, à largeur nulle en théorie, se retrouve
    décalé après sa consonne. On dessine donc cluster par cluster :
    consonne à la position du curseur, puis ses marques À LA MÊME
    ORIGINE (elles se superposent à la consonne).

    La chaîne est découpée en runs hébreu/autre (ordre logique) :
    chaque run occupe sa place, les runs hébreux sont dessinés en
    interne de droite à gauche, les autres de gauche à droite. Le
    premier caractère fort donne la direction de base (un libellé
    français contenant un mot hébreu reste globalement LTR).
    Avec raqm, le moteur gère bidi et ancrage : simple délégation.
    """
    if _RAQM:
        draw.text(xy, text, font=font, fill=fill)
        return
    runs = _hebrew_runs(text)
    if not any(heb for heb, _ in runs):
        draw.text(xy, text, font=font, fill=fill)
        return
    base_rtl = runs[0][0]
    x, y = xy
    if not base_rtl:
        # Base LTR : runs de gauche à droite, chaque run à sa place.
        for heb, run in runs:
            if heb:
                _draw_hebrew_run(draw, x, y, run, font, fill)
            else:
                draw.text((x, y), run, font=font, fill=fill)
            x += _run_width(draw, run, font)
    else:
        # Base RTL : le premier run logique se pose au bord droit, les
        # suivants vers la gauche ; un run latin s'écrit en interne LTR.
        total = _text_width(draw, text, font)
        x += total
        for heb, run in runs:
            w = _run_width(draw, run, font)
            if heb:
                _draw_hebrew_run(draw, x - w, y, run, font, fill)
            else:
                draw.text((x - w, y), run, font=font, fill=fill)
            x -= w


def _text_width(draw, text, font):
    """Largeur d'un texte tel que dessiné par _draw_text."""
    if _RAQM:
        return draw.textlength(text, font=font)
    return sum(_run_width(draw, run, font)
               for _, run in _hebrew_runs(text))

_NON_FINITE_TITLE = "Formes non finies"


def _visual(text):
    """Texte prêt au dessin Pillow, sans marques de directionnalité.

    Le dessin est fait par _draw_text (ancrage du nikkud) ; ici on ne
    fait que nettoyer les marques de direction (LRM/RLM), jamais
    inverser : l'ordre des clusters est géré au dessin.
    """
    if not text:
        return ""
    return _BIDI_MARKS_RE.sub("", str(text))


def _binyan_entry(parsed, binyan_code):
    for b in parsed.get("binyanim", []):
        if b.get("code") == binyan_code:
            return b
    return None


def build_binyan_document(parsed, binyan_code):
    """Document imprimable d'un binyan à partir du texte parsé du CLI.

    ``parsed`` est la structure renvoyée par parse_binyanim_text ;
    ``binyan_code`` le code du binyan à imprimer (qal, nif, piel...).
    Renvoie :
        {"title", "subtitle", "meta": [...], "notes": [...],
         "sections": [{"title", "rows": [(libellé, forme), ...]}]}
    Lève ValueError si le binyan n'est pas dans le résultat.
    """
    entry = _binyan_entry(parsed, binyan_code)
    if entry is None:
        raise ValueError(f"Binyan inconnu dans le résultat : {binyan_code!r}")

    verb = parsed.get("verb", {})
    weak = parsed.get("weak", {})
    doc = {
        "title": f"Paradigme — {entry['name_fr']} ({entry['name_he']})",
        "subtitle": "",
        "meta": [],
        "notes": [],
        "sections": [],
    }

    # Sous-titre : racine, lemme BHSA, traduction française du verbe.
    parts = []
    if verb.get("root"):
        parts.append(f"Racine {verb['root']}")
    if verb.get("lex"):
        parts.append(f"lemme BHSA : {verb['lex']}")
    doc["subtitle"] = "  ·  ".join(parts)
    if verb.get("gloss_fr"):
        doc["subtitle"] += f"  « {verb['gloss_fr']} »"

    # Catégorie du verbe (fort ou faible).
    code = weak.get("code")
    if code in (None, "strong"):
        doc["meta"].append("Verbe fort (shalem) : conjugaison régulière.")
    elif weak.get("label"):
        doc["meta"].append(f"Verbe faible : {weak['label']}")

    # Attestation du binyan pour cette racine.
    if entry.get("exists") is False:
        if entry.get("mishnah_forms"):
            doc["meta"].append(
                "Binyan non attesté dans la Bible hébraïque pour cette "
                "racine, mais attesté dans la Mishna (paradigme "
                "théorique, construit par analogie).")
        elif entry.get("modern_forms"):
            doc["meta"].append(
                "Binyan non attesté dans la Bible hébraïque pour cette "
                "racine, mais attesté en hébreu moderne (paradigme "
                "théorique, construit par analogie).")
        else:
            doc["meta"].append(
                "Binyan non attesté dans la Bible hébraïque pour cette "
                "racine (paradigme théorique, construit par analogie).")
    elif entry.get("attested"):
        doc["meta"].append("Binyan attesté dans la BHSA pour cette forme.")

    # Traductions du verbe dans ce binyan.
    trads = []
    if entry.get("translation_fr"):
        trads.append(f"fr : {entry['translation_fr']}")
    if entry.get("translation_en"):
        trads.append(f"en : {entry['translation_en']}")
    if trads:
        doc["notes"].append("Traduction : " + "  |  ".join(trads))
    if entry.get("mishnah_forms"):
        doc["notes"].append(
            "Formes attestées dans la Mishna : "
            + ", ".join(entry["mishnah_forms"]))
    modern = entry.get("modern_forms") or {}
    if modern:
        modern_txt = ("Attesté en hébreu moderne : "
                      + (modern.get("lemma") or ""))
        if modern.get("gloss"):
            modern_txt += f" ({modern['gloss']})"
        if modern.get("url"):
            modern_txt += f"\n{modern['url']}"
        doc["notes"].append(modern_txt)

    # Sections de paradigme : parsées depuis le texte du binyan. Les
    # en-têtes de temps («  Parfait (qatal) : ») ouvrent une section,
    # les lignes indentées «    libellé  forme » deviennent des rangées.
    current = None
    for line in entry.get("text", "").split("\n"):
        if not line.strip():
            continue
        if (line.startswith("--") or line.startswith("Traduction")
                or line.startswith("⚠") or line.startswith("✸")
                or line.startswith("◈")):
            continue
        row = _ROW_RE.match(line)
        if row and current is not None:
            current["rows"].append((row.group(1), row.group(2)))
            continue
        head = re.match(r"^ {2}(\S.*?)\s*:\s*$", line)
        if head:
            title = head.group(1).strip()
            current = {"title": title, "rows": []}
            doc["sections"].append(current)
    return doc


# --- Polices ----------------------------------------------------------------

# Paires (régulière, grasse) par ordre de priorité, par plateforme.
# Priorité absolue : les polices DejaVu embarquées (data/fonts), dont
# les tables GPOS hébraïques positionnent correctement le nikkud même
# sans moteur de shaping (le Pillow Windows n'embarque pas libraqm).
# Repli : polices système couvrant l'hébreu avec nikkud.
def _bundled_fonts():
    """Polices DejaVu embarquées avec l'application (data/fonts).

    Sources : dossier data/fonts à côté du script (exécution depuis les
    sources) ; sous PyInstaller, sys._MEIPASS où le .spec recrée
    l'arborescence data/ (le dossier data est embarqué tel quel).
    """
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (os.path.join(here, "data", "fonts"),
                 os.path.join(os.path.dirname(here), "data", "fonts")):
        regular = os.path.join(base, "DejaVuSans.ttf")
        if os.path.isfile(regular):
            bold = os.path.join(base, "DejaVuSans-Bold.ttf")
            return [(regular, bold if os.path.isfile(bold) else regular)]
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        regular = os.path.join(sys._MEIPASS, "data", "fonts",
                              "DejaVuSans.ttf")
        if os.path.isfile(regular):
            bold = os.path.join(sys._MEIPASS, "data", "fonts",
                                "DejaVuSans-Bold.ttf")
            return [(regular, bold if os.path.isfile(bold) else regular)]
    return []


def _font_pairs():
    bundled = _bundled_fonts()
    if sys.platform == "win32":
        fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        return bundled + [
            (os.path.join(fonts, "dejavusans.ttf"),
             os.path.join(fonts, "dejavusans-bold.ttf")),
            (os.path.join(fonts, "arial.ttf"),
             os.path.join(fonts, "arialbd.ttf")),
            (os.path.join(fonts, "tahoma.ttf"),
             os.path.join(fonts, "tahomabd.ttf")),
            (os.path.join(fonts, "segoeui.ttf"),
             os.path.join(fonts, "segoeuib.ttf")),
        ]
    if sys.platform == "darwin":
        supp = "/System/Library/Fonts/Supplemental"
        return bundled + [
            (os.path.join(supp, "DejaVuSans.ttf"),
             os.path.join(supp, "DejaVuSans-Bold.ttf")),
            (os.path.join(supp, "Arial Unicode.ttf"),
             os.path.join(supp, "Arial Unicode.ttf")),
            (os.path.join(supp, "Arial.ttf"),
             os.path.join(supp, "Arial Bold.ttf")),
        ]
    return bundled + [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        (os.path.expanduser("~/.fonts/DejaVuSans.ttf"),
         os.path.expanduser("~/.fonts/DejaVuSans-Bold.ttf")),
        ("/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf",
         "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]


def _load_font(bold, pt, dpi):
    """Charge une police (grasse ou régulière) ; repli : police par défaut."""
    from PIL import ImageFont
    size = max(1, round(pt * dpi / 72))
    for regular, bold_path in _font_pairs():
        path = bold_path if bold else regular
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        if not bold and os.path.isfile(regular):
            try:
                return ImageFont.truetype(regular, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# --- Rendu ------------------------------------------------------------------

def render_binyan_pages(doc, dpi=150, font_scale=1.0):
    """Met le document en pages A4 ; renvoie une liste de PIL.Image.

    ``font_scale`` (0.6 à 2.0) agrandit/réduit toutes les polices du
    document — utile pour compenser la réduction du mode 2 pages/
    feuille ou pour un rendu plus aéré (les tailles de base sont en
    points : 17/11/9/12/9,5/12/8 pour titre/sous-titre/méta/section/
    libellé/forme/pied de page).
    """
    from PIL import Image, ImageDraw

    font_scale = min(2.0, max(0.6, float(font_scale)))
    scale = dpi / 72.0
    width = round(8.27 * dpi)   # 210 mm
    height = round(11.69 * dpi)  # 297 mm
    margin = round(0.85 * dpi)
    footer_zone = round(0.55 * dpi)

    f_title = _load_font(True, 17 * font_scale, dpi)
    f_subtitle = _load_font(False, 11 * font_scale, dpi)
    f_meta = _load_font(False, 9 * font_scale, dpi)
    f_section = _load_font(True, 12 * font_scale, dpi)
    f_label = _load_font(False, 9.5 * font_scale, dpi)
    f_form = _load_font(True, 12 * font_scale, dpi)
    f_footer = _load_font(False, 8, dpi)

    ink = "#1a1a1a"
    grey = "#555555"
    rule = "#999999"

    pages = []

    def new_page():
        img = Image.new("RGB", (width, height), "white")
        pages.append((img, ImageDraw.Draw(img)))
        return img, ImageDraw.Draw(img), margin

    img, draw, y = new_page()

    def text(x, yy, s, font, fill=ink):
        _draw_text(draw, (x, yy), _visual(s), font=font, fill=fill)

    def text_right(x_right, yy, s, font, fill=ink):
        s = _visual(s)
        w = _text_width(draw, s, font)
        _draw_text(draw, (x_right - w, yy), s, font=font, fill=fill)

    def ensure_room(needed):
        nonlocal img, draw, y
        if y + needed > height - margin - footer_zone:
            img, draw, y = new_page()

    # En-tête (première page uniquement).
    text(margin, y, doc["title"], f_title)
    y += round(f_title.size * 1.45)
    if doc.get("subtitle"):
        text(margin, y, doc["subtitle"], f_subtitle, grey)
        y += round(f_subtitle.size * 1.5)
    for line in doc.get("meta", []):
        text(margin, y, line, f_meta, grey)
        y += round(f_meta.size * 1.45)
    if doc.get("notes"):
        y += round(f_meta.size * 0.5)
        for line in doc["notes"]:
            text(margin, y, line, f_meta)
            y += round(f_meta.size * 1.45)
    y += round(f_meta.size * 0.6)
    draw.line([(margin, y), (width - margin, y)], fill=rule, width=2)
    y += round(f_meta.size * 1.2)

    # Sections : titre souligné + rangées « libellé (gauche) forme (droite) ».
    for section in doc.get("sections", []):
        if not section.get("rows"):
            continue
        ensure_room(round(f_section.size * 3))
        text(margin, y, section["title"], f_section)
        y += round(f_section.size * 1.35)
        for label, form in section["rows"]:
            row_h = max(f_label.size, f_form.size)
            ensure_room(round(row_h * 1.7))
            text(margin, y, label, f_label, grey)
            text_right(width - margin, y, form, f_form)
            y += round(row_h * 1.55)
        y += round(f_section.size * 0.8)

    # Pied de page : « analyse_hebreu — page i/n ».
    total = len(pages)
    for i, (pimg, pdraw) in enumerate(pages, start=1):
        footer = f"analyse_hebreu — page {i}/{total}"
        fw = pdraw.textlength(footer, font=f_footer)
        pdraw.text(((width - fw) / 2, height - margin + round(6 * scale)),
                   footer, font=f_footer, fill=grey)

    return [pimg for pimg, _ in pages]


def compose_sheets(pages, per_sheet=2, dpi=150):
    """Regroupe les pages en feuilles A4 paysage, 2 pages par feuille.

    Chaque page portrait est réduite pour tenir dans sa demi-colonne
    (marge + gouttière centraux) et centrée verticalement. Une feuille
    incomplète garde sa colonne droite vide.
    """
    if not pages:
        raise ValueError("Aucune page à composer.")
    if per_sheet != 2:
        raise ValueError(f"Disposition non supportée : {per_sheet} "
                         "pages par feuille.")
    from PIL import Image

    sheet_w = round(11.69 * dpi)   # 297 mm (paysage)
    sheet_h = round(8.27 * dpi)    # 210 mm
    margin = round(0.4 * dpi)
    gutter = round(0.5 * dpi)
    cell_w = (sheet_w - 2 * margin - gutter) // 2

    sheets = []
    for i in range(0, len(pages), per_sheet):
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
        for col, page in enumerate(pages[i:i + per_sheet]):
            scale = min(cell_w / page.width,
                        (sheet_h - 2 * margin) / page.height, 1.0)
            size = (max(1, round(page.width * scale)),
                    max(1, round(page.height * scale)))
            reduced = page if size == page.size else page.resize(size)
            x = margin + col * (cell_w + gutter) + (cell_w - size[0]) // 2
            y = (sheet_h - size[1]) // 2
            sheet.paste(reduced, (x, y))
        sheets.append(sheet)
    return sheets


def save_pdf(pages, path, dpi=150):
    """Écrit les pages dans un PDF (une page A4 par image)."""
    if not pages:
        raise ValueError("Aucune page à exporter.")
    pages[0].save(path, format="PDF", save_all=True,
                  append_images=pages[1:], resolution=dpi)


# --- Impression -------------------------------------------------------------

def list_printers():
    """Imprimantes installées, par ordre de préférence système.

    La première est l'imprimante par défaut quand elle est identifiable.
    Renvoie une liste (éventuellement vide) de noms.
    """
    try:
        if sys.platform == "win32":
            import win32print
            flags = (win32print.PRINTER_ENUM_LOCAL
                     | win32print.PRINTER_ENUM_CONNECTIONS)
            names = []
            # EnumPrinters(flags, name, level) — level 1 renvoie des
            # PRINTER_INFO_1 (flags, description, name, comment) ; le
            # nom de l'imprimante est à l'index 2.
            for info in win32print.EnumPrinters(flags, None, 1):
                try:
                    names.append(info[2])
                except (IndexError, TypeError):
                    continue
            default = None
            try:
                default = win32print.GetDefaultPrinter()
            except Exception:
                pass
            if default in names:
                names.remove(default)
                names.insert(0, default)
            return names
        # Linux et macOS : lpstat (CUPS)
        for cmd in ("lpstat -e", "lpstat -a"):
            try:
                out = subprocess.run(cmd.split(), check=True, capture_output=True,
                                     timeout=15)
                names = [l.strip() for l in
                        out.stdout.decode(errors="replace").splitlines()
                        if l.strip()]
                if names:
                    return names
            except (OSError, subprocess.SubprocessError):
                continue
        return []
    except Exception:
        return []


def print_pdf_file(path, printer=None):
    """Imprime un PDF sur l'imprimante donnée (défaut si None).

    Sous Windows : verbe shell « printto » qui accepte une imprimante
    cible (l'association PDF du système gère l'impression).
    Sous Linux/macOS : lp -d / lpr -P (CUPS).

    Renvoie True si une commande a été lancée, False si le fichier
    doit être ouvert manuellement pour impression.
    """
    try:
        if sys.platform == "win32":
            if printer:
                import win32api
                win32api.ShellExecute(0, "printto", path,
                                      f'"{printer}"', ".", 0)
            else:
                os.startfile(path, "print")  # noqa: S606 (association PDF)
            return True
        if sys.platform == "darwin":
            cmd = ["lpr", path] if not printer else ["lpr", "-P", printer, path]
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            return True
        for cmd in ((["lp", "-d", printer, path] if printer else ["lp", path]),
                    (["lpr", "-P", printer, path] if printer else ["lpr", path])):
            try:
                subprocess.run(cmd, check=True, capture_output=True,
                               timeout=30)
                return True
            except (OSError, subprocess.SubprocessError):
                continue
        return False
    except (OSError, subprocess.SubprocessError):
        return False


def open_pdf_file(path):
    """Ouvre le PDF avec l'application par défaut (repli d'impression)."""
    try:
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", path])  # noqa: S603,S607
        return True
    except OSError:
        return False


def choose_printer_dialog(parent, printers, default=None):
    """Dialogue Tk de sélection d'imprimante ; renvoie le nom ou None.

    Liste des imprimantes (la première/défaut présélectionnée), boutons
    Imprimer et Annuler. Renvoie None si la liste est vide (l'appelant
    imprime sur la défaut) ou si l'utilisateur annule.
    """
    if not printers:
        return None
    import tkinter as tk
    from tkinter import ttk

    choice = {"printer": None}
    dlg = tk.Toplevel(parent)
    dlg.title("Imprimer")
    dlg.transient(parent)
    dlg.resizable(False, False)
    dlg.grab_set()

    frm = ttk.Frame(dlg, padding=12)
    frm.pack(fill="both", expand=True)
    ttk.Label(frm, text="Imprimante :").grid(row=0, column=0,
                                             sticky="w", pady=(0, 6))
    var = tk.StringVar(value=default if default in printers else printers[0])
    lst = ttk.Combobox(frm, textvariable=var, values=printers,
                       state="readonly", width=44)
    lst.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    frm.columnconfigure(0, weight=1)

    def ok():
        choice["printer"] = var.get()
        dlg.destroy()

    def cancel():
        choice["printer"] = None
        dlg.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=2, column=0, sticky="e")
    ttk.Button(btns, text="Annuler", command=cancel).pack(side="left",
                                                          padx=(0, 6))
    ttk.Button(btns, text="Imprimer", command=ok).pack(side="left")

    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - dlg.winfo_reqwidth()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - dlg.winfo_reqheight()) // 2
    dlg.geometry(f"+{max(0, x)}+{max(0, y)}")
    dlg.bind("<Return>", lambda e: ok())
    dlg.bind("<Escape>", lambda e: cancel())
    dlg.protocol("WM_DELETE_WINDOW", cancel)
    dlg.wait_window()
    return choice["printer"]


# --- Aperçu (Tkinter) -------------------------------------------------------

class BinyanPrintPreview:
    """Fenêtre d'aperçu avant impression (composition, pas d'héritage Tk).

    Importée paresseusement : le module reste utilisable (rendu, PDF,
    tests) sans tkinter ni affichage.
    """

    _MIN_ZOOM = 0.25
    _MAX_ZOOM = 3.0

    def __init__(self, parent, pages, title="Binyan", doc=None, dpi=150,
                 two_up=False, font_scale=100, on_close=None):
        import tkinter as tk
        from tkinter import ttk, messagebox
        from PIL import ImageTk

        self._tk = tk
        self._messagebox = messagebox
        self._ImageTk = ImageTk
        self.doc = doc
        self._dpi = dpi
        self._on_close = on_close
        self.pages = pages
        self._two_up = tk.BooleanVar(value=bool(two_up))
        self._sheets_cache = None
        self._page = 0
        self._zoom = 1.0
        self._photo = None
        self._fit_job = None
        self._font_job = None

        self.win = tk.Toplevel(parent)
        self.win.title(f"Aperçu avant impression — {title}")
        self.win.geometry("980x960")
        self.win.transient(parent)

        bar = ttk.Frame(self.win)
        bar.pack(fill="x", padx=6, pady=6)
        self.btn_prev = ttk.Button(bar, text="◀", width=3,
                                   command=self._prev_page)
        self.btn_prev.pack(side="left")
        self.label_page = ttk.Label(bar, text="", width=10, anchor="center")
        self.label_page.pack(side="left", padx=4)
        self.btn_next = ttk.Button(bar, text="▶", width=3,
                                   command=self._next_page)
        self.btn_next.pack(side="left")
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y",
                                                    padx=8)
        ttk.Button(bar, text="−", width=3,
                   command=lambda: self._zoom_by(1 / 1.25)).pack(side="left")
        self.label_zoom = ttk.Label(bar, text="", width=8, anchor="center")
        self.label_zoom.pack(side="left", padx=4)
        ttk.Button(bar, text="+", width=3,
                   command=lambda: self._zoom_by(1.25)).pack(side="left")
        ttk.Button(bar, text="Ajuster", command=self._fit_width).pack(
            side="left", padx=4)
        # Impression économe : deux pages du paradigme côte à côte sur
        # une même feuille A4 paysage (colonnes réduites).
        ttk.Checkbutton(bar, text="2 pages/feuille",
                        variable=self._two_up,
                        command=self._on_two_up).pack(side="left", padx=8)
        self._two_up.trace_add("write", self._invalidate_sheets)

        # Taille de police du document (pourcentage des tailles de base).
        # Re-rendu différé : chaque frappe dans le champ re-programme le
        # rendu 400 ms plus tard (le rendu complet d'un paradigme prend
        # quelques centaines de ms).
        ttk.Label(bar, text="Police :").pack(side="left", padx=(8, 2))
        self.font_scale_var = tk.StringVar(value=str(int(font_scale)))
        self._font_spin = ttk.Spinbox(bar, from_=60, to=200, increment=10,
                                      width=5, textvariable=self.font_scale_var,
                                      command=self._rerender)
        self._font_spin.pack(side="left")
        ttk.Label(bar, text="%").pack(side="left")
        # Flèches de la spinbox : rendu immédiat (command ci-dessus) ;
        # frappe clavier : rendu différé, le temps de taper la valeur.
        self._font_spin.bind("<KeyRelease>", lambda e: self._on_font_scale())
        self._font_spin.bind("<Return>", lambda e: self._rerender())
        self._font_spin.bind("<FocusOut>", lambda e: self._rerender())

        ttk.Button(bar, text="Enregistrer en PDF…",
                   command=self._save_pdf).pack(side="right", padx=4)
        self.btn_print = ttk.Button(bar, text="Imprimer…", command=self._print)
        self.btn_print.pack(side="right", padx=4)
        ttk.Button(bar, text="Fermer",
                   command=self._close).pack(side="right", padx=4)

        wrap = ttk.Frame(self.win)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, background="#404040",
                                highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        yscroll = ttk.Scrollbar(wrap, orient="vertical",
                                command=self.canvas.yview)
        yscroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=yscroll.set)
        self.canvas.bind("<Configure>",
                         lambda e: self.win.after_idle(self._fit_if_needed))
        self.win.bind("<Escape>", lambda e: self._close())
        self.win.bind("<Prior>", lambda e: self._prev_page())
        self.win.bind("<Next>", lambda e: self._next_page())
        # Fermeture (Échap, croix, bouton) : propager les réglages à
        # l'appelant (persistance gui.properties) avant de détruire.
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        self._fit_width(first=True)

    # --- disposition 2 pages/feuille ----------------------------------------

    def _close(self):
        """Ferme l'aperçu en propageant les réglages courants."""
        if self._on_close is not None:
            try:
                self._on_close(self._two_up.get(),
                               int(self.font_scale_var.get()))
            except (ValueError, TypeError):
                pass
        self.win.destroy()

    def _invalidate_sheets(self, *_args):
        """La case « 2 pages/feuille » a changé : composition à refaire."""
        self._sheets_cache = None

    def _on_font_scale(self):
        """Nouvelle taille de police : re-rend le document.

        Rendu immédiat sur les flèches de la spinbox (retour tactile) ;
        différé de 400 ms sur la frappe clavier (le temps de finir de
        taper la valeur). Sans document source (aperçu ouvert sur des
        pages déjà rendues), le contrôle est sans effet.
        """
        if self.doc is None:
            return
        if self._font_job is not None:
            try:
                self.win.after_cancel(self._font_job)
            except self._tk.TclError:
                pass
            self._font_job = None
        self._font_job = self.win.after(400, self._rerender)

    def _rerender(self):
        self._font_job = None
        raw = self.font_scale_var.get().strip()
        if not raw:
            return
        try:
            scale = float(raw) / 100.0
        except ValueError:
            return
        if not (0.6 <= scale <= 2.0):
            return
        # Le rendu d'un paradigme multi-pages peut prendre plusieurs
        # secondes : montrer l'activité (curseur, libellé) et forcer le
        # rafraîchissement avant de bloquer la boucle d'événements.
        self.win.configure(cursor="watch")
        self.label_page.configure(text="re-rendu…")
        self.win.update_idletasks()
        try:
            self.pages = render_binyan_pages(self.doc, dpi=self._dpi,
                                             font_scale=scale)
        except Exception as exc:
            self.win.configure(cursor="")
            self._messagebox.showerror(
                "Impression", f"Échec du re-rendu : {exc}")
            return
        self.win.configure(cursor="")
        self._sheets_cache = None
        self._page = 0
        self._fit_width(first=True)

    def _on_two_up(self):
        """Bascule 1/2 pages par feuille : recompose et rafraîchit l'aperçu."""
        self._page = 0
        self._fit_width(first=True)

    def _current_pages(self):
        """Pages affichées/imprimées selon la case « 2 pages/feuille ».

        La composition est mise en cache : recomposer à chaque affichage
        serait coûteux (redimensionnement des deux pages complètes)."""
        if not self._two_up.get() or len(self.pages) <= 1:
            return self.pages
        if self._sheets_cache is None:
            self._sheets_cache = compose_sheets(self.pages, per_sheet=2)
        return self._sheets_cache

    # --- pages et zoom ------------------------------------------------------

    def _show_page(self):
        shown_pages = self._current_pages()
        img = shown_pages[self._page]
        size = (max(1, round(img.width * self._zoom)),
                max(1, round(img.height * self._zoom)))
        shown = img if size == img.size else img.resize(size)
        self._photo = self._ImageTk.PhotoImage(shown)
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, size[0], size[1]))
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        self.label_page.configure(
            text=f"page {self._page + 1}/{len(shown_pages)}")
        self.label_zoom.configure(text=f"{round(self._zoom * 100)} %")
        self.btn_prev.state(["!disabled"] if self._page > 0 else ["disabled"])
        self.btn_next.state(["!disabled"] if self._page < len(shown_pages) - 1
                            else ["disabled"])

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._show_page()

    def _next_page(self):
        if self._page < len(self._current_pages()) - 1:
            self._page += 1
            self._show_page()

    def _zoom_by(self, factor):
        self._zoom = min(self._MAX_ZOOM, max(self._MIN_ZOOM,
                                             self._zoom * factor))
        self._show_page()

    def _fit_width(self, first=False):
        canvas_w = max(1, self.canvas.winfo_width())
        if first and canvas_w <= 1:
            self._zoom = 0.65
        else:
            self._zoom = min(self._MAX_ZOOM, max(
                self._MIN_ZOOM,
                (canvas_w - 24) / self._current_pages()[0].width))
        self._show_page()

    def _fit_if_needed(self):
        if self._fit_job is not None:
            self.win.after_cancel(self._fit_job)
        self._fit_job = self.win.after(150, self._fit_width)

    # --- impression et export ----------------------------------------------

    def _save_pdf(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".pdf",
            filetypes=[("Fichier PDF", "*.pdf")])
        if not path:
            return
        try:
            save_pdf(self._current_pages(), path)
        except (OSError, ValueError) as exc:
            self._messagebox.showerror(
                "Enregistrement", f"Échec de l'enregistrement : {exc}")
            return
        self._messagebox.showinfo(
            "Enregistrement", f"PDF enregistré :\n{path}")

    def _print(self):
        # Sélection de l'imprimante : liste système, défaut présélectionnée.
        # Pas d'imprimante détectée : repli sur l'imprimante par défaut.
        printers = list_printers()
        printer = None
        if printers:
            printer = choose_printer_dialog(self.win, printers)
            if printer is None:
                return  # annulé
        pdf = os.path.join(tempfile.gettempdir(), "analyse_hebreu_binyan.pdf")
        try:
            save_pdf(self._current_pages(), pdf)
        except (OSError, ValueError) as exc:
            self._messagebox.showerror(
                "Impression", f"Échec de la génération du PDF : {exc}")
            return
        if print_pdf_file(pdf, printer=printer):
            self._messagebox.showinfo(
                "Impression",
                (f"Document envoyé à « {printer} »." if printer
                 else "Document envoyé à l'imprimante par défaut."))
        elif open_pdf_file(pdf):
            self._messagebox.showinfo(
                "Impression",
                "Aucune imprimante n'est accessible en ligne de commande.\n"
                "Le PDF a été ouvert : imprimez-le depuis sa visionneuse.")
        else:
            self._messagebox.showwarning(
                "Impression",
                f"Impossible de lancer l'impression.\nPDF : {pdf}")


def open_binyan_preview(parent, parsed, binyan_code,
                        two_up=False, font_scale=100, on_close=None):
    """Construit le document du binyan, le met en pages et ouvre l'aperçu.

    ``two_up`` et ``font_scale`` (pourcentage) sont les réglages
    initiaux de disposition ; ``on_close(two_up, font_scale)`` est
    appelé à la fermeture pour persister les réglages.

    Renvoie la fenêtre d'aperçu, ou None si le binyan est introuvable
    (l'erreur est signalée par l'appelant).
    """
    doc = build_binyan_document(parsed, binyan_code)
    pages = render_binyan_pages(doc, font_scale=font_scale / 100.0)
    return BinyanPrintPreview(parent, pages, title=doc["title"], doc=doc,
                              two_up=two_up, font_scale=font_scale,
                              on_close=on_close)
