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
    format_text,
    format_json,
    format_summary,
    format_word,
    format_word_json,
    format_phrase,
    format_phrase_json,
    book_list,
    DataNotFoundError,
)


def build_parser():
    p = argparse.ArgumentParser(
        prog="analyse_hebreu",
        description="Analyse grammaticale d'un verset d'hébreu biblique (BHSA/ETCBC).",
        epilog="Ex. : python analyse_hebreu.py 'Genèse 1:1' --format text",
    )
    p.add_argument(
        "reference",
        nargs="?",
        help='Référence du verset, ex. "Genèse 1:1", "Gen 1:1", "Genesis 1:1".\n'
             "Ou, avec --word, un mot hébreu à analyser (avec nikkud, sans teamim).",
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
        "--file",
        help="Fichier contenant un mot/ligne (--word) ou une phrase/ligne (--phrase).",
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
        "--list-books",
        action="store_true",
        help="Liste les livres disponibles et quitte.",
    )
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        api = load_corpus()
    except DataNotFoundError as exc:
        print(f"Erreur : base BHSA introuvable.\n\n{exc}", file=sys.stderr)
        return 2

    if args.list_books:
        print("Livres disponibles :")
        for b in book_list(api.F):
            print(f"  - {b}")
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

    # Mode analyse de verset
    if not args.reference:
        print("Erreur : une référence de verset (ou --word MOT) est requise.", file=sys.stderr)
        return 1

    try:
        analysis = analyze_verse_by_reference(api, args.reference)
    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

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
