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
    consonant_skeleton,
    find_line_matches,
    fold_sofit,
    normalize_query,
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

    def test_ltr_prefix_line_keeps_prefix_first(self):
        """Une ligne dont la première lettre forte est latine (base LTR),
        ex. « === Phrase analysée : … === », garde son préfixe en tête de
        la chaîne stockée : il s'affiche en début de ligne, pas rejeté à
        droite de l'hébreu."""
        line = "=== Phrase analysée : מֵאֵימָתַי קוֹרִין ==="
        visual = to_visual(line)
        # marqueur de base LTR (double LRM, invisible) puis le préfixe
        stripped = visual.lstrip(bidi_display.LRM + bidi_display.RLM)
        self.assertTrue(stripped.startswith("=== Phrase analysée :"))
        self.assertEqual(to_logical(visual), line)

    def test_rtl_base_with_latin_marked_and_reversible(self):
        """Une ligne à base RTL contenant du latin fort reste réversible
        (marque RLM en tête de la ligne visuelle)."""
        line = "בְּרֵאשִׁית wayyiqtol בָּרָא"
        visual = to_visual(line)
        self.assertTrue(visual.startswith(bidi_display.RLM))
        self.assertEqual(to_logical(visual), line)

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
        # les fragments portent un marqueur de base (RLM) ; la copie
        # doit redonner le texte SANS les marqueurs, ligne par ligne.
        expected = "\n".join(
            l.lstrip(bidi_display.RLM + bidi_display.LRM)
            for l in wrapped.split("\n"))
        self.assertEqual(to_logical(to_visual(wrapped)), expected)

    def test_wrapped_ltr_line_keeps_suffix_at_end(self):
        """Fragment replié d'une ligne à base LTR : le suffixe neutre
        (« === ») reste en FIN de fragment, pas rejeté à gauche (la base
        de la ligne d'origine est préservée par le marqueur)."""
        line = ("=== Phrase analysée : מֵאֵימָתַי קוֹרִין "
                "אֶת שְׁמַע בְּעַרְבִית ===")
        wrapped = logical_wrap(line, len, 40)
        lines = wrapped.split("\n")
        self.assertGreater(len(lines), 1)
        self.assertTrue(lines[-1].endswith("==="))
        self.assertEqual(to_logical(to_visual(wrapped)),
                         "\n".join(
                             l.lstrip(bidi_display.RLM + bidi_display.LRM)
                             for l in lines))

    def test_hebrew_segment_in_ltr_line_reads_rtl(self):
        """Dans une ligne à base LTR, le segment hébreu multi-mots est
        inversé d'un bloc : le DERNIER mot logique est le plus à GAUCHE
        (premier dans la chaîne visuelle) — la phrase se lit de droite
        à gauche, pas mot à mot de gauche à droite."""
        line = "=== Phrase analysée : מֵאֵימָתַי קוֹרִין אֶת שְׁמַע ==="
        visual = to_visual(line).lstrip(LRM + bidi_display.RLM)
        seg = visual[visual.find("אֵים") if "אֵים" in visual else 0:]
        # le segment hébreu est inversé cluster par cluster : la 1re
        # lettre hébreu stockée est la DERNIÈRE lettre du DERNIER mot
        # logique (ע de שְׁמַע) — la phrase se lit de droite à gauche.
        first_heb = next(c for c in visual if "\u05D0" <= c <= "\u05EA")
        self.assertEqual(first_heb, "ע")  # ayin final de שְׁמַע
        self.assertEqual(to_logical(to_visual(line)), line)

    def test_sof_pasuq_attached_to_hebrew_end(self):
        """Le sof pasuq « : » collé au dernier mot hébreu (Sefaria l'écrit
        en deux-points ASCII, neutres) prend la direction du mot : il
        s'inverse avec le bloc et s'affiche à la FIN de lecture (bord
        gauche du bloc), pas détaché au bord droit."""
        line = "=== Phrase analysée : וּפְטוּרוֹת מִן הַמַּעַשְׂרוֹת: ==="
        visual = to_visual(line).lstrip(LRM + bidi_display.RLM)
        # le segment hébreu inversé commence par ':' (sof pasuq = fin de
        # lecture = bord gauche du bloc), PUIS la dernière lettre du
        # dernier mot (ת de רוֹת).
        # le sof pasuq du verset est le DERNIER ':' de la ligne ; il
        # précède immédiatement la dernière lettre du dernier mot (ת)
        # dans le stockage visuel du bloc hébreu inversé.
        seg_start = visual.rindex(":")
        self.assertLess(seg_start, visual.rindex("ת"))
        seg = visual[seg_start:seg_start + 8]
        self.assertTrue(seg.startswith(":" + LRM + "ת"))
        self.assertEqual(to_logical(to_visual(line)), line)

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


