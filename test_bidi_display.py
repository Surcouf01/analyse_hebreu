"""Tests du module bidi_display (affichage hébreu stable dans le GUI).

Exécution :  python -m unittest test_bidi_display -v
"""

import unittest

import bidi_display
from bidi_display import (
    to_visual,
    to_logical,
    has_hebrew,
    logical_wrap,
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


class TestLogicalWrap(unittest.TestCase):
    """logical_wrap : retour à la ligne en ordre logique avant conversion."""

    def test_short_line_untouched(self):
        self.assertEqual(logical_wrap(GEN11, len, 1000), GEN11)

    def test_latin_lines_untouched(self):
        text = "Analyse grammaticale de l'hébreu biblique — une phrase assez " \
               "longue qui dépasserait la largeur du widget."
        self.assertEqual(logical_wrap(text, len, 10), text)

    def test_hebrew_wraps_in_reading_order(self):
        """La première ligne découpée doit contenir le PREMIER mot logique
        (le début de la phrase), pas la fin : c'est ce qui garantit que
        l'ordre d'affichage haut en bas reste l'ordre de lecture."""
        words = ["בְּרֵאשִׁית", "בָּרָא", "אֱלֹהִים", "שָׁמַיִם", "וְאֵת"]
        line = " ".join(words)
        wrapped = logical_wrap(line, len, 12)
        out_lines = wrapped.split("\n")
        self.assertGreater(len(out_lines), 1)
        for l in out_lines:
            self.assertLessEqual(len(l), 12)
        # Le premier mot logique est sur la première ligne...
        self.assertIn(words[0], out_lines[0])
        # ... et le dernier mot logique sur la dernière ligne.
        self.assertIn(words[-1], out_lines[-1])

    def test_round_trip_preserved(self):
        """Le texte découpé puis visuel reste réversible en logique."""
        wrapped = logical_wrap(GEN11 + " אֱלֹהִים שָׁמַיִם", len, 8)
        self.assertEqual(to_logical(to_visual(wrapped)), wrapped)

    def test_wide_word_split_by_clusters(self):
        """Un mot plus large qu'une ligne est coupé entre clusters, jamais
        au milieu d'une lettre + nikkud."""
        word = "וּפְטוּרוֹת"
        parts = bidi_display._split_wide_word(word, len, 3)
        self.assertGreater(len(parts), 1)
        joined = "".join(parts)
        # chaque fragment reste un préfixe/suffixe du mot (clusters intacts)
        self.assertEqual(sorted(parts[0]), sorted(word[:len(parts[0])]))
        self.assertEqual(to_logical(to_visual(joined)), joined)

    def test_empty_and_zero_width(self):
        self.assertEqual(logical_wrap("", len, 80), "")
        self.assertEqual(logical_wrap(GEN11, len, 0), GEN11)


if __name__ == "__main__":
    unittest.main()
