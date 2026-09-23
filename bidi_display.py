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

# Paires de caractères miroir (règle UAX #9 L4) : en contexte RTL, une
# parenthèse ouvrante est rendue avec le glyphe de sa fermante (et
# réciproquement) pour que les parenthèses ENTOURENT visuellement le mot
# qu'elles encadrent. Tk rend le texte stocké tel quel (le stockage visuel
# court-circuite son moteur bidi) : le miroir doit donc être appliqué
# explicitement, au moment du réordonnancement. Les guillemets français
# « » ne sont PAS Bidi_Mirrored (U+00AB/U+00BB) : ils ne sont pas miroités.
_MIRROR_PAIRS = {
    "(": ")", ")": "(",
    "[": "]", "]": "[",
    "{": "}", "}": "{",
    "<": ">", ">": "<",
    "\u2039": "\u203a", "\u203a": "\u2039",  # guillemets simples ‹ ›
    "\u27e8": "\u27e9", "\u27e9": "\u27e8",  # chevrons ⟨ ⟩
}


def _mirror_char(ch):
    """Glyphe miroir d'un caractère (cf. _MIRROR_PAIRS), ou lui-même."""
    return _MIRROR_PAIRS.get(ch, ch)


def _mirror_cluster(cluster):
    """Miroite les caractères miroirables d'un cluster (règle UAX #9 L4)."""
    if not any(ch in _MIRROR_PAIRS for ch in cluster):
        return cluster
    return "".join(_mirror_char(ch) for ch in cluster)


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


def _cluster_dir(cluster):
    """Direction d'un cluster : "R", "L", "EN" (chiffres) ou None
    (neutre : espaces, ponctuation). Les marques combinantes (NSM) sont
    ignorées ; c'est le caractère de base qui décide."""
    for ch in cluster:
        bd = unicodedata.bidirectional(ch)
        if bd in ("R", "AL"):
            return "R"
        if bd == "L":
            return "L"
        if bd in ("EN", "AN"):
            return "EN"
    return None


def _resolve_dirs(clusters, base_rtl):
    """Résout la direction de chaque cluster (simplification de l'algorithme
    bidi Unicode, règles W4/N1/N2 + attache des ponctuations) :

    - un séparateur de nombres (ex. « : » de « 1:1 ») entre deux chiffres
      est un nombre (règle W4) ; les chiffres (EN) forment leur propre
      segment et gardent l'ordre gauche-droite (ex. « 123 » entre deux
      mots hébreux ne s'inverse pas). Contrairement à UAX #9 (où les
      chiffres influencent les neutres comme du RTL), les chiffres sont
      ici traités comme du LTR pour cette influence : « Clause 1 : … »
      garde son deux-points à côté du texte latin ;

    - une PONCTUATION directement attachée à un mot (sans espace
      intercalé) prend la direction de ce mot : le sof pasuq « : » collé
      au dernier mot hébreu d'un verset (Sefaria l'écrit en deux-points
      ASCII, neutre) est RTL — il s'inverse avec le bloc hébreu et
      s'affiche à la FIN de lecture (bord gauche), même quand la ligne
      est à base latine (ex. « === Phrase analysée : …רוֹת: === ») ;
      sans cette règle, il se détachait du bloc et restait au bord
      droit (début de lecture) ;

    - un neutre entouré de deux forts de même direction prend cette
      direction (ex. l'espace ENTRE deux mots hébreux est RTL : tout le
      segment hébreu s'inverse d'un bloc et se lit de droite à gauche,
      même au milieu d'une ligne à base latine) ;

    - un neutre entre deux directions différentes prend la direction de
      base ; les espaces ne sont JAMAIS attachés : « מִן === » garde ses
      « === » au bord droit (fin de ligne), ils ne rejoignent pas le
      bloc hébreu.
    """
    raw = [_cluster_dir(c) for c in clusters]
    dirs = list(raw)
    n = len(dirs)
    for i in range(1, n - 1):
        if (raw[i] is None and raw[i - 1] == "EN" and raw[i + 1] == "EN"
                and len(clusters[i]) == 1
                and unicodedata.bidirectional(clusters[i][0])
                in ("CS", "ES", "ET")):
            dirs[i] = "EN"

    def nearest(i, step):
        j = i + step
        while 0 <= j < n:
            if raw[j] is not None:
                return raw[j]
            j += step
        return None

    out = []
    for i in range(n):
        d = dirs[i]
        if d is not None:
            out.append(d)
            continue
        c = clusters[i]
        # Attache : ponctuation collée à un mot fort (pas une espace).
        if not c.isspace():
            left_d = raw[i - 1] if i > 0 else None
            right_d = raw[i + 1] if i < n - 1 else None
            if left_d is not None and right_d is None:
                out.append(left_d)
                continue
            if right_d is not None and left_d is None:
                out.append(right_d)
                continue
            if left_d is not None and left_d == right_d:
                out.append(left_d)
                continue
        left = nearest(i, -1)
        right = nearest(i, +1)
        if left is not None and left == right:
            out.append(left)
        else:
            out.append("R" if base_rtl else "L")
    return out


