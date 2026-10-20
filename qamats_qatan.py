#!/usr/bin/env python3
"""Détection du qamats qatan (voyelle /o/, U+05C7) dans un texte voyellé.

Règle canonique (Joüon §88A–B ; GKC §9b ; voir aussi Gesenius' Hebrew
Grammar) : un qamats (U+05B8) se lit /o/ (qamats qatan) quand il se
trouve dans une **syllabe fermée non accentuée** :

  - syllabe fermée : suivie de deux consonnes (sheva naḥ après la
    consonne post-vocalique, ou voyelle suivie d'une consonne finale) ;
  - non accentuée : le teamim du mot ne place pas l'accent sur cette
    syllabe (accents discrets et conjonctifs, U+0591–U+05AE/05AF).

Exceptions appliquées :

  1. Begadkefat : une syllabe « fermée » par un dagesh lene
     (בגדכפת post-vocalique) est en fait historiquement ouverte — le
     dagesh lene est un artefact de prononciation ; qamats gadol.
  2. Gutturales : un qamats suivi d'une gutturale portant un sheva
     composé (hateph) ou une gutturale qui rouvre la syllabe reste
     le plus souvent gadol (ex. נָעֳמִי Naʿomi, pas Noʿomi).
  3. Mot monosyllabique accentué (silluq/paštaʾ…) : gadol.

L'API principale est ``qamats_qatan_text(text)`` : analyse un verset
(ou un mot) et remplace les qamats qatan détectés par U+05C7 (le
point d'interrogation inversé hébreu, « qamats qatan » Unicode 5.0).
``detect_qamats_qatan(text)`` renvoie les positions détectées sans
modifier le texte.

L'usage initial est le prétraitement du verset avant la synthèse
vocale (phonikud lit U+05C7 comme /o/, mais l'ambigu U+05B8 comme
/a/ d'après le contexte heuristique — la conversion explicite force
la lecture correcte, ex. כָּל kol et non kal).
"""

import re

QAMATS = "\u05B8"          # ָ qamats
QAMATS_QATAN = "\u05C7"    # ׇ qamats qatan explicite
SHEVA = "\u05B0"           # ְ
HATEPH_SEGOL = "\u05B1"
HATEPH_PATAH = "\u05B2"
HATEPH_QAMATS = "\u05B3"
HIREQ = "\u05B4"
TSERE = "\u05B5"
SEGOL = "\u05B6"
PATAH = "\u05B7"
HOLAM = "\u05B9"
QUBUTS = "\u05BB"
DAGESH = "\u05BC"
HATAF = (HATEPH_SEGOL, HATEPH_PATAH, HATEPH_QAMATS)
NIKKUD = (SHEVA, HIREQ, TSERE, SEGOL, PATAH, QAMATS, HOLAM, QUBUTS,
          HATEPH_SEGOL, HATEPH_PATAH, HATEPH_QAMATS, DAGESH,
          QUBUTS, QAMATS_QATAN,
          "\u05C1", "\u05C2")  # + points shin/sin
VOWELS = (HIREQ, TSERE, SEGOL, PATAH, QAMATS, HOLAM, QUBUTS) + HATAF
HOLAM_HASER = "\u05BA"    # וֺ holam haser (sur le vav)
VOWELS = VOWELS + (HOLAM_HASER,)
GUTTURALS = "\u05D0\u05D4\u05D7\u05E2"   # א ה ח ע
BEGADKEFAT = "\u05D1\u05D2\u05D3\u05DB\u05E4\u05EA"  # בגדכפת
LETTERS = "\u05D0-\u05EA"

# Teamim : accents discrets (positifs) et conjonctifs, U+0591–U+05AF.
_TEAMIM_RE = re.compile("[\u0591-\u05af\u05bd\u05c0\u05c3\u05c6]")
# Séparateurs de mots.
_SPLIT_RE = re.compile(f"[^{LETTERS}{re.escape(''.join(NIKKUD))}\u05bf\u05be]+")


# Exceptions lexicales : mots dont le pattern graphique (qamats + sheva
# + consonne vocalisée) correspond à un sheva NAʿ (syllabe ouverte), non
# détectable graphiquement — identique à des cas qatan comme חָכְמָה.
# Squelette consonantique (sans nikkud) des mots concernés.
_LEXICAL_GADOL = {
    "\u05d7\u05e0\u05d9\u05d4",   # חניה khanəyā (sheva naʿ)
    "\u05d1\u05e0\u05d9\u05d4",   # בניה banəyā
    "\u05e2\u05dc\u05d9\u05d5\u05df",  # עליון ʿalyon (ʿa-lyon)
}


