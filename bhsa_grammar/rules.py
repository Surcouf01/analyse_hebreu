"""Moteur de règles grammaticales pour l'hébreu biblique (BHSA/ETCBC).

Chaque règle est une fonction qui prend un nœud (word, phrase, clause) et le
contexte (l'API Text-Fabric) et renvoie une liste de règles détectées sous forme
de chaînes explicatives en français. Les règles s'appuient sur les features
morphologiques et syntaxiques de la base BHSA.
"""

from . import morph_fr as M


def _fv(F, name, node):
    """Renvoie la valeur d'une feature, ou None."""
    feat = getattr(F, name, None)
    if feat is None:
        return None
    return feat.v(node)


def _clean(val):
    if val is None:
        return None
    if val in ("NA", "none", "None", "unknown", ""):
        return None
    return val


def _detect_volitive(ps, pfm, nme, cons):
    """Détecte le mode volitif (cohortif / jussif) d'un yiqtol.

    La BHSA code cohortif et jussif comme « impf ». La distinction se fait par :
      - cohortif : 1re personne + préfixe א (pfm '>') + voyelle longue,
        souvent marqué par un ה final (nme contient 'H' ou la forme finit par ה).
      - jussif : 3e personne, forme courte (nme absent, sans suffixe long).
    Renvoie 'cohortif', 'jussif' ou None.
    """
    if ps == "p1":
        # Cohortif : préfixe א. On est prudent : sans voyelle longue on reste yiqtol.
        if pfm == ">":
            # Cohortif si la forme a une finale allongée (ה, ou nme long).
            if nme and ("H" in nme or len(nme) >= 1):
                return "cohortif"
            # Sans marque explicite, on signale le potentiel cohortif uniquement
            # si la consonne finale est ה (voyelle longue parahque).
            if cons and cons.endswith("H"):
                return "cohortif"
    # NB : le jussif (3e personne) ne se distingue morphologiquement du yiqtol
    # que par la forme courte, ce qui est ambigu sans contexte (négation לֹא/אַל,
    # particule לוּ). On évite donc de sur-détecter et on laisse l'utilisateur
    # trancher ; la règle n'est émise qu'en mode « phrase libre » où un marqueur
    # négatif précède (voir phrase_analyzer).
    return None


# --------------------------------------------------------------------------- #
# Règles au niveau du MOT
# --------------------------------------------------------------------------- #

