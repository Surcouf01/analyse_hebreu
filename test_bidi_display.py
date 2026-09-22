"""Tests du module bidi_display (affichage hébreu stable dans le GUI).

Exécution :  python -m unittest test_bidi_display -v
"""

import unittest

import bidi_display
from bidi_display import (
    to_visual,
    to_logical,
    has_hebrew,
    visual_cluster_bounds,
    visual_hebrew_word_range,
    LRM,
)

# Genèse 1:1 (sans niqqud partiel pour lisibilité des fixtures)
GEN11 = "בְּרֵאשִׁית בָּרָא אֱלֹהִים"


class TestHasHebrew(unittest.TestCase):
    def test_pure_hebrew(self):
        self.assertTrue(has_hebrew("שָׁלוֹם"))

    def test_mixed_line(self):
        self.assertTrue(has_hebrew("Louis Segond — בְּרֵאשִׁית"))

    def test_latin_only(self):
        self.assertFalse(has_hebrew("Louis Segond 1910"))
        self.assertFalse(has_hebrew(""))


class TestRoundTrip(unittest.TestCase):
    """to_logical(to_visual(x)) doit redonner x (sans marques)."""

    def test_round_trip_hebrew_line(self):
        self.assertEqual(to_logical(to_visual(GEN11)), GEN11)

    def test_round_trip_mixed_line(self):
        line = "  · Clause 1 : בְּרֵאשִׁית בָּרָא"
        self.assertEqual(to_logical(to_visual(line)), line)

    def test_round_trip_latin_untouched(self):
        line = "=== Genesis 1:1 ==="
        self.assertEqual(to_visual(line), line)
        self.assertEqual(to_logical(line), line)

    def test_round_trip_multiline(self):
        text = (
            "=== Genesis 1:1 ===\n"
            "בְּרֵאשִׁית בָּרָא אֱלֹהִים\n"
            "\n"
            "-- Phrase 1 --\n"
            "  · Clause 1 : בְּרֵאשִׁית\n"
            "          ↳ wayyiqtol : בְּרֵאשִׁית est un substantif\n"
            "Traduction (fr) : Au commencement, Dieu créa…\n"
        )
        self.assertEqual(to_logical(to_visual(text)), text)

    def test_maqaf_and_sof_pasuq_stay_in_word(self):
        line = "הַשָּׁמַיִם וְאֵת הָאָָרֶץ׃"
        visual = to_visual(line)
        # le mot avec sof pasuq reste groupé (marques LRM par cluster)
        self.assertIn(LRM, visual)
        self.assertEqual(to_logical(visual), line)

    def test_numbers_keep_ltr_order(self):
        line = "בְּרֵאשִׁית 123 בָּרָא"
        visual = to_visual(line)
        self.assertIn("123", visual)
        self.assertEqual(to_logical(visual), line)

    def test_involution(self):
        """Le couple to_logical ∘ to_visual restitue le texte d'origine."""
        once = to_visual(GEN11)
        self.assertEqual(to_logical(once), GEN11)
        # idempotence sur les lignes sans hébreu
        latin = "=== Genesis 1:1 ==="
        self.assertEqual(to_visual(to_visual(latin)), latin)

    def test_visual_marks_stripped_before_reorder(self):
        """Une entrée contenant déjà des marques bidi (ancien format RLE/RLM)\n        est normalisée sans doubler les marques."""
        legacy = "\u202B" + GEN11 + "\u202C"
        self.assertEqual(to_visual(legacy), to_visual(GEN11))


class TestClusterSnap(unittest.TestCase):
    """visual_hebrew_word_range : extension des mots hébreux en ordre visuel."""

    def test_word_range_found(self):
        line = to_visual(GEN11)
        # col 0 : LRM du premier cluster → dans le premier mot
        rng = visual_hebrew_word_range(line, 1)
        self.assertIsNotNone(rng)
        start, end = rng
        word = line[start:end]
        self.assertTrue(has_hebrew(word))
        # les trois mots hébreux donnent chacun une plage distincte
        ranges = []
        col = 0
        while col < len(line):
            rng = visual_hebrew_word_range(line, col)
            if rng is None:
                col += 1
                continue
            if not ranges or ranges[-1] != rng:
                ranges.append(rng)
            col = rng[1] + 1
        self.assertEqual(len(ranges), 3)

    def test_no_hebrew_returns_none(self):
        self.assertIsNone(
            visual_hebrew_word_range("Louis Segond 1910", 3))


class TestStability(unittest.TestCase):
    """Le stockage visuel doit rendre l'ordre logique == ordre affiché."""

    def test_visual_line_starts_with_last_word(self):
        visual = to_visual(GEN11)
        # en ordre visuel, le mot affiché le plus à droite est אֱלֹהִים
        # (dernier mot logique) ; son dernier caractère (le mem final ם)
        # est donc en tête de la chaîne stockée.
        self.assertTrue(visual.startswith(LRM))
        bounds = visual_cluster_bounds(visual)
        self.assertTrue(bounds)
        start, end = bounds[0]
        first_cluster = visual[start:end]
        self.assertEqual(first_cluster[0], LRM)
        # premier cluster stocké : LRM + mem final ם du dernier mot logique
        self.assertEqual(first_cluster[1], "ם")

    def test_no_bidi_embedding_marks(self):
        """Plus d'embeddings RLE/PDF : le stockage visuel ne repose que sur\n        des marques LRM locales, insensibles à la découpe en fragments."""
        visual = to_visual(GEN11)
        self.assertNotIn("\u202B", visual)
        self.assertNotIn("\u202C", visual)
        self.assertNotIn("\u200F", visual)


if __name__ == "__main__":
    unittest.main()