def _skeleton(word):
    """Squelette consonantique d'un mot (nikkud et teamim retirés)."""
    return "".join(ch for ch in word
                   if "\u05d0" <= ch <= "\u05ea"
                   or ch in "\u05d9\u05d5")


def _letters_after(text, i):
    """Itérateur (lettre, nikkud_qui_la_suivent) à partir de l'index i.

    Les marques (dagesh, shin/sin dot) qui suivent ``i`` appartiennent à
    la consonne du cluster courant : elles sont sautées avant d'atteindre
    la consonne suivante.
    """
    out = []
    n = len(text)
    j = i
    # Sauter les marques restantes du cluster courant (ex. dagesh du
    # begadkefat après le qamats : כָּל).
    while j < n and text[j] in NIKKUD:
        j += 1
    while j < n:
        ch = text[j]
        if "\u05D0" <= ch <= "\u05EA":
            # consonne : rassembler ses marques
            k = j + 1
            marks = ""
            while k < n and text[k] in NIKKUD:
                marks += text[k]
                k += 1
            out.append((ch, marks))
            j = k
        elif ch == "\u05BF":       # rafe : marque, on continue
            j += 1
        elif ch == "\u05BE":       # maqqef : fin du mot logique
            break
        else:
            break
    return out


def _is_closed_unstressed(word, qamats_idx, accents_pos):
    """Le qamats à ``qamats_idx`` est-il dans une syllabe fermée
    non accentuée ? (règle principale + exceptions begadkefat/gutturales)

    ``accents_pos`` : indices (dans le mot) des caractères portant un
    teamim (accent), positions d'accent connues.
    """
    seq = _letters_after(word, qamats_idx + 1)
    if not seq:
        return False
    cons, marks = seq[0]
    nxt = seq[1] if len(seq) > 1 else None

    # ה final sans mappiq (ni dagesh) après le qamats : mater lectionis,
    # la syllabe est OUVERTE (חָכְמָה khokh-mā) — gadol.
    if cons == "\u05D4" and DAGESH not in marks and nxt is None:
        return False

    # Exception 1 : gutturale suivie d'un hateph — la syllabe se rouvre
    # (נָעֳמִי Naʿomi) : gadol.
    if cons in GUTTURALS and any(h in marks for h in HATAF):
        return False

    # Syllabe fermée ?
    #  a) consonne suivie d'un sheva (naḥ) puis d'une autre consonne,
    #     ou d'une voyelle puis consonne : fermée.
    #  b) la consonne est finale et ne porte pas de voyelle : fermée.
    if SHEVA in marks and not any(v in marks for v in VOWELS):
        # sheva nu (silencieux) : syllabe fermée par la consonne suivante.
        closed = True
        # Sheva naʿ (vocal) : après une syllabe OUVERTE courte (le cas
        # du qamats gadol justement), le sheva se prononce et la syllabe
        # du qamats est ouverte : חָנְיָה kha-ne-ya. Indices graphiques du
        # sheva naʿ : consonne suivante porte une voyelle ET la lettre
        # après le sheva est yod/vav sans voyelle (mater) ou la voyelle
        # du qamats serait dans une syllabe ouverte.
        if nxt is not None:
            ncons, nmarks = nxt
            if ncons == "\u05D9" and not any(v in nmarks for v in VOWELS):
                # Sheva naʿ graphique sûr : sheva + yod nu (mater de la
                # syllabe suivante) — חָנְיָה kha-ne-yā : gadol. Les autres
                # cas de sheva naʿ exigent la grammaire du mot : la règle
                # graphique standard les laisse en syllabe fermée.
                return False
        # Exception begadkefat : dagesh lene sur la consonne SUIVANTE
        # (après le sheva) — la fermeture est artificielle.
        if nxt is not None:
            ncons, nmarks = nxt
            if DAGESH in nmarks and ncons in BEGADKEFAT:
                # dagesh lene après sheva : בָּרַךְ type — gadol.
                return False
            # sheva naḥ + gutturale rouverte : חָכְמָה est fermée (khokh),
            # mais אָחְלַי... reste gadol : on ne ferme pas devant une
            # gutturale portant voyelle longue.
            if ncons in GUTTURALS and any(v in nmarks for v in (TSERE, HOLAM, QAMATS)):
                return False
    elif any(v in marks for v in VOWELS):
        # consonne portant une voyelle : la syllabe du qamats est ouverte.
        return False
    else:
        # Pas de voyelle NI sheva écrit sur la consonne suivante :
        # - fin de mot (כָּל) : fermée ;
        # - suivie d'une consonne vocalisée (שָׁלוֹם : lamed nu puis
        #   vav+holam) : le sheva non écrit est naʿ, la syllabe du
        #   qamats est OUVERTE — gadol. Un sheva ÉCRIT (חָכְמָה)
        #   marque seul la fermeture certaine.
        if nxt is not None:
            ncons, nmarks = nxt
            if any(v in nmarks for v in VOWELS) or ncons in "\u05D5\u05D9":
                closed = False
            else:
                closed = True
        else:
            closed = True

    if not closed:
        return False

    # Non accentuée : le teamim ne tombe ni sur la consonne de la
    # syllabe, ni sur le qamats lui-même (certains accents se posent
    # sur la voyelle).
    for pos in accents_pos:
        if qamats_idx - 2 <= pos <= qamats_idx + 2:
            return False
    # Sans teamim (mot isolé) : accent par défaut sur la dernière
    # voyelle du mot — un qamats final accentué reste gadol
    # (ex. אָמְנָם om-nam). Exception : le monosyllabe fermé
    # (une seule voyelle dans le mot) reste qatan — כָּל kol porte
    # l'accent ET un qamats qatan (Joüon §88Bc : le qatan des
    # monosyllabes est accentué).
    if not accents_pos:
        vowels_idx = [i for i, ch in enumerate(word) if ch in VOWELS]
        if len(vowels_idx) <= 1:
            return True  # monosyllabe fermé : qatan
        if qamats_idx == vowels_idx[-1]:
            return False
    return True


