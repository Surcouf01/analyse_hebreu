"""Affichage droite-à-gauche stable du texte hébreu pour le GUI Tk.

Le widget Text de Tk affiche l'hébreu correctement (le moteur de rendu de
la plateforme réordonne les lettres de droite à gauche), mais toutes ses
opérations de géométrie — clic de souris (``@x,y``), bornes de la
sélection, copie — travaillent sur l'ordre LOGIQUE du texte stocké. Sur une
ligne hébraïque, la position cliquée correspond donc à un autre caractère
que celui affiché sous le curseur : la sélection « danse » et devient
impossible à contrôler.

La solution : stocker dans le widget un texte déjà réordonné en ordre
VISUEL. L'ordre logique du widget coïncide alors avec l'ordre affiché, et
la sélection à la souris devient stable et prévisible.

Deux précautions supplémentaires :

- Chaque cluster RTL (lettre + voyelles/accents) est précédé d'une marque
  LRM (U+200E) : le rendu de chaque fragment reste identique, même quand la
  ligne est découpée par le surlignage de sélection ou par le retour à la
  ligne (Tk dessine chaque fragment indépendamment).

- La copie (Ctrl+C) restitue l'ordre logique d'origine : les marques sont
  retirées puis les clusters réordonnés (la transformation est
  involutive).

Seul le GUI est concerné ; la sortie CLI n'est pas modifiée (le terminal
applique lui-même l'algorithme bidi).
"""

import re
import unicodedata

# Marque gauche-droite (Left-to-Right Mark) : invisible, sans largeur.
LRM = "\u200E"

# Cluster hébreu en ordre visuel : LRM + une lettre de base (consonne ou
# voyelle lettre) suivie de ses marques combinantes — nikkud U+05B0..U+05BD,
# daguesh U+05BC, points shin/sin U+05C1..U+05C2, teamim U+0591..U+05AF.
# Le sof pasuq U+05C3, porteur, forme son propre cluster.
_VISUAL_CLUSTER_RE = re.compile(
    "\u200E[\u05D0-\u05EA\u05EF][\u0591-\u05BD\u05BF\u05C1\u05C2]*"
    "|\u200E\u05C3"
)

# Mot hébreu dans une ligne en ordre visuel : suite contiguë de clusters.
_HEBREW_WORD_RE = re.compile("(?:\u200E[\u0590-\u05FF]+)+")

# Toutes les marques de directionnalité, retirées à la copie.
_BIDI_MARKS_RE = re.compile(
    "[\u200E\u200F\u202A\u202B\u202C\u202D\u202E"
    "\u2066\u2067\u2068\u2069]"
)


def _is_hebrew_char(ch):
    """Vrai pour tout caractère du bloc hébreu (lettres, voyelles/nikkud,
    accents/teamim, ponctuation : U+0590..U+05FF)."""
    return "\u0590" <= ch <= "\u05FF"


def has_hebrew(line):
    """Vrai si la ligne contient au moins un caractère hébreu."""
    return any(_is_hebrew_char(c) for c in line)


def _clusters(line):
    """Découpe une ligne en clusters de graphèmes : une lettre de base
    suivie de ses marques combinantes (nikkud, daguesh, teamim). Les
    marques de directionnalité (catégorie Cf, ex. LRM) forment leur
    propre cluster — elles ne se rattache jamais à la lettre précédente."""
    clusters = []
    for ch in line:
        if (clusters
                and (unicodedata.combining(ch) > 0
                     or unicodedata.category(ch) in ("Mn", "Me"))):
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return clusters


def _cluster_is_rtl(cluster):
    """Vrai si le cluster contient au moins un caractère hébreu."""
    return any(_is_hebrew_char(c) for c in cluster)


def _visual_clusters(clusters):
    """Réordonne les clusters en ordre visuel (ligne à base RTL) : les
    segments s'empilent de droite à gauche ; à l'intérieur d'un segment
    RTL les clusters sont inversés, un segment LTR (mots latins, chiffres,
    espaces) garde son ordre interne. La transformation est involutive."""
    runs = []
    for c in clusters:
        rtl = _cluster_is_rtl(c)
        if runs and runs[-1][0] == rtl:
            runs[-1][1].append(c)
        else:
            runs.append((rtl, [c]))
    out = []
    for rtl, run in reversed(runs):
        out.extend(reversed(run) if rtl else run)
    return out


def to_visual(text):
    """Prépare un texte pour un affichage hébreu stable dans le GUI.

    Chaque ligne contenant de l'hébreu est mise en ordre visuel, chaque
    cluster RTL étant précédé d'une marque LRM ; les lignes sans hébreu
    sont laissées inchangées. L'entrée doit être en ordre logique
    (toute marque de directionnalité déjà présente est d'abord retirée).
    """
    if not text:
        return text
    out_lines = []
    for line in text.split("\n"):
        line = _BIDI_MARKS_RE.sub("", line)
        clusters = _clusters(line)
        if not any(_cluster_is_rtl(c) for c in clusters):
            out_lines.append(line)
            continue
        parts = []
        for c in _visual_clusters(clusters):
            if _cluster_is_rtl(c):
                parts.append(LRM)
            parts.append(c)
        out_lines.append("".join(parts))
    return "\n".join(out_lines)


def to_logical(text):
    """Inverse :code:`to_visual` (copie dans le presse-papiers) : retire
    les marques de directionnalité et remet les clusters en ordre
    logique."""
    if not text:
        return text
    out_lines = []
    for line in text.split("\n"):
        clean = _BIDI_MARKS_RE.sub("", line)
        clusters = _clusters(clean)
        if not any(_cluster_is_rtl(c) for c in clusters):
            out_lines.append(clean)
            continue
        out_lines.append("".join(_visual_clusters(clusters)))
    return "\n".join(out_lines)


def visual_hebrew_word_range(line, col):
    """Étendue ``(début, fin)`` du mot hébreu contenant la colonne
    ``col`` dans une ligne en ordre visuel, marques LRM incluses ; ``None``
    si la colonne n'est pas dans un mot hébreu."""
    for m in _HEBREW_WORD_RE.finditer(line):
        if m.start() <= col < m.end():
            return m.start(), m.end()
    return None


def visual_cluster_bounds(line):
    """Bornes ``(début, fin)`` de chaque cluster hébreu (LRM + lettre +
    voyelles/accents) d'une ligne en ordre visuel.

    Utilisé pour aligner clics et sélection sur les lettres pointées : le
    curseur ne se place jamais au milieu d'un cluster.
    """
    return [(m.start(), m.end()) for m in _VISUAL_CLUSTER_RE.finditer(line)]