def _visual_clusters(clusters, base_rtl=True):
    """Réordonne les clusters en ordre visuel (simplification UAX #9).

    Les clusters sont regroupés en segments de même direction résolue
    (cf. _resolve_dirs). En base RTL les segments s'empilent de droite à
    gauche (ordre inverse) ; en base LTR (en-tête latin suivi d'hébreu,
    ex. « === Phrase analysée : … === ») ils restent dans l'ordre
    logique, pour que le préfixe latin s'affiche en début de ligne. Dans
    tous les cas, un segment RTL voit ses clusters inversés : chaque mot
    ET l'ordre des mots du segment (le segment forme un bloc qui se lit
    de droite à gauche), tandis que les segments LTR et les nombres
    gardent l'ordre gauche-droite. La transformation est involutive."""
    resolved = _resolve_dirs(clusters, base_rtl)
    runs = []
    for c, d in zip(clusters, resolved):
        if runs and runs[-1][0] == d:
            runs[-1][1].append(c)
        else:
            runs.append((d, [c]))
    ordered = list(reversed(runs)) if base_rtl else runs
    out = []
    for d, run in ordered:
        if d == "R":
            # Règle UAX #9 L4 : un caractère miroir résolu RTL est rendu avec
            # son glyphe miroir. La transformation est involutive : to_logical
            # re-résout les directions et re-miroite, ce qui restitue
            # l'original à la copie.
            out.extend(_mirror_cluster(c) for c in reversed(run))
        else:
            out.extend(run)
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

    Chaque fragment replié est préfixé du marqueur de la direction de
    base de la ligne D'ORIGINE (RLM = RTL, double LRM = LTR, cf.
    _split_base_marker) : un fragment qui commence par de l'hébreu ne
    doit pas redevenir base RTL — sinon le suffixe neutre de la ligne
    (ex. « === ») s'afficherait à gauche au lieu de rester en fin de
    ligne. Les lignes non coupées ne sont pas marquées.

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
        mark = RLM if _base_rtl(line) else LRM + LRM
        words = []
        for w in line.split(" "):
            words.extend(_split_wide_word(w, measure, avail))
        cur = ""
        split_lines = []
        for w in words:
            cand = w if not cur else cur + " " + w
            if cur and measure(cand) > avail:
                split_lines.append(cur)
                cur = w
            else:
                cur = cand
        split_lines.append(cur)
        if len(split_lines) == 1:
            # Ligne non coupée : pas de marque, to_visual déduit la base.
            out_lines.append(split_lines[0])
        else:
            out_lines.extend(mark + l for l in split_lines)
    return "\n".join(out_lines)


