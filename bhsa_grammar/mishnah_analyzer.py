"""Analyse grammaticale du texte de la Mishna.

La Mishna n'a pas d'annotation morphologique : le texte hébreu (Torat Emet,
domaine public, avec nikkud) est analysé mot à mot via la base BHSA, comme
une phrase libre (cf. phrase_analyzer.analyze_phrase).

Limites :
  - la BHSA est la Bible : les mots propres à la Mishna (araméens, termes
    techniques rabbiniques, formes post-bibliques) n'y figurent pas et
    renvoient « Aucune occurrence trouvée » ;
  - la Mishna n'est pas cantillée : le texte n'a pas de teamim, et le moteur
    les retire de toute façon (word_analyzer._normalize) s'ils apparaissent.
"""

from bhsa_grammar import analyze_phrase, format_phrase, format_phrase_json

_HEADER = "Analyse grammaticale (indicative, base BHSA)"
_LIMITS = (
    "L'analyse s'appuie sur la base BHSA (Bible) : les mots propres à la "
    "Mishna (termes post-bibliques) peuvent être absents et signalés "
    "« Aucune occurrence trouvée »."
)


def analyze_mishnah_text(F, L, hebrew_text):
    """Analyse un texte mishnaïque (une mishna) et renvoie la structure."""
    return analyze_phrase(F, L, hebrew_text)


def format_mishnah_analysis(analysis, fmt="text"):
    """Formate l'analyse d'une mishna en texte ou JSON."""
    if fmt == "json":
        return format_phrase_json(analysis)
    return format_phrase(analysis)


def mishnah_analysis_block(analysis, fmt="text"):
    """Bloc de texte prêt à afficher, avec en-tête et avertissement."""
    header = f"=== {_HEADER} ==="
    return "\n\n".join((header, format_mishnah_analysis(analysis, fmt), _LIMITS))