class TestMirrorParens(unittest.TestCase):
    """Règle UAX #9 L4 : en contexte RTL, une parenthèse est rendue avec
    son glyphe miroir — sinon les parenthèses autour d'une racine hébraïque
    s'affichent « inversées » (ouvertures vers l'extérieur du mot)."""

    def test_parens_around_hebrew_root(self):
        """(בלהה) dans une ligne à base RTL : à l'écran (ordre du stockage,
        gauche-à-droite), la racine inversée doit être PRÉCÉDÉE du glyphe
        miroir de « ( » et SUIVIE de celui de « ) » — les parenthèses
        encadrent le mot, elles ne s'ouvrent pas vers l'extérieur."""
        line = "‣ בַּלָּ֫הֹ֥ות  (בלהה)  « Bilha »"
        visual = to_visual(line)
        clean = visual.replace(LRM, "").replace(bidi_display.RLM, "")
        self.assertIn("(ההלב)", clean)
        self.assertNotIn(")ההלב(", clean)
        # La copie restitue la ligne logique d'origine (involutivité :
        # to_logical re-miroite dans l'autre sens).
        self.assertEqual(to_logical(visual), line)

    def test_parens_around_hebrew_in_ltr_line(self):
        """A (בלהה) B : les parenthèses encadrent le mot hébreu inversé."""
        visual = to_visual("A (בלהה) B")
        clean = visual.replace(LRM, "").replace(bidi_display.RLM, "")
        self.assertIn("(ההלב)", clean)
        self.assertEqual(to_logical(visual), "A (בלהה) B")

    def test_latin_parens_not_mirrored(self):
        """Une parenthèse en contexte LTR (latin) garde son glyphe."""
        line = "Bilha : « servante » (nom propre)"
        self.assertEqual(to_visual(line), line)
        self.assertEqual(to_logical(line), line)

    def test_brackets_and_braces_mirrored(self):
        """Crochets et accolades autour d'une racine : idem parenthèses."""
        line = "Racine [בלהה] et {בלהה}"
        clean = (to_visual(line)
                 .replace(LRM, "").replace(bidi_display.RLM, ""))
        self.assertIn("[ההלב]", clean)
        self.assertIn("{ההלב}", clean)
        self.assertEqual(to_logical(to_visual(line)), line)

    def test_guillemets_francais_not_mirrored(self):
        """« » ne sont pas Bidi_Mirrored : leur glyphe ne change jamais
        (seul l'ordre d'affichage suit le bidi, comme pour un navigateur)."""
        line = "בלהה « Bilha »"
        visual = to_visual(line)
        clean = visual.replace(LRM, "").replace(bidi_display.RLM, "")
        self.assertIn("«", clean)
        self.assertIn("»", clean)
        self.assertEqual(clean.count("«"), 1)
        self.assertEqual(clean.count("»"), 1)
        self.assertEqual(to_logical(visual), line)


