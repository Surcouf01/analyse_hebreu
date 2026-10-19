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


def test_render_and_pdf(tmpdir="/tmp"):
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
    print("test_render_and_pdf : ok")


if __name__ == "__main__":
    test_document()
    test_render_and_pdf()
    print("tests/test_binyan_print.py : tous les tests sont passés.")