def _split_base_marker(line):
    """Retire le marqueur de base en tête de ligne et le renvoie.

    Convention (cf. to_visual) :
      - RLM en tête : base RTL — le RLM n'est jamais utilisé comme
        marque de cluster, aucune ambiguïté ;
      - deux LRM ou plus en tête : base LTR — les fragments repliés
        d'une ligne à base LTR qui commencent par de l'hébreu en ont
        besoin (une marque de cluster LRM précède chaque cluster
        hébreu, un LRM unique n'est donc pas un marqueur de base) ;
      - un seul LRM : marque de cluster du premier mot, pas un
        marqueur — la base est déduite du contenu.

    Renvoie ``(base_rtl | None, reste)``.
    """
    i = 0
    while i < len(line) and line[i] in (LRM, RLM):
        i += 1
    marks = line[:i]
    rest = line[i:]
    if not marks:
        return None, line
    if RLM in marks:
        return True, rest
    if len(marks) >= 2:
        return False, rest
    return None, line


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
        forced, line = _split_base_marker(line)
        line = _BIDI_MARKS_RE.sub("", line)
        clusters = _clusters(line)
        if not any(_cluster_is_rtl(c) for c in clusters):
            out_lines.append(line)
            continue
        base_rtl = _base_rtl(line) if forced is None else forced
        parts = []
        for c in _visual_clusters(clusters, base_rtl):
            if _cluster_is_rtl(c):
                parts.append(LRM)
            parts.append(c)
        # Marque de base en tête pour rester inversible à la copie :
        # nécessaire si la base ne peut pas être redéduite du contenu —
        # ligne à base RTL CONTENANT du latin (sinon redéduite LTR), ou
        # ligne à base LTR (redéduite RTL par défaut). L'hébreu pur non
        # marqué reste RTL par défaut.
        out = "".join(parts)
        if (base_rtl and _has_ltr_strong(line)) or not base_rtl:
            out = (RLM if base_rtl else LRM + LRM) + out
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
        # Base de la ligne : marque en tête (RLM = RTL, double LRM = LTR,
        # cf. _split_base_marker), sinon déduite du contenu.
        marked, line = _split_base_marker(line)
        clean = _BIDI_MARKS_RE.sub("", line)
        clusters = _clusters(clean)
        if not any(_cluster_is_rtl(c) for c in clusters):
            out_lines.append(clean)
            continue
        if marked is None:
            marked = not _has_ltr_strong(clean)
        out_lines.append("".join(_visual_clusters(clusters, marked)))
    return "\n".join(out_lines)


def visual_hebrew_word_range(line, col):
    """Étendue ``(début, fin)`` du mot hébreu contenant la colonne
    ``col`` dans une ligne en ordre visuel, marques LRM incluses ; ``None``
    si la colonne n'est pas dans un mot hébreu."""
    for m in _HEBREW_WORD_RE.finditer(line):
        if m.start() <= col < m.end():
            return m.start(), m.end()
    return None


# --- Recherche consonantique (Ctrl-F dans la zone de résultat) ---------


def consonant_skeleton(text):
    """Squelette consonantique : lettres hébraïques nues (U+05D0..U+05EA),
    sans nikkud, sans teamim, sans daguesh, sans point shin/sin ; les
    autres caractères (latin, chiffres, ponctuation, espaces, marques
    bidi) sont ignorés."""
    return "".join(c for c in text if 0x05D0 <= ord(c) <= 0x05EA)


def has_hebrew_letters(text):
    """Vrai si le texte contient au moins une lettre hébraïque (les
    seules consonnes, voyelles-point et accents ne comptent pas)."""
    return any(0x05D0 <= ord(c) <= 0x05EA for c in text)


def _visual_cluster_indices(clusters, base_rtl=True):
    """Permutation associée à :code:`_visual_clusters` : renvoie ``perm``
    tel que le cluster en position logique (de lecture) ``k`` est
    ``clusters[perm[k]]``. Même calcul (runs de direction, inversion des
    runs RTL, empilement des segments), mais sur les INDICES — les
    clusters de contenu identique (deux « א » sans nikkud) ne sont pas
    confondus.
    """
    resolved = _resolve_dirs(clusters, base_rtl)
    runs = []
    for i, d in enumerate(resolved):
        if runs and runs[-1][0] == d:
            runs[-1][1].append(i)
        else:
            runs.append((d, [i]))
    ordered = list(reversed(runs)) if base_rtl else runs
    perm = []
    for d, run in ordered:
        perm.extend(reversed(run) if d == "R" else run)
    return perm


