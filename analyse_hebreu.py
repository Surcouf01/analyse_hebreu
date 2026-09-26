#!/usr/bin/env python3
"""Analyseur grammatical de l'hébreu biblique — interface en ligne de commande.

Exemples :

    python analyse_hebreu.py "Genèse 1:1"
    python analyse_hebreu.py "Gen 1:1" --format json
    python analyse_hebreu.py "Genesis 1:1" --summary
    python analyse_hebreu.py --list-books

Le programme localise automatiquement la base morphologique BHSA (ETCBC) :
  - variable d'environnement BHSA_DATA (chemin du dossier de features .tf) ;
  - dépôt cloné localement : bhsa_repo/tf/c (branche data2021 du dépôt
    ETCBC/bhsa), ex. obtenu via :
        git clone --branch data2021 https://github.com/ETCBC/bhsa.git bhsa_repo
  - chargement en ligne via tf.app.use('bhsa') si aucune source locale.
"""

import argparse
import sys

from bhsa_grammar import (
    load_corpus,
    analyze_verse_by_reference,
    analyze_word,
    analyze_phrase,
    analyze_binyanim,
    format_text,
    format_json,
    format_summary,
    format_word,
    format_word_json,
    format_phrase,
    format_phrase_json,
    format_binyanim,
    format_binyanim_json,
    book_list,
    book_list_fr,
    DataNotFoundError,
    load_translation,
    get_translation,
    TranslationNotFoundError,
)
from bhsa_grammar.mishnah_catalog import SEDARIM, SCHWAB_TRACTATES
from bhsa_grammar.mishnah_analyzer import (
    analyze_mishnah_text,
    mishnah_analysis_block,
)


def build_parser():
    p = argparse.ArgumentParser(
        prog="analyse_hebreu",
        description="Analyse grammaticale d'un texte d'hébreu biblique (BHSA/ETCBC) "
                    "— verset de la Bible ou mishna (via Sefaria).",
        epilog="Ex. : python analyse_hebreu.py 'Genèse 1:1' --format text ; "
                "python analyse_hebreu.py --mishna 'Bérakhot 1:1'",
    )
    p.add_argument(
        "reference",
        nargs="?",
        help='Référence du verset, ex. "Genèse 1:1", "Gen 1:1", "Genesis 1:1".\n'
             "Ou, avec --word/--binyanim, un mot hébreu (avec nikkud, sans teamim)\n"
             "ou une racine trilitaire ; avec --phrase, une phrase hébreu.",
    )
    p.add_argument(
        "--word",
        action="store_true",
        help="Analyse un mot hébreu isolé (argument = le mot, ou fichier via --file).",
    )
    p.add_argument(
        "--phrase",
        action="store_true",
        help="Analyse une phrase hébreu libre (argument = la phrase, ou fichier via --file).",
    )
    p.add_argument(
        "--binyanim",
        action="store_true",
        help="Conjugue un verbe hébreu dans les 7 binyanim, toutes personnes "
             "(argument = mot conjugué ou racine trilitaire, ou fichier via --file).",
    )
    p.add_argument(
        "--mishna-binyanim",
        action="store_true",
        help="En mode --binyanim, signale aussi les binyanim attestés dans la "
             "Mishna (Sefaria, fichier mishnah_binyanim.json) mais absents "
             "de la Bible hébraïque, avec des formes d'attestation.",
    )
    p.add_argument(
        "--file",
        help="Fichier contenant un mot/ligne (--word/--binyanim) ou une phrase/ligne (--phrase).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "summary"],
        default="text",
        help="Format de sortie (défaut : text).",
    )
    p.add_argument(
        "--no-words",
        action="store_true",
        help="En format text, masque le détail mot à mot.",
    )
    p.add_argument(
        "--translation",
        action="store_true",
        help="Affiche la traduction française (Louis Segond 1910, domaine public) "
             "du verset analysé, avant l'analyse grammaticale.",
    )
    p.add_argument(
        "--translation-en",
        action="store_true",
        help="Affiche aussi la traduction anglaise (King James Version 1611, "
             "domaine public) du verset analysé.",
    )
    p.add_argument(
        "--translation-es",
        action="store_true",
        help="Affiche aussi la traduction espagnole (Reina-Valera 1909, "
             "dominio público) du verset analysé.",
    )
    p.add_argument(
        "--mishna",
        action="store_true",
        help="Affiche une mishna (argument = référence, ex. 'Bérakhot 1:1', "
             "'Mishnah Berakhot 2:5', 'Avot 1:3'). Le texte hébreu (Torat "
             "Emet, domaine public) vient de l'API Sefaria, ainsi que la "
             "traduction française (Moïse Schwab, domaine public) lorsque "
             "le traité est couvert (38 sur 63).",
    )
    p.add_argument(
        "--mishna-analyze",
        action="store_true",
        help="Avec --mishna : ajoute l'analyse grammaticale de la mishna "
             "(mot à mot via la base BHSA, comme pour une phrase libre ; "
             "requiert la base BHSA).",
    )
    p.add_argument(
        "--list-books",
        action="store_true",
        help="Liste les livres disponibles et quitte (Bible seule ; avec "
             "--mishna, les traités de la Mishna).",
    )
    return p


