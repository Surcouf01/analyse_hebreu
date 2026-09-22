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

# Marque droite-gauche (Right-to-Left Mark) : invisible, sans largeur.
# Préfixe des lignes à base RTL CONTENANT du texte latin fort : sans elle,
# to_logical ne pourrait pas distinguer, à la copie, une telle ligne visuelle
# d'une ligne à base LTR (ordre des runs inversé dans les deux sens).
RLM = "\u200F"


def _base_rtl(line):
    """Direction de base de la ligne : celle de la première lettre forte
    (standard Unicode). Hébreu/arabe → RTL, latin → LTR ; les neutres
    (ponctuation, espaces) et les chiffres sont ignorés. Par défaut RTL."""
    for ch in line:
        bd = unicodedata.bidirectional(ch)
        if bd in ("R", "AL"):
            return True
        if bd == "L":
            return False
    return True


def _has_ltr_strong(line):
    """Vrai si la ligne contient au moins une lettre forte LTR (latine)."""
    return any(unicodedata.bidirectional(c) == "L" for c in line)

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


def _visual_clusters(clusters, base_rtl=True):
    """Réordonne les clusters en ordre visuel. À l'intérieur d'un segment
    RTL les clusters sont inversés ; un segment LTR (mots latins, chiffres,
    espaces) garde son ordre interne. En base RTL les segments s'empilent
    de droite à gauche (ordre inverse) ; en base LTR (en-tête latin suivi
    d'hébreu, ex. « === Phrase analysée : … === ») ils restent dans l'ordre
    logique, pour que le préfixe latin s'affiche bien en début de ligne.
    La transformation est involutive dans les deux bases."""
    runs = []
    for c in clusters:
        rtl = _cluster_is_rtl(c)
        if runs and runs[-1][0] == rtl:
            runs[-1][1].append(c)
        else:
            runs.append((rtl, [c]))
    ordered = reversed(runs) if base_rtl else runs
    out = []
    for rtl, run in ordered:
        out.extend(reversed(run) if rtl else run)
    return out


def logical_wrap(text, measure, avail):
    """Retour à la ligne en ordre LOGIQUE pour les lignes contenant de
    l'hébreu, avant la conversion en ordre visuel.

    Tk coupe les lignes trop longues au mot près sur le texte STOCKÉ :
    en ordre visuel, la première ligne affichée contiendrait la FIN de
    la phrase (le début tomberait sur la ligne suivante). Cette fonction
    insère donc les retours à la ligne AVANT la conversion, au mot près
    (ou entre clusters pour un mot plus large que la ligne). Les lignes
    sans hébreu ne sont pas découpées : Tk les gère correctement (leur
    ordre logique est leur ordre visuel).

    ``measure(str) -> largeur`` (pixels, ou toute unité cohérente avec
    ``avail``) ; ``avail`` est la largeur disponible d'une ligne.
    """
    if not text or not avail or avail <= 0:
        return text
    out_lines = []
    for line in text.split("\n"):
        if not has_hebrew(line):
            out_lines.append(line)
            continue
        words = []
        for w in line.split(" "):
            words.extend(_split_wide_word(w, measure, avail))
        cur = ""
        for w in words:
            cand = w if not cur else cur + " " + w
            if cur and measure(cand) > avail:
                out_lines.append(cur)
                cur = w
            else:
                cur = cand
        out_lines.append(cur)
    return "\n".join(out_lines)


def _split_wide_word(word, measure, avail):
    """Coupe un mot plus large qu'une ligne entière entre clusters
    (jamais au milieu d'une lettre + nikkud)."""
    if measure(word) <= avail:
        return [word]
    parts = []
    cur = ""
    for c in _clusters(word):
        if cur and measure(cur + c) > avail:
            parts.append(cur)
            cur = c
        else:
            cur += c
    if cur:
        parts.append(cur)
    return parts


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
        base_rtl = _base_rtl(line)
        parts = []
        for c in _visual_clusters(clusters, base_rtl):
            if _cluster_is_rtl(c):
                parts.append(LRM)
            parts.append(c)
        out = "".join(parts)
        if base_rtl and _has_ltr_strong(line):
            # Ligne RTL mixte : marquée pour que to_logical retrouve la base.
            out = RLM + out
        out_lines.append(out)
    return "\n".join(out_lines)


def to_logical(text):
    """Inverse :code:`to_visual` (copie dans le presse-papiers) : retire
    les marques de directionnalité et remet les clusters en ordre
    logique."""
    if not text:
        return text
    out_lines = []
    for line in text.split("\n"):
        # Base de la ligne : marquée RLM (RTL mixte), sinon déduite du
        # contenu (RTL par défaut, LTR si la ligne contient du latin fort).
        # Les marques sont retirées AVANT le test : LRM a la classe bidi
        # « L » et fausserait la détection.
        marked_rtl = line.startswith(RLM)
        clean = _BIDI_MARKS_RE.sub("", line)
        base_rtl = marked_rtl or not _has_ltr_strong(clean)
        clusters = _clusters(clean)
        if not any(_cluster_is_rtl(c) for c in clusters):
            out_lines.append(clean)
            continue
        out_lines.append("".join(_visual_clusters(clusters, base_rtl)))
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
