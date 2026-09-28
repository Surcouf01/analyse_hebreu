"""Analyse d'une phrase hébreu libre saisie (sans référence de verset).

La phrase est segmentée par espaces/tabulations ; chaque token est analysé via
le moteur de mot isolé (``word_analyzer.analyze_word``). On ajoute ensuite des
règles contextuelles qui ne sont visibles qu'à l'échelle de l'énoncé :

  - waw initial (ו) ou coordonnant plusieurs mots ;
  - marqueurs de négation (לֹא / אַל / אֵין) qui gouvernent le verbe ;
  - jussif potentiel : yiqtol 3e personne court après אַל / לֹא / לוּ ;
  - article défini (ה) qui détermine le nom suivant ;
  - אֵת comme marqueur d'objet direct devant un syntagme défini ;
  - état construit (סְמִיכוּת) : deux noms consécutifs, le 1er à l'état construit.

Ces règles contextuelles sont indicatives : l'analyse d'une phrase libre sans
ponctuation ni contexte large reste une aide, non une exégèse.
"""

import unicodedata

from .word_analyzer import (
    analyze_word,
    _normalize,
    _strip_nikkud,
)
from . import morph_fr as M


# Marqueurs de négation (forme normalisée, sans teamim) qui gouvernent un verbe.
_NEGATION = {"לֹא", "אַל", "אֵין", "אֵינֶנּוּ", "אֵינְךָ", "אֵינֶךָ", "אֵינָהּ"}
# Particule marquant le jussif (souvent avec yiqtol 3e personne).
_JUSSIVE_MARKERS = {"אַל", "לֹא", "לוּ"}
# Préfixes qui, détachés, indiquent un rôle grammatical.
_ARTICLE_PREFIX = "ה"

# Marques de paragraphe massorétiques : samekh (setumah) et pe (petuchah).
# Ce sont des lettres, mais elles ne forment jamais un mot : elles marquent
# un changement de paragraphe dans le texte biblique et doivent être ignorées.
_PARAGRAPH_LETTERS = {"ס", "פ"}
# Maqaf (־) : la BHSA segmente les mots liés par un maqaf en deux nœuds
# « word » distincts (le maqaf vit dans le trailer) ; on fait pareil.
_MAQAF = "־"


def _tokens(phrase):
    """Découpe une phrase en tokens et normalise chacun.

    - les espaces et retours à la ligne séparent les tokens (un verset copié
      depuis le GUI peut contenir des retours à la ligne de découpage) ;
    - les tokens liés par un maqaf (־) sont séparés, comme dans la BHSA ;
    - la ponctuation de verset collée au mot (sof pasuq ׃, paseq ׀) est
      retirée par la normalisation ;
    - les marques de paragraphe (ס setumah, פ petuchah) sont ignorées.

    Renvoie (tokens, notes) : les notes décrivent les éléments ignorés.
    """
    tokens, notes = [], []
    for raw in phrase.split():
        for part in raw.split(_MAQAF):
            tok = _normalize(part)
            if not tok:
                continue
            if _strip_nikkud(tok) in _PARAGRAPH_LETTERS:
                kind = "setumah" if _strip_nikkud(tok) == "ס" else "petuchah"
                notes.append(
                    f"« {tok} » ({kind}) : marque de paragraphe massorétique, "
                    "ignorée pour l'analyse."
                )
                continue
            tokens.append(tok)
    return tokens, notes


def _is_definite(F, w):
    """Un nœud word est-il défini (article) ou déterminé ?"""
    sp = F.sp.v(w)
    if sp == "art":
        return True
    return False


def _features(F, w):
    def g(n):
        feat = getattr(F, n, None)
        return feat.v(w) if feat else None
    return {
        "sp": g("sp"),
        "pdp": g("pdp"),
        "ps": g("ps"),
        "vt": g("vt"),
        "nme": g("nme"),
        "st": g("st"),
        "prs": g("prs"),
        "gn": g("gn"),
        "nu": g("nu"),
        "lex": g("lex_utf8"),
    }