def _stored_clusters(visual_line):
    """Clusters réels (hors marques bidi LRM/RLM) d'une ligne stockée en
    ordre visuel : liste ``[(début, fin, texte)]`` en coordonnées du texte
    STOCKÉ (marques comprises) — directement utilisables comme indices de
    colonne Tk. Renvoie ``(clusters, base_rtl)`` ; ``base_rtl`` suit la
    même déduction que :code:`to_logical` (marque en tête, sinon contenu).
    """
    marked, stripped = _split_base_marker(visual_line)
    out = []
    # Positions dans la ligne TELLE QUE STOCKÉE : le marqueur de base en
    # tête (RLM ou double LRM) compte dans les indices Tk.
    pos = len(visual_line) - len(stripped)
    for cl in _clusters(stripped):
        if all(unicodedata.category(ch) == "Cf" for ch in cl):
            pos += len(cl)
            continue
        out.append((pos, pos + len(cl), cl))
        pos += len(cl)
    clean = _BIDI_MARKS_RE.sub("", stripped)
    if not any(_cluster_is_rtl(c) for c in _clusters(clean)):
        return out, None
    if marked is None:
        marked = not _has_ltr_strong(clean)
    return out, marked


def find_line_matches(visual_line, query_skeleton):
    """Recherche le squelette consonantique ``query_skeleton`` dans une
    ligne stockée en ordre visuel, et renvoie les correspondances en
    indices du texte STOCKÉ (marques LRM/RLM comprises) — directement
    surlignables dans le widget.

    La zone de résultat affiche l'hébreu en ordre VISUEL (mots inversés
    entre eux, chaque mot gardant l'ordre de ses lettres) avec des marques
    bidi invisibles. Chercher la sous-chaîne directement échouerait : les
    marques pollueraient le texte et l'ordre visuel des mots est l'inverse
    de l'ordre de lecture. On cherche donc sur le squelette consonantique
    — consonnes hébraïques seules, nikkud/teamim/daguesh ignorés — en
    ordre LOGIQUE de lecture (les consonnes de la requête se lisent dans
    le même sens que celles de la ligne), puis on projette chaque
    correspondance sur les clusters stockés via la permutation bidi
    (cf. _visual_cluster_indices).

    Renvoie ``[(début, fin), …]`` en indices du texte stocké, en ordre de
    LECTURE (ordre logique : droite à gauche à l'écran pour l'hébreu) —
    l'ordre naturel pour naviguer d'occurrence en occurrence. L'étendue
    couvre la première à la dernière consonne de l'occurrence, marques
    combinantes (nikkud/teamim) et caractères intercalés (espace, maqaf)
    inclus.
    """
    if not query_skeleton:
        return []
    stored, base_rtl = _stored_clusters(visual_line)
    if not stored or base_rtl is None:
        return []
    perm = _visual_cluster_indices([c for _s, _e, c in stored], base_rtl)
    if len(perm) != len(stored):
        return []
    # Entrées en ordre de lecture : une par cluster portant des lettres
    # hébraïques (les espaces/latin/ponctuation ne comptent pas).
    entries = []
    for k in perm:
        start, end, text = stored[k]
        letters = consonant_skeleton(text)
        if letters:
            entries.append((letters, start, end))
    if not entries:
        return []
    skel = "".join(e[0] for e in entries)
    matches = []
    begin = 0
    while True:
        j = skel.find(query_skeleton, begin)
        if j < 0:
            break
        covered = entries[j:j + len(query_skeleton)]
        spans = [(s, e) for _l, s, e in covered]
        vis_start = min(s for s, _e in spans)
        vis_end = max(e for _s, e in spans)
        matches.append((vis_start, vis_end))
        begin = j + 1
    return matches


def normalize_query(text, visual=False):
    """Normalise une requête de recherche en squelette consonantique :
    retire nikkud, teamim, daguesh, points shin/sin et marques bidi — il
    ne reste que les consonnes hébraïques, en ordre de lecture.

    ``visual=True`` pour un texte issu de la zone de résultat (sélection
    en ordre visuel, convertie ici via :code:`to_logical`, comme le fait
    Ctrl+C) ; une saisie au clavier (virtuel ou physique) est déjà en
    ordre logique et passe avec ``visual=False``.
    """
    if visual:
        text = to_logical(text)
    return consonant_skeleton(text)



def visual_cluster_bounds(line):
    """Bornes ``(début, fin)`` de chaque cluster hébreu (LRM + lettre +
    voyelles/accents) d'une ligne en ordre visuel.

    Utilisé pour aligner clics et sélection sur les lettres pointées : le
    curseur ne se place jamais au milieu d'un cluster.
    """
    return [(m.start(), m.end()) for m in _VISUAL_CLUSTER_RE.finditer(line)]
