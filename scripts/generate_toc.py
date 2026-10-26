#!/usr/bin/env python3
"""Génère la table des matières du README.

Extrait les titres markdown (niveaux 1 à 4) de ``README.md`` et :

  1. écrit ``TOC.md`` : la table des matières complète, avec liens
     hypertextes (ancres GitHub) ;
  2. insère (ou met à jour) cette table au début de ``README.md``,
     entre les marqueurs ``<!-- TOC -->`` et ``<!-- /TOC -->``.

Anti-récursivité :

  - les titres situés dans des blocs de code (clôtures ``` ou ~~~)
    ne sont pas extraits (des lignes comme ``# GUI en mode onedir``
    y sont des commentaires shell, pas des titres) ;
  - le contenu du bloc TOC existant est ignoré lors de l'extraction,
    donc le titre « Sommaire » inséré par le script ne se retrouve
    pas dans la table générée au prochain passage ;
  - la réécriture de ``README.md`` remplace le bloc entre marqueurs,
    jamais le reste du fichier.

Ancres : reproduction de l'algorithme de GitHub — minuscules,
ponctuation supprimée (les traits d'union sont conservés), espaces
remplacées par des traits d'union, doublons suffixés ``-1``, ``-2``…

Usage :

    python scripts/generate_toc.py [--check]

Sans option : génère TOC.md et met à jour README.md. Avec ``--check``
(sortie git-style) : vérifie que TOC.md et le bloc README.md sont à
jour sans rien écrire ; code de retour non nul sinon (utilisable en CI).
"""

import argparse
import re
import sys
from pathlib import Path

TOC_START = "<!-- TOC -->"
TOC_END = "<!-- /TOC -->"
MAX_LEVEL = 4

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^(```|~~~)")
_TOC_BLOCK_RE = re.compile(
    re.escape(TOC_START) + r".*?" + re.escape(TOC_END),
    re.DOTALL)


def strip_toc_block(text):
    """Retire le bloc TOC existant (marqueurs compris)."""
    return _TOC_BLOCK_RE.sub("", text)


def extract_headings(text):
    """Titres ``(niveau, texte)`` hors blocs de code."""
    headings = []
    in_fence = False
    for line in text.split("\n"):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if m:
            headings.append((len(m.group(1)), m.group(2).strip()))
    return headings


def slugify(text, seen):
    """Ancre GitHub du titre, avec déduplication (-1, -2, …)."""
    slug = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    if not slug:
        slug = "section"
    base, n = slug, 0
    while slug in seen:
        n += 1
        slug = f"{base}-{n}"
    seen.add(slug)
    return slug


def build_toc(headings, link_prefix=""):
    """Table des matières markdown : liste imbriquée de liens.

    ``link_prefix`` : préfixe d'ancre — vide pour le bloc inclus dans
    README.md (``#ancre``), ``README.md`` pour TOC.md autonome
    (``README.md#ancre``).
    """
    lines = []
    seen = set()
    top = min(lvl for lvl, _txt in headings)
    for level, text in headings:
        anchor = slugify(text, seen)
        indent = "  " * (level - top)
        lines.append(f"{indent}- [{text}]({link_prefix}#{anchor})")
    return "\n".join(lines)


def build_readme_block(toc):
    """Bloc à insérer dans README.md (marqueurs compris)."""
    return (f"{TOC_START}\n"
            f"\n"
            f"## Sommaire\n"
            f"\n"
            f"{toc}\n"
            f"\n"
            f"{TOC_END}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="vérifier sans écrire (code non nul si périmé)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    readme_path = root / "README.md"
    toc_path = root / "TOC.md"

    readme = readme_path.read_text(encoding="utf-8")

    # Extraction : sans le bloc TOC (anti-récursivité) ni le titre
    # « Sommaire » qu'il contient.
    body = strip_toc_block(readme)
    # Le titre principal (niveau 1) n'entre pas dans sa propre table.
    headings = [(lvl, txt) for lvl, txt in extract_headings(body)
                if 2 <= lvl <= MAX_LEVEL]
    if not headings:
        print("Aucun titre trouvé dans README.md", file=sys.stderr)
        return 1

    toc = build_toc(headings)

    # TOC.md : table complète, autonome (liens préfixés README.md).
    toc_doc = ("# Table des matières — README\n"
               "\n"
               "Généré par `scripts/generate_toc.py` (les liens pointent\n"
               "vers les ancres de [README.md](README.md)).\n"
               "\n"
               f"{build_toc(headings, link_prefix='README.md')}\n")

    # README.md : le bloc TOC suit le titre principal (premier niveau 1).
    # Le texte hors bloc est inchangé byte pour byte (seul le bloc entre
    # marqueurs est remplacé), pour que --check soit stable.
    lines = body.split("\n")
    insert_at = 0
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m and len(m.group(1)) == 1:
            insert_at = i + 1
            break
    if insert_at == 0:
        print("Aucun titre de niveau 1 trouvé dans README.md", file=sys.stderr)
        return 1
    # Le bloc est encadré d'une ligne vide de chaque côté ; toute ligne
    # vide résiduelle juste après (laissée par une exécution précédente)
    # est reprise telle quelle — l'ensemble est idempotent.
    new_readme = "\n".join(
        lines[:insert_at] + ["", build_readme_block(toc), ""]
        + lines[insert_at:])
    new_readme = re.sub(r"(\n" + re.escape(TOC_END) + r")\n{3,}",
                       r"\1\n\n", new_readme)

    if args.check:
        stale = []
        if toc_path.exists():
            if toc_path.read_text(encoding="utf-8") != toc_doc:
                stale.append("TOC.md")
        else:
            stale.append("TOC.md (absent)")
        if readme != new_readme:
            stale.append("README.md (bloc sommaire)")
        if stale:
            print("Périmé : " + ", ".join(stale))
            print("Régénérer : python scripts/generate_toc.py")
            return 1
        print("TOC.md et README.md à jour.")
        return 0

    toc_path.write_text(toc_doc, encoding="utf-8")
    readme_path.write_text(new_readme, encoding="utf-8")
    print(f"TOC.md généré ({len(headings)} titres) ; "
          f"sommaire inséré dans README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