def analyze_phrase(F, L, phrase):
    """Analyse une phrase hébreu libre et renvoie une structure.

    Renvoie :
        {
            "input": "<phrase>",
            "tokens": [
                {
                    "text": "<token>",
                    "rules": [...],          # règles contextuelles
                    "word_analysis": {...},  # résultat de analyze_word
                },
                ...
            ],
            "context_rules": [...],  # règles portant sur l'ensemble de l'énoncé
        }
    """
    toks, notes = _tokens(phrase)
    result = {
        "input": phrase,
        "tokens": [],
        "context_rules": [],
        "notes": notes,
    }

    # Analyse chaque token comme mot isolé.
    token_analyses = []
    for t in toks:
        wa = analyze_word(F, L, t, limit=8)
        token_analyses.append(wa)

    # Règles contextuelles portant sur la séquence.
    context_rules = []

    # 1. Négation + verbe : repère un token négation suivi d'un verbe.
    for i, wa in enumerate(token_analyses):
        norm_tok = _normalize(toks[i])
        if norm_tok in _NEGATION:
            # Cherche un verbe dans les tokens suivants (jusqu'à 2 tokens).
            for j in range(i + 1, min(i + 3, len(token_analyses))):
                for m in token_analyses[j]["matches"]:
                    if m["features"].get("sp") == "verb":
                        context_rules.append(
                            f"Négation « {toks[i]} » gouverne le verbe « {toks[j]} » : "
                            f"clause négative ({norm_tok})."
                        )
                        # Jussif potentiel : yiqtol 3e pers court après négation.
                        if (
                            m["features"].get("vt") == "impf"
                            and m["features"].get("ps") == "p3"
                        ):
                            context_rules.append(
                                f"Jussif potentiel : « {toks[j]} » est un yiqtol 3e "
                                f"personne court sous négation « {toks[i]} » (forme "
                                f"volitive négative : « qu'il ne fasse pas »)."
                            )
                        break
                else:
                    continue
                break

    # 2. Article ה suivi d'un nom → syntagme défini.
    for i, wa in enumerate(token_analyses):
        norm_tok = _normalize(toks[i])
        if norm_tok == "ה" or norm_tok.startswith("הַ"):
            if i + 1 < len(token_analyses):
                nxt = token_analyses[i + 1]
                for m in nxt["matches"]:
                    if m["features"].get("sp") in ("subs", "nmpr"):
                        context_rules.append(
                            f"Article défini « {toks[i]} » détermine le nom « {toks[i+1]} » : "
                            f"syntagme nominal défini."
                        )
                        break

    # 3. État construit : deux noms consécutifs, le 1er à l'état construit.
    for i, wa in enumerate(token_analyses):
        first_construct = False
        for m in wa["matches"]:
            if m["features"].get("sp") in ("subs", "nmpr") and m["features"].get("st") == "c":
                first_construct = True
                break
        if first_construct and i + 1 < len(token_analyses):
            nxt = token_analyses[i + 1]
            for m in nxt["matches"]:
                if m["features"].get("sp") in ("subs", "nmpr"):
                    context_rules.append(
                        f"État construit (סְמִיכוּת) : « {toks[i]} » (état construit) "
                        f"est déterminé par « {toks[i+1]} » (état absolu) — chaîne de "
                        f"génitif/annexion."
                    )
                    break

    # 4. Waw conjonctif : token commençant par ו préfixé.
    for i, wa in enumerate(token_analyses):
        norm_tok = _normalize(toks[i])
        if norm_tok.startswith("וְ") or norm_tok.startswith("וַ") or norm_tok.startswith("וָ"):
            context_rules.append(
                f"Waw conjonctif en « {toks[i]} » : coordonne/relie au token précédent."
            )

    # 5. אֵת marqueur d'objet direct devant un nom défini.
    for i, wa in enumerate(token_analyses):
        norm_tok = _normalize(toks[i])
        if norm_tok == "אֵת" and i + 1 < len(token_analyses):
            nxt = token_analyses[i + 1]
            for m in nxt["matches"]:
                if m["features"].get("sp") in ("subs", "nmpr"):
                    context_rules.append(
                        f"« {toks[i]} » (אֵת) marque l'objet direct défini « {toks[i+1]} »."
                    )
                    break

    # Construit la liste des tokens avec leurs règles propres + références.
    for i, wa in enumerate(token_analyses):
        token_rules = []
        if not wa["found"]:
            token_rules.append(
                "Aucune occurrence trouvée dans la base BHSA (vérifier l'orthographe/nikkud)."
            )
        else:
            # On prend les règles de la 1re analyse (la plus fréquente).
            if wa["matches"]:
                token_rules.extend(wa["matches"][0]["rules"])
                if len(wa["matches"]) > 1:
                    token_rules.append(
                        f"Analyse ambiguë : {len(wa['matches'])} lectures possibles "
                        f"(voir --format json pour le détail)."
                    )
        result["tokens"].append({
            "text": toks[i],
            "rules": token_rules,
            "word_analysis": wa,
        })

    # Traduction indicative du versement : gloss français (lemme) du meilleur
    # match de chaque token, dans l'ordre des tokens.
    glosses = []
    for wa in token_analyses:
        if wa["found"] and wa["matches"]:
            m = wa["matches"][0]
            g = m.get("gloss_fr") or m.get("gloss") or ""
            glosses.append(g if g else "—")
        else:
            glosses.append("—")
    result["translation_fr"] = " ".join(glosses)

    result["context_rules"] = context_rules
    return result