def word_rules(F, L, w):
    """Analyse un mot et renvoie une liste de descriptions de règles grammaticales."""
    rules = []
    sp = _clean(_fv(F, "sp", w))
    pdp = _clean(_fv(F, "pdp", w))
    gn = _clean(_fv(F, "gn", w))
    nu = _clean(_fv(F, "nu", w))
    ps = _clean(_fv(F, "ps", w))
    st = _clean(_fv(F, "st", w))
    vt = _clean(_fv(F, "vt", w))
    vs = _clean(_fv(F, "vs", w))
    ls = _clean(_fv(F, "ls", w))
    prs = _clean(_fv(F, "prs", w))
    lex = _clean(_fv(F, "lex_utf8", w))
    cons = _clean(_fv(F, "g_cons", w))

    # Article défini (ה)
    if sp == "art" or pdp == "art":
        rules.append("Article défini (hé préfixé) : marque la détermination du nom suivant.")

    # Conjonction waw (ו)
    if cons and cons.startswith("W") and sp == "conj":
        rules.append("Waw conjonctif (ו) : relie ou coordonne ; peut marquer continuation, addition, ou apodose.")

    # Verbe
    if sp == "verb":
        tense = M.t(M.VERB_TENSE, vt)
        stem = M.t(M.STEM, vs)
        person = M.t(M.PERSON, ps)
        gender = M.t(M.GENDER, gn)
        number = M.t(M.NUMBER, nu)
        rules.append(
            f"Verbe : binyan {stem}, {tense}, {person}, {gender}, {number}."
        )
        if vt == "wayq":
            rules.append(
                "Wayyiqtol : forme narrative séquentielle (waw + yiqtol), "
                "exprime une action successive/consécutive au récit passé."
            )
        if vt == "perf":
            rules.append(
                "Qatal (perfectif) : action vue comme accomplie/ponctuelle, "
                "souvent passé narratif ou parfait de constatation."
            )
        if vt == "impf":
            # Détecter le mode volitif : cohortif (1re pers) ou jussif (3e pers
            # court). La BHSA code tout en « impf » ; la distinction vient de la
            # morphologie (préfixe א + voyelle longue pour le cohortif ; forme
            # courte pour le jussif).
            pfm = _clean(_fv(F, "pfm", w))
            nme = _clean(_fv(F, "nme", w))
            volitive = _detect_volitive(ps, pfm, nme, cons)
            base_desc = (
                "Yiqtol (imperfectif) : action inaccomplie, volitif, futur, "
                "habituel ou modal selon le contexte."
            )
            if volitive == "cohortif":
                rules.append(
                    "Yiqtol de cohortif (1re personne) : injonction à la 1re "
                    "personne (« faisons… », « que je… »), marqué par le préfixe "
                    "א + voyelle longue (ה final)."
                )
            elif volitive == "jussif":
                rules.append(
                    "Yiqtol de jussif (3e personne courte) : ordre/permission "
                    "à la 3e personne (« qu'il fasse… »), forme courte sans "
                    "suffixe long."
                )
            else:
                rules.append(base_desc)
        if vt == "impv":
            rules.append("Impératif : ordre/injonction (2e personne).")
        if vt == "infq":
            rules.append("Infinitif construit : forme nominale du verbe, souvent prépositionnel.")
        if vt == "infc":
            rules.append("Infinitif absolu : accentuation/adverbe verbal, parfois indépendant.")
        if vt in ("ptca", "ptcp"):
            rules.append("Participe : forme nominale exprimant l'aspect inaccompli ou l'état.")

    # Substantif / nom
    if sp in ("subs", "nmpr") or pdp in ("subs", "nmpr"):
        etat = M.t(M.STATE, st)
        gender = M.t(M.GENDER, gn)
        number = M.t(M.NUMBER, nu)
        label = "Nom propre" if sp == "nmpr" else "Substantif"
        rules.append(f"{label} : {etat}, {gender}, {number}.")
        if st == "c":
            rules.append(
                "État construit : le nom est lié au mot suivant (complément du nom), "
                "forme une chaîne de génitif/annexion."
            )
        if st == "e":
            rules.append("État emphatique : détermination par l'article (araméen).")

    # Préposition
    if sp == "prep" or pdp == "prep":
        rules.append("Préposition (souvent préfixée) : introduit un complément (lieu, temps, agent, etc.).")

    # Pronom indépendant
    if sp in ("prps", "pron") and pdp == "prps":
        rules.append(f"Pronom personnel indépendant : {M.t(M.PERSON, ps)}, {M.t(M.GENDER, gn)}, {M.t(M.NUMBER, nu)}.")

    # Suffixe pronominal (uniquement si un vrai suffixe est présent)
    if prs and prs not in ("n/a", "NA", "unknown", "absent", "none"):
        prs_gn = _clean(_fv(F, "prs_gn", w))
        prs_nu = _clean(_fv(F, "prs_nu", w))
        prs_ps = _clean(_fv(F, "prs_ps", w))
        bits = []
        if prs_ps:
            bits.append(M.t(M.PERSON, prs_ps))
        if prs_gn:
            bits.append(M.t(M.GENDER, prs_gn))
        if prs_nu:
            bits.append(M.t(M.NUMBER, prs_nu))
        suffix_desc = ", ".join(b for b in bits if b and b != "—")
        rules.append(f"Suffixe pronominal ({suffix_desc}) : pronom objet/possessif attaché au mot.")

    # Négation
    if sp == "nega" or lex in ("אל", "לא", "אין"):
        rules.append("Particule de négation (לֹא/אַל/אֵין) : nie la clause verbale ou nominale.")

    # Interrogatif (on se base uniquement sur sp/pdp pour éviter de confondre
    # l'article ה avec le ה interrogatif)
    if sp == "inrg" or pdp == "inrg":
        rules.append("Particule interrogative (ה) : transforme l'énoncé en question.")

    # Qere / Ketiv : la forme écrite (ketiv) diffère de la forme lue (qere).
    qere = _clean(_fv(F, "qere", w))
    qere_utf8 = _clean(_fv(F, "qere_utf8", w))
    if qere and qere not in ("absent", "n/a"):
        rules.append(
            "Qere/Ketiv : ketiv (écrit) « {} » lu comme qere « {} » "
            "(tradition de lecture).".format(
                F.g_word_utf8.v(w).strip(),
                (qere_utf8 or qere).strip(),
            )
        )

    return rules


