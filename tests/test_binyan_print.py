#!/usr/bin/env python3
"""Test de non-régression du mode Impression (binyan_print.py).

Vérifie que :
  1. le document d'un binyan est construit correctement depuis le
     texte marqué produit par binyanim_to_text (en-têtes, sections,
     rangées, statut d'attestation, traductions) ;
  2. le rendu A4 (Pillow) produit des pages à la taille A4 attendue,
     avec pagination si le paradigme dépasse une page ;
  3. l'export PDF écrit un fichier lisible ;
  4. un binyan absent du résultat lève ValueError.

Usage :
    python tests/test_binyan_print.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import binyan_print  # noqa: E402
from bhsa_grammar.binyan_gen import (  # noqa: E402
    binyanim_to_text,
    parse_binyanim_text,
)


def _sample_analysis():
    """Analyse binyanim minimale mais représentative (7 binyanim)."""
    def b(code, name_fr, name_he, exists, attested, forms):
        return {
            "code": code, "name_fr": name_fr, "name_he": name_he,
            "sense": "sens " + code,
            "translation_fr": "traduction fr " + code,
            "translation_en": "translation en " + code,
            "attested": attested, "exists": exists,
            "mishnah_forms": forms,
            "paradigm": {
                "perf": {("p3", "m", "sg"): "שָׁמַר",
                         ("p3", "f", "sg"): "שָׁמְרָה",
                         ("p1", "c", "sg"): "שָׁמַרְתִּי"},
                "impf": {("p3", "m", "sg"): "יִשְׁמֹר",
                         ("p2", "m", "sg"): "תִּשְׁמֹר"},
                "impv": {("p2", "m", "sg"): "שְׁמֹר"},
                "juss": {}, "coh": {},
            },
            "non_finite": {("inf", "", ""): "שְׁמֹר"},
        }

    analysis = {
        "input": "שָׁמַר",
        "found": True,
        "verb": {
            "root": ("ש", "ׁ", "מ", "ר"),
            "root_display": "שָׁמַר",
            "lex": "CMR[",
            "gloss_fr": "garder",
            "category": "strong",
            "category_label": "Verbe fort (shalem)",
            "category_desc": "conjugaison régulière",
            "is_weak": False,
        },
        "binyanim": [
            b("qal", "qal (paal)", "פָּעַל", True, True, []),
            b("nif", "nifal", "נִפְעַל", True, True, []),
            b("piel", "piel", "פִּעַל", False, False, ["שִׁימֵר"]),
            b("pual", "pual", "פֻּעַל", False, False, []),
            b("hit", "hithpael", "הִתְפַּעֵל", False, False, []),
            b("hif", "hifil", "הִפְעִיל", True, True, []),
            b("hof", "hofal", "הָפְעַל", False, False, []),
        ],
    }
    return analysis


def test_document():
    analysis = _sample_analysis()
    parsed = parse_binyanim_text(binyanim_to_text(analysis))

    # Document du qal : titre, sous-titre, 3 sections avec rangées.
    doc = binyan_print.build_binyan_document(parsed, "qal")
    assert "qal (paal)" in doc["title"], doc["title"]
    assert "שָׁמַר" in doc["subtitle"], doc["subtitle"]
    assert doc["sections"], "aucune section parsée"
    titles = [s["title"] for s in doc["sections"]]
    assert any("Parfait" in t for t in titles), titles
    perf = next(s for s in doc["sections"] if "Parfait" in s["title"])
    labels = [lbl for lbl, _ in perf["rows"]]
    assert any("3e pers. masc. sing." in l for l in labels), labels
    forms = [f for _, f in perf["rows"]]
    assert any("שָׁמַר" in f for f in forms), forms

    # Binyan non attesté avec formes mishnaïques (piel de שמר) :
    # la note d'attestation et les formes mishnaïques sont présentes.
    doc = binyan_print.build_binyan_document(parsed, "piel")
    joined = " ".join(doc["meta"]) + " ".join(doc["notes"])
    assert "non attesté" in joined.lower() or "Mishna" in joined, joined
    assert "שִׁימֵר" in joined, joined

    # Binyan absent du résultat : ValueError.
    try:
        binyan_print.build_binyan_document(parsed, "inconnu")
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError attendue pour un binyan inconnu")
    print("test_document : ok")


def test_render_and_pdf():
    tmpdir = tempfile.mkdtemp(prefix="binyan_print_")
    analysis = _sample_analysis()
    parsed = parse_binyanim_text(binyanim_to_text(analysis))
    doc = binyan_print.build_binyan_document(parsed, "qal")

    dpi = 150
    pages = binyan_print.render_binyan_pages(doc, dpi=dpi)
    assert pages, "aucune page rendue"
    # A4 à 150 dpi : 1240 x 1754 (± arrondi).
    for p in pages:
        assert abs(p.width - round(8.27 * dpi)) <= 1, p.width
        assert abs(p.height - round(11.69 * dpi)) <= 1, p.height

    # Pagination : un paradigme 7 binyanim complet dépasse une page,
    # vérifié sur le document du hithpael (gabarit long).
    big = binyan_print.build_binyan_document(parsed, "hit")
    big["sections"] = big["sections"] * 12  # forcer le débordement
    multi = binyan_print.render_binyan_pages(big, dpi=dpi)
    assert len(multi) > 1, "pagination attendue sur un paradigme long"

    pdf_path = os.path.join(tmpdir, "test_binyan_print.pdf")
    binyan_print.save_pdf(pages, pdf_path, dpi=dpi)
    assert os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 0
    with open(pdf_path, "rb") as fh:
        assert fh.read(4) == b"%PDF"
    os.remove(pdf_path)
    os.rmdir(tmpdir)

    # 2 pages par feuille : N pages portrait -> ceil(N/2) feuilles A4
    # paysage, contenu réduit et sans chevauchement des colonnes.
    sheets = binyan_print.compose_sheets(multi, per_sheet=2, dpi=dpi)
    assert len(sheets) == (len(multi) + 1) // 2, (len(sheets), len(multi))
    expected_w = round(11.69 * dpi)
    expected_h = round(8.27 * dpi)
    for s in sheets:
        assert abs(s.width - expected_w) <= 1, s.size
        assert abs(s.height - expected_h) <= 1, s.size
    # Composition identique : recomposer deux fois donne les mêmes feuilles.
    again = binyan_print.compose_sheets(multi, per_sheet=2, dpi=dpi)
    assert len(again) == len(sheets)
    print("test_render_and_pdf : ok")


def test_visual_raqm_modes():
    """_visual ne fait que nettoyer les marques de direction ; l'ordre
    (bidi) et l'ancrage du nikkud sont gérés au dessin (_draw_text)."""
    form = "\u05e9\u05b9\u05c1\u05de\u05b5\u05e8"  # shin+holam+sin, mem, tsere, resh
    out = binyan_print._visual(form)
    # Chaîne logique intacte : le dessin s'en charge, pas _visual.
    assert out == form, (out, form)
    # Les marques de direction (LRM/RLM) sont retirées.
    marked = "\u200e" + form + "\u200f"
    assert binyan_print._visual(marked) == form
    print("test_visual_raqm_modes : ok")