def _run_mishna_cli(args):
    """Mode livre : affiche une mishna via l'API Sefaria (sans la base BHSA)."""
    if not args.reference:
        print("Erreur : en mode --mishna, fournissez une référence "
              "(ex. 'Bérakhot 1:1').", file=sys.stderr)
        return 1
    from bhsa_grammar.sefaria_client import fetch_mishnah_mishnayot
    book, rest = (args.reference.split(" ", 1)
                  if " " in args.reference else (args.reference, "1:1"))
    book = book.strip()
    try:
        if ":" in rest:
            chap_s, mish_s = rest.split(":")
        else:
            chap_s, mish_s = rest, "1"
        chapter, mishnah = int(chap_s), int(mish_s)
    except ValueError:
        print(f"Erreur : référence de mishna invalide ({args.reference}).",
              file=sys.stderr)
        return 1
    # Résolution du traité : nom Sefaria, nom français ou mot-clé
    # (n'importe quel mot du nom, ex. « Avot » pour « Pirké Avot »).
    names = {}
    for _seder, tracts in SEDARIM:
        for t, fr in tracts:
            for w in (t.lower().split() + fr.lower().split()):
                names.setdefault(w, t)
            names.setdefault(t.lower(), t)
            names.setdefault(fr.lower(), t)
    tractate = names.get(book.lower()) or names.get(book.lower().rstrip("s"))
    if tractate is None:
        print(f"Erreur : traité inconnu « {book} ». Utilisez --list-books --mishna "
              "pour la liste (noms Sefaria ou français).", file=sys.stderr)
        return 1
    fr_name = next(fr for t, fr in [x for _, tracts in SEDARIM for x in tracts]
                   if t == tractate)
    # Bornes connues du catalogue : erreur claire si la référence dépasse.
    from bhsa_grammar.mishnah_catalog import STRUCTURE
    shape = STRUCTURE.get(tractate) or []
    if shape and (not 1 <= chapter <= len(shape)
                  or not 1 <= mishnah <= shape[chapter - 1]):
        print(f"Erreur : {fr_name} compte {len(shape)} chapitre(s) ; la "
              f"référence {chapter}:{mishnah} n'existe pas.", file=sys.stderr)
        return 1
    he = fetch_mishnah_mishnayot(tractate, chapter, "hebrew")
    if he and 1 <= mishnah <= len(he):
        print(f"=== {fr_name} {chapter}:{mishnah} ===")
        print(he[mishnah - 1])
    else:
        print(f"Erreur : mishna {fr_name} {chapter}:{mishnah} indisponible "
              "(API Sefaria injoignable ou référence inexistante).",
              file=sys.stderr)
        return 1
    if tractate in SCHWAB_TRACTATES:
        fr_texts = fetch_mishnah_mishnayot(tractate, chapter, "french")
        if fr_texts and 1 <= mishnah <= len(fr_texts):
            print()
            print("Traduction (Moïse Schwab, Talmud de Jérusalem) — "
                  f"{fr_name} {chapter}:{mishnah}")
            print(fr_texts[mishnah - 1])
    else:
        print()
        print("(Traduction française non disponible pour ce traité : "
              "la traduction de Schwab ne couvre que 38 traités sur 63.)")
    if args.mishna_analyze:
        print()
        try:
            api = load_corpus()
        except DataNotFoundError as exc:
            print(f"(Analyse grammaticale indisponible : base BHSA introuvable.)\n"
                  f"({exc})")
            return 0
        analysis = analyze_mishnah_text(api.F, api.L, he[mishnah - 1])
        print(mishnah_analysis_block(analysis, "text"))
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)

    # Mode Mishna : pas besoin de la base BHSA.
    if args.mishna and not args.list_books:
        return _run_mishna_cli(args)
    if args.list_books and args.mishna:
        print("Traités de la Mishna disponibles (nom français — nom Sefaria) :")
        for seder, tracts in SEDARIM:
            print(f"  {seder} :")
            for title, fr in tracts:
                schwab = "" if title in SCHWAB_TRACTATES else "  [sans trad. FR]"
                print(f"    - {fr}  ({title}){schwab}")
        return 0

    try:
        api = load_corpus()
    except DataNotFoundError as exc:
        print(f"Erreur : base BHSA introuvable.\n\n{exc}", file=sys.stderr)
        return 2

    if args.list_books:
        print("Livres disponibles (nom français — nom BHSA) :")
        for bhsa, fr in book_list_fr(api.F):
            print(f"  - {fr}  ({bhsa})")
        return 0

    # Mode analyse de mot isolé
    if args.word:
        F, L = api.F, api.L
        words = []
        if args.file:
            try:
                with open(args.file, encoding="utf-8") as fh:
                    words = [w.strip() for w in fh if w.strip()]
            except OSError as exc:
                print(f"Erreur de lecture du fichier : {exc}", file=sys.stderr)
                return 1
        elif args.reference:
            words = [args.reference]
        else:
            print("Erreur : en mode --word, fournissez un mot (argument) ou --file FICHIER.", file=sys.stderr)
            return 1

        any_found = False
        for i, w in enumerate(words):
            if len(words) > 1:
                print(f"\n{'='*20} Mot {i+1}/{len(words)} : {w} {'='*20}")
            analysis = analyze_word(F, L, w)
            if analysis["found"]:
                any_found = True
            if args.format == "json":
                print(format_word_json(analysis))
            else:
                print(format_word(analysis))
        return 0 if any_found else 1

    # Mode conjugaison dans tous les binyanim
    if args.binyanim:
        F, L = api.F, api.L
        verbs = []
        if args.file:
            try:
                with open(args.file, encoding="utf-8") as fh:
                    verbs = [w.strip() for w in fh if w.strip()]
            except OSError as exc:
                print(f"Erreur de lecture du fichier : {exc}", file=sys.stderr)
                return 1
        elif args.reference:
            verbs = [args.reference]
        else:
            print("Erreur : en mode --binyanim, fournissez un verbe (argument) ou --file FICHIER.",
                  file=sys.stderr)
            return 1

        any_found = False
        for i, w in enumerate(verbs):
            if len(verbs) > 1:
                print(f"\n{'='*20} Verbe {i+1}/{len(verbs)} : {w} {'='*20}")
            analysis = analyze_binyanim(F, w, use_mishnah=args.mishna_binyanim)
            if analysis["found"]:
                any_found = True
            if args.format == "json":
                print(format_binyanim_json(analysis))
            else:
                print(format_binyanim(analysis))
        return 0 if any_found else 1

    # Mode analyse de phrase libre
    if args.phrase:
        F, L = api.F, api.L
        phrases = []
        if args.file:
            try:
                with open(args.file, encoding="utf-8") as fh:
                    phrases = [p.strip() for p in fh if p.strip()]
            except OSError as exc:
                print(f"Erreur de lecture du fichier : {exc}", file=sys.stderr)
                return 1
        elif args.reference:
            phrases = [args.reference]
        else:
            print("Erreur : en mode --phrase, fournissez une phrase (argument) ou --file FICHIER.", file=sys.stderr)
            return 1

        for i, p in enumerate(phrases):
            if len(phrases) > 1:
                print(f"\n{'='*20} Phrase {i+1}/{len(phrases)} {'='*20}")
            analysis = analyze_phrase(F, L, p)
            if args.format == "json":
                print(format_phrase_json(analysis))
            else:
                print(format_phrase(analysis))
        return 0

    # Mode analyse de verset (Bible)
    if not args.reference:
        print("Erreur : une référence de verset (ou --word MOT, ou --mishna "
              "RÉFÉRENCE) est requise.", file=sys.stderr)
        return 1

    try:
        analysis = analyze_verse_by_reference(api, args.reference)
    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    b_book, b_ch, b_vs = analysis["reference"]
    def _print_translation(lang, title, enabled):
        if not enabled or args.format == "json":
            return
        try:
            idx = load_translation(language=lang)
        except TranslationNotFoundError:
            return
        trans = get_translation(idx, b_book, b_ch, b_vs)
        print(f"Traduction ({title}) — {b_book} {b_ch}:{b_vs}")
        if trans:
            print(trans)
        else:
            print("(verset absent de la traduction : numérotation différente "
                  "de la BHSA)")
        print()

    _print_translation("fr", "Louis Segond 1910", args.translation)
    _print_translation("en", "King James Version 1611", args.translation_en)
    _print_translation("es", "Reina-Valera 1909", args.translation_es)

    if args.format == "json":
        print(format_json(analysis))
    elif args.format == "summary":
        summary = format_summary(analysis)
        print("=== Règles détectées (synthèse) ===")
        for level in ("clause", "phrase", "word"):
            print(f"\n[{level}]")
            for r in summary[level]:
                print(f"  - {r}")
    else:
        print(format_text(analysis, verbose_words=not args.no_words))
    return 0


if __name__ == "__main__":
    sys.exit(main())