# --------------------------------------------------------------------------- #
# Règles au niveau de la PHRASE
# --------------------------------------------------------------------------- #

def phrase_rules(F, L, p):
    """Analyse une phrase (BHSA 'phrase') et renvoie les règles grammaticales."""
    rules = []
    # Valeurs brutes pour la traduction (NA reste traduit par le dictionnaire).
    function_raw = _fv(F, "function", p)
    typ_raw = _fv(F, "typ", p)
    det_raw = _fv(F, "det", p)
    function = _clean(function_raw)
    typ = _clean(typ_raw)
    det = _clean(det_raw)

    rules.append(
        f"Syntagme ({M.t(M.PHRASE_TYPE, typ_raw)}) de fonction « {M.t(M.PHRASE_FUNCTION, function_raw)} »."
    )

    if function == "Time":
        rules.append("Circonstance de temps : complément circonstanciel antéposé (souvent en tête).")
    if function == "Objc":
        rules.append("Objet direct : complément d'objet du verbe, introduit par אֵת si défini.")
    if function == "Subj":
        rules.append("Sujet : argument sujet du verbe.")
    if function == "Pred":
        rules.append("Prédicat verbal : noyau verbal de la clause.")
    if function == "PreC":
        rules.append("Prédicat complétif : relation sujet-attribut (clause nominale).")
    if function == "Cmpl":
        rules.append("Complément (oblique) : complément non-objet du verbe.")
    if function == "Frnt":
        rules.append("Élément frontalisé (antéposé) : mise en relief topique/cadratif.")
    if function == "Adju":
        rules.append("Adjunct : circonstanciel libre non requis par le verbe.")
    if function == "Rela":
        rules.append("Phrase relative : introduit une proposition relative.")

    if det == "det":
        rules.append("Syntagme déterminé : présence de l'article ou d'un déterminant possessif.")
    if det == "def":
        rules.append("Syntagme défini par l'article (ה).")
    if det == "und":
        rules.append("Syntagme indéterminé : ni article ni possessif défini.")

    # Détection de l'état construit dans la phrase (chaîne d'annexion)
    words = L.d(p, "word")
    has_construct = any(_clean(_fv(F, "st", w)) == "c" for w in words)
    if has_construct and typ == "NP":
        rules.append(
            "Chaîne d'état construit (סְמִיכוּת) : un nom à l'état construit est "
            "suivi d'un nom à l'état absolu qui le détermine (génitif)."
        )

    # Objet direct avec אֵת devant un nom défini
    if typ == "PP":
        first_lexes = [_clean(_fv(F, "lex_utf8", w)) for w in words[:1]]
        if first_lexes and first_lexes[0] == "את":
            rules.append(
                "אֵת marqueur d'objet direct défini : précède le complément d'objet "
                "lorsqu'il est déterminé."
            )

    return rules


# --------------------------------------------------------------------------- #
# Règles au niveau de la CLAUSE
# --------------------------------------------------------------------------- #