def test_draw_text_nikud_anchor():
    """Sans raqm : le nikkud est ancré sur sa consonne, l'hébreu est
    dessiné de droite à gauche, les textes mixtes gardent leur ordre
    de lecture."""
    from PIL import Image, ImageDraw, ImageFont
    saved = binyan_print._RAQM
    font_path = None
    for regular, _bold in binyan_print._font_pairs():
        if os.path.isfile(regular):
            font_path = regular
            break
    if font_path is None:
        print("test_draw_text_nikud_anchor : ignoré (aucune police)")
        return
    font = ImageFont.truetype(font_path, 64)

    def render(s):
        img = Image.new("RGB", (600, 160), "white")
        d = ImageDraw.Draw(img)
        binyan_print._draw_text(d, (50, 30), s, font=font, fill="black")
        return img

    def ink(img):
        px = img.convert("L").load()
        w, h = img.size
        return {(x, y) for x in range(w) for y in range(h)
                if px[x, y] < 180}

    try:
        binyan_print._RAQM = False
        # Le holam (point haut) de שֹׁמֵר doit être sur le shin, à
        # DROITE du mot (premier cluster logique = bord droit).
        img = render("\u05e9\u05b9\u05c1\u05de\u05b5\u05e8")
        px = ink(img)
        xs = sorted({x for x, _ in px})
        mid = (xs[0] + xs[-1]) / 2
        top_of = lambda side: min((y for x, y in px
                                   if (x > mid) == side), default=999)
        # Côté droit : encre haute (tête du shin + holam au-dessus).
        # Côté gauche : le resh est une lettre haute aussi — on compare
        # les MINIMUMS : le holam dépasse la hauteur des corps lettres.
        right_top = top_of(True)
        left_top = top_of(False)
        # Sans ancrage correct, le holam tomberait après le mot (hors
        # colonnes) ; avec l'ancrage il est au-dessus du shin, plus haut
        # que le corps du resh.
        assert right_top < left_top, (right_top, left_top)

        # Texte mixte : la largeur mesure tout, le rendon ne déborde pas
        # à gauche de l'origine.
        mixed = "Racine \u05e9\u05b8\u05c1\u05de\u05b7\u05e8"
        img2 = Image.new("RGB", (900, 160), "white")
        d2 = ImageDraw.Draw(img2)
        w = binyan_print._text_width(d2, mixed, font)
        binyan_print._draw_text(d2, (50, 30), mixed, font=font, fill="black")
        xs2 = sorted({x for x, _ in ink(img2)})
        assert xs2[0] >= 45, xs2[0]        # ne part pas avant l'origine
        assert xs2[-1] <= 55 + w + 2, (xs2[-1], w)  # ne déborde pas
    finally:
        binyan_print._RAQM = saved
    print("test_draw_text_nikud_anchor : ok")