def _accent_positions(word):
    """Indices des positions d'accent (teamim) dans le mot."""
    return [i for i, ch in enumerate(word) if _TEAMIM_RE.match(ch)]


def detect_qamats_qatan(text):
    """Positions des qamats à lire comme qatan (/o/), par mot.

    Renvoie une liste de (index_de_début_de_mot, index_du_qamats_dans_le_mot).
    """
    results = []
    words = []
    start = 0
    for m in _SPLIT_RE.finditer(text):
        if m.start() > start:
            words.append((start, text[start:m.start()]))
        start = m.end()
    if start < len(text):
        words.append((start, text[start:]))
    for w_start, word in words:
        if QAMATS not in word:
            continue
        # Exception lexicale : motif à sheva naʿ indécidable graphiquement.
        if _skeleton(word) in _LEXICAL_GADOL:
            continue
        accents = _accent_positions(word)
        for i, ch in enumerate(word):
            if ch == QAMATS:
                if _is_closed_unstressed(word, i, accents):
                    results.append((w_start, i))
    return results


def qamats_qatan_text(text):
    """Remplace les qamats qatan détectés par U+05C7 dans ``text``.

    Retourne (nouveau_texte, nb_remplacements).
    """
    out = list(text)
    count = 0
    for w_start, i in detect_qamats_qatan(text):
        out[w_start + i] = QAMATS_QATAN
        count += 1
    return "".join(out), count


def apply_for_speech(text):
    """Prétraitement pour la synthèse vocale : les qamats qatan détectés
    sont convertis en HOLAM (U+05B9), voyelle /o/ non ambiguë.

    On n'insère pas U+05C7 : le nettoyage des teamim avant la
    phonémisation (verse_audio.strip_teamim) retire la plage
    U+05C3..U+05C7 qui le contient. Le holam porte la même valeur /o/
    et survit au nettoyage — phonikud le lira /o/ (ex. כָּל kol et non
    kal).

    Le rendu écrit garde U+05B8 (le texte biblique n'encode pas la
    distinction) : cette conversion ne concerne que la parole.
    """
    new_text, _count = qamats_qatan_text(text)
    return new_text.replace(QAMATS_QATAN, HOLAM)