class TestConsonantSearch(unittest.TestCase):
    """Recherche Ctrl-F : squelette consonantique (sans nikkud ni teamim)
    sur le texte stocké en ordre visuel."""

    def test_skeleton_strips_vowels_and_accents(self):
        self.assertEqual(consonant_skeleton(GEN11), "בראשיתבראאלהים")
        self.assertEqual(consonant_skeleton("Louis Segond 1910"), "")
        # shin/sin : le point (U+05C1/U+05C2) n'est pas une consonne.
        self.assertEqual(consonant_skeleton("שָׁלוֹם שָׂם"), "שלוםשם")

    def test_find_word_reading_order(self):
        """Genèse 1:1 : la requête ברא (sans nikkud) trouve le ברא
        intérieur à בראשית (premier en lecture) PUIS le mot ברא,
        et chaque correspondance reconvertie en logique donne bien le
        texte vocalisé d'origine."""
        visual = to_visual(GEN11)
        matches = find_line_matches(visual, "ברא")
        self.assertEqual(len(matches), 2)
        texts = [to_logical(visual[a:b]) for a, b in matches]
        self.assertEqual(texts, ["בְּרֵא", "בָּרָא"])

    def test_find_word_with_nikkud_in_query(self):
        """Une requête saisie AVEC nikkud (clavier virtuel) doit trouver
        les mêmes occurrences que la requête consonantique."""
        visual = to_visual(GEN11)
        q = normalize_query("בְּרֵאשִׁית")
        self.assertEqual(q, "בראשית")
        matches = find_line_matches(visual, q)
        self.assertEqual(len(matches), 1)
        a, b = matches[0]
        self.assertEqual(to_logical(visual[a:b]), "בְּרֵאשִׁית")

    def test_find_from_visual_selection(self):
        """Une sélection copiée depuis la zone de résultat (ordre visuel,
        marques comprises) est normalisable en requête."""
        visual = to_visual(GEN11)
        matches = find_line_matches(visual, "ברא")
        a, b = matches[1]
        selected = visual[a:b]
        self.assertEqual(normalize_query(selected, visual=True), "ברא")

    def test_find_multiline_each_line_searched(self):
        text = ("Phrase 1 : בְּרֵאשִׁית בָּרָא\n"
                "Phrase 2 : אֵת הַשָׁמַיִם")
        visual = to_visual(text)
        line1, line2 = visual.split("\n")
        self.assertEqual(len(find_line_matches(line1, "ברא")), 2)
        self.assertEqual(find_line_matches(line2, "ברא"), [])
        self.assertEqual(len(find_line_matches(line2, "שמים")), 1)

    def test_find_in_mixed_ltr_line(self):
        """Ligne à base LTR (préfixe latin + hébreu) : les bornes restent
        exactement sur le mot trouvé (le marqueur de base double-LRM
        ne décale pas les indices)."""
        line = "=== Phrase analysée : בְּרֵאשִׁית בָּרָא ==="
        visual = to_visual(line)
        matches = find_line_matches(visual, "ברא")
        self.assertEqual(len(matches), 2)
        texts = [to_logical(visual[a:b]) for a, b in matches]
        self.assertIn("בְּרֵא", texts)
        self.assertIn("בָּרָא", texts)

    def test_wrapped_line_fragments_searched(self):
        """Après découpe (logical_wrap), chaque fragment visuel est
        cherché indépendamment — un mot coupé n'est pas trouvé à cheval
        sur deux lignes (les fragments sont indépendants)."""
        wrapped = logical_wrap(GEN11, len, 12)
        fragments = to_visual(wrapped).split("\n")
        total = sum(len(find_line_matches(f, "אלהים")) for f in fragments)
        self.assertEqual(total, 1)

    def test_sofit_fold_pairs(self):
        """fold_sofit plie les cinq lettres finales vers leur forme
        médiale, sans toucher au reste."""
        self.assertEqual(fold_sofit("ךםןףץ"), "כמנפצ")
        self.assertEqual(fold_sofit("ךְ"), "כְ")
        self.assertEqual(fold_sofit("Bilha"), "Bilha")
        self.assertEqual(fold_sofit(""), "")

    def test_find_sofit_insensitive_default(self):
        """Par défaut, ך et כ sont équivalentes : la requête המלך (avec
        kaf sofit) ET המלכ (avec kaf normal) trouvent le mot הַמֶּלֶךְ."""
        line = "וַיֹּאמֶר הַמֶּלֶךְ אֶל־מַלְכֵי"
        visual = to_visual(line)
        for q in ("המלך", "המלכ"):
            matches = find_line_matches(visual, q)
            self.assertEqual(len(matches), 1, q)
            a, b = matches[0]
            self.assertEqual(to_logical(visual[a:b]), "הַמֶּלֶךְ")

    def test_find_sofit_sensitive_exact(self):
        """sofit_insensitive=False : seules les formes EXACTES
        correspondent — המלכ ne trouve plus הַמֶּלֶךְ (ך final)."""
        line = "וַיֹּאמֶר הַמֶּלֶךְ אֶל־מַלְכֵי"
        visual = to_visual(line)
        self.assertEqual(find_line_matches(visual, "המלך",
                                           sofit_insensitive=False),
                         find_line_matches(visual, "המלך"))
        self.assertEqual(
            find_line_matches(visual, "המלכ", sofit_insensitive=False),
            [])

    def test_find_sofit_query_side_folded_too(self):
        """Le pliage s'applique aussi à la requête — cas réel du GUI : les
        racines affichées entre parenthèses sont écrites SANS sofit
        (ex. « הַמֶּלֶךְ (מלכ) »). En mode insensible, la requête מלך (kaf
        sofit) trouve le mot ET la racine ; en mode exact, seulement le
        mot (la racine מלכ a un kaf normal)."""
        line = "הַמֶּלֶךְ (מלכ) « roi »"
        visual = to_visual(line)
        matches = find_line_matches(visual, "מלך")  # kaf sofit en requête
        self.assertEqual(len(matches), 2)
        found = [to_logical(visual[a:b]) for a, b in matches]
        # Le mot biblique contient מלך (kaf sofit) : trouvé au kaf près ;
        # la racine entre parenthèses est écrite מלכ (kaf normal) : trouvée
        # aussi en mode insensible.
        self.assertIn("מֶּלֶךְ", found)
        self.assertIn("מלכ", found)
        exact = find_line_matches(visual, "מלך",
                                  sofit_insensitive=False)
        self.assertEqual(len(exact), 1)
        a, b = exact[0]
        self.assertEqual(to_logical(visual[a:b]), "מֶּלֶךְ")

    def test_no_query_no_match(self):
        self.assertEqual(find_line_matches(to_visual(GEN11), ""), [])
        self.assertEqual(find_line_matches("Louis Segond 1910", "ברא"), [])


if __name__ == "__main__":
    unittest.main()