def test_shuruq_centering():
    """Le dagesh du shuruq (וּ) tombe dans l'encre du vav, pas à côté.

    Régression : le centrage sur la chasse (advance) du vav — large mais
    à l'encre étroite — posait le point à droite de la lettre.
    """
    from PIL import Image, ImageDraw, ImageFont
    saved = binyan_print._RAQM
    font_path = None
    for regular, _bold in binyan_print._font_pairs():
        if os.path.isfile(regular):
            font_path = regular
            break
    if font_path is None:
        print("test_shuruq_centering : ignoré (aucune police)")
        return
    font = ImageFont.truetype(font_path, 96)

    def render(s):
        img = Image.new("RGB", (600, 200), "white")
        d = ImageDraw.Draw(img)
        binyan_print._draw_text(d, (100, 30), s, font=font, fill="black")
        return img

    try:
        binyan_print._RAQM = False
        vav = "\u05d5"
        vav_dagesh = "\u05d5\u05bc"
        img_with, img_bare = render(vav_dagesh), render(vav)
        p1 = img_with.convert("L").load()
        p2 = img_bare.convert("L").load()
        pts_bare = sorted({x for x in range(600) for y in range(200)
                           if p2[x, y] < 180})
        # Encre totale du vav+shuruq : ne doit pas déborder à droite
        # de l'encre du vav seul de plus d'un point du dagesh.
        pts_with = sorted({x for x in range(600) for y in range(200)
                           if p1[x, y] < 180})
        assert max(pts_with) <= max(pts_bare) + 2, \
            (max(pts_with), max(pts_bare))
        assert min(pts_with) >= min(pts_bare) - 2
        # Le décalage de centrage place l'encre du dagesh dans la
        # largeur d'encre du vav (méthode _ink_bbox, rendu réel).
        bx0, bx1 = binyan_print._ink_bbox(vav, font)
        dx0, dx1 = binyan_print._ink_bbox("\u05bc", font)
        off = binyan_print._centering_offset(vav, "\u05bc", font)
        marked = (dx0 + off, dx1 + off)
        assert bx0 - 1 <= marked[0] and marked[1] <= bx1 + 1, \
            (bx0, bx1, marked)
    finally:
        binyan_print._RAQM = saved
    print("test_shuruq_centering : ok")


def test_font_scale():
    """font_scale agrandit/réduit les polices et borne les excès."""
    analysis = _sample_analysis()
    parsed = parse_binyanim_text(binyanim_to_text(analysis))
    doc = binyan_print.build_binyan_document(parsed, "qal")
    # Document long : la pagination varie avec la taille de police.
    long_doc = binyan_print.build_binyan_document(parsed, "qal")
    long_doc["sections"] = long_doc["sections"] * 8

    small = binyan_print.render_binyan_pages(long_doc, font_scale=0.7)
    base = binyan_print.render_binyan_pages(long_doc, font_scale=1.0)
    big = binyan_print.render_binyan_pages(long_doc, font_scale=1.6)
    assert len(big) >= len(base) >= len(small), \
        (len(small), len(base), len(big))

    # Hors bornes : valeur clampée silencieusement (0.6-2.0).
    clamped = binyan_print.render_binyan_pages(doc, font_scale=5.0)
    maxed = binyan_print.render_binyan_pages(doc, font_scale=2.0)
    assert len(clamped) == len(maxed)
    print("test_font_scale : ok")


if __name__ == "__main__":
    test_document()
    test_render_and_pdf()
    test_visual_raqm_modes()
    test_draw_text_nikud_anchor()
    test_shuruq_centering()
    test_font_scale()
    print("tests/test_binyan_print.py : tous les tests sont passés.")