def clause_rules(F, L, c):
    """Analyse une clause et renvoie les règles grammaticales structurelles."""
    rules = []
    # Valeurs brutes pour la traduction (NA est un code significatif pour rela).
    typ_raw = _fv(F, "typ", c)
    rela_raw = _fv(F, "rela", c)
    typ = _clean(typ_raw)
    rela = _clean(rela_raw)

    relation_label = M.t(M.CLAUSE_RELA, rela_raw)
    rules.append(f"Clause de type « {M.t(M.CLAUSE_TYPE, typ_raw)} », relation « {relation_label} ».")

    # Wayyiqtol (narratif séquentiel)
    if typ and typ.startswith("Way"):
        rules.append(
            "Clause wayyiqtol : succession narrative ; le waw conversif transforme "
            "l'imperfectif en récit d'événements successifs au passé."
        )
    # We-qatal (continuatif / apodose)
    if typ and (typ.startswith("WQt") or typ.startswith("WXQt") or typ in ("WxQ0", "WxQX", "WxY0", "WxYX") or typ.startswith("ZQt")):
        rules.append(
            "Clause we-qatal / continuatif (waw + perfectif) : continuation, apodose "
            "ou action coordonnée au contexte précédent."
        )
    # We-yiqtol (parataxe / coordination)
    if typ and (typ.startswith("WIm") or typ.startswith("WXIM") or typ in ("WYq0", "WYqX", "WXYq", "WxI0", "ZIm0", "ZImX", "ZYq0", "ZYqX")):
        rules.append(
            "Clause we-yiqtol : waw + imperfectif ; coordination paratactique ou "
            "volitive coordonnée."
        )
    # Clause nominale
    if typ in ("NmCl", "AjCl"):
        rules.append(
            "Clause nominale (sans verbe fini) : prédication par juxtaposition ; "
            "le prédicat (souvent un nom, un participe ou une préposition) est attribué au sujet."
        )
    # Participiale
    if typ == "Ptcp":
        rules.append(
            "Clause participiale : prédicat exprimé par un participe (souvent l'aspect "
            "progressif ou l'état)."
        )
    # Infinitive
    if typ in ("InfA", "InfC"):
        rules.append("Clause infinitive : construction au nom verbal (absolu ou construit).")
    # X initial (topicalisation / dislocation) : types où un constituant non-verbal
    # précède explicitement le verbe (BHSA marque « X » ou « x » dans le code).
    if typ and (
        typ.startswith("x")
        or (typ.startswith("X") and len(typ) > 1)
        or (typ.startswith("Wx") and typ not in ("WxI0", "WxQ0", "WxY0"))
    ):
        rules.append(
            "Clause à constituant initial (X antéposé) : un élément non-verbal "
            "(sujet, objet, circonstanciel) précède le verbe (topicalisation/dislocation)."
        )
    # Relation
    if rela and rela != "NA":
        if rela in ("ReVo", "RgRc"):
            rules.append("Subordination : clause intégrée à la clause régente (relative/complétive).")
        elif rela == "Coor":
            rules.append("Coordination : clause reliée par parataxe à la précédente.")
        elif rela in ("Subj", "Objc", "Cmpl", "Adju", "PrAd", "PreC"):
            rules.append(
                f"Clause complétive : relation syntaxique « {relation_label} » par rapport à la clause régente."
            )

    # Conjonction initiale de coordination
    words = L.d(c, "word")
    if words:
        first_cons = _clean(_fv(F, "g_cons", words[0]))
        if first_cons and first_cons.startswith("W") and _clean(_fv(F, "sp", words[0])) == "conj":
            rules.append("Waw initial : clause coordonnée à la précédente (parataxe).")

    return rules


# --------------------------------------------------------------------------- #
# Orchestration : analyse complète d'un verset
# --------------------------------------------------------------------------- #

def analyze_verse(F, L, T, verse):
    """Renvoie un dictionnaire structuré décrivant l'analyse du verset."""
    section = T.sectionFromNode(verse)
    text = T.text(verse)
    result = {
        "reference": section,
        "text": text,
        "sentences": [],
    }
    for s in L.d(verse, "sentence"):
        sent = {
            "text": T.text(s),
            "clauses": [],
        }
        for c in L.d(s, "clause"):
            clause = {
                "text": T.text(c),
                "rules": clause_rules(F, L, c),
                "phrases": [],
            }
            for p in L.d(c, "phrase"):
                phrase = {
                    "text": T.text(p),
                    "rules": phrase_rules(F, L, p),
                    "words": [],
                }
                for w in L.d(p, "word"):
                    word = {
                        "text": F.g_word_utf8.v(w),
                        "lex": _clean(_fv(F, "lex_utf8", w)) or "",
                        "gloss": _clean(_fv(F, "gloss", w)) or "",
                        "rules": word_rules(F, L, w),
                    }
                    phrase["words"].append(word)
                clause["phrases"].append(phrase)
            sent["clauses"].append(clause)
        result["sentences"].append(sent)
    return result
