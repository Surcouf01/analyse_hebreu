"""Chargement de la base morphologique BHSA (ETCBC) via Text-Fabric.

Le module localise automatiquement le jeu de features BHSA. Priorité :
  1. variable d'environnement ``BHSA_DATA`` (chemin vers le dossier contenant
     les features .tf, ex. ``.../bhsa/tf/c``) ;
  2. un sous-dossier ``bhsa_data`` à côté du paquet ;
  3. un dépôt git cloné à ``../bhsa_repo/tf/c`` (clone de ETCBC/bhsa branche
     ``data2021``) ;
  4. le chargement en ligne via ``tf.app.use('bhsa', ...)`` (nécessite réseau et
     un quota GitHub suffisant).

Si aucune source n'est trouvée, une exception ``DataNotFoundError`` est levée
avec un message d'aide à l'installation.
"""

import os
import sys

from tf.fabric import Fabric


class DataNotFoundError(RuntimeError):
    """Levée quand la base BHSA est introuvable."""


# Features requises pour l'analyse grammaticale.
FEATURES = (
    "g_word_utf8 g_cons g_cons_utf8 g_lex_utf8 lex lex_utf8 sp ls vt vs gn nu ps "
    "st pdp prs prs_gn prs_nu prs_ps pfm nme vbe vbs uvf function typ det rela "
    "kind domain pargr gloss language qere qere_utf8 qere_trailer_utf8 "
    "book chapter verse otype oslots otext"
).split()


def _candidate_paths():
    """Renvoie la liste des chemins candidats pour le dossier de features."""
    paths = []
    env = os.environ.get("BHSA_DATA")
    if env:
        paths.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    paths.append(os.path.join(here, "bhsa_data"))
    paths.append(os.path.join(here, "bhsa_data", "tf", "c"))
    # Clone standard du tutoriel : /workspace/bhsa_repo/tf/c
    paths.append("/workspace/bhsa_repo/tf/c")
    # Relatif au répertoire de travail courant
    paths.append(os.path.join(os.getcwd(), "bhsa_repo", "tf", "c"))
    paths.append(os.path.join(os.getcwd(), "bhsa_data", "tf", "c"))
    return paths


def _is_tf_dir(path):
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "otype.tf"))


def load_corpus():
    """Charge et renvoie l'API Text-Fabric (F, L, T, E).

    Essaie d'abord le chargement local ; sinon tente le téléchargement en ligne
    via ``tf.app.use('bhsa')``. Lève ``DataNotFoundError`` en cas d'échec.
    """
    # 1. Chargement local
    for path in _candidate_paths():
        if _is_tf_dir(path):
            TF = Fabric(path)
            TF.load(FEATURES, silent=True)
            api = TF.api
            if api.F.otype.maxNode:
                return api
            # Sinon, continue à chercher

    # 2. Chargement en ligne (réseau requis)
    try:
        from tf.app import use

        A = use("bhsa", hoist=globals())
        if "F" in globals() and F.otype.maxNode:
            return _OnlineAPI(globals())
    except Exception as exc:  # noqa: BLE001
        online_error = str(exc)
    else:
        online_error = None

    raise DataNotFoundError(
        "Impossible de localiser la base BHSA. Options :\n"
        "  1. Cloner le dépôt : git clone --branch data2021 "
        "https://github.com/ETCBC/bhsa.git bhsa_repo\n"
        "     puis utiliser le dossier bhsa_repo/tf/c.\n"
        "  2. Définir la variable d'environnement BHSA_DATA vers le dossier\n"
        "     contenant otype.tf, oslots.tf, otext.tf et les features .tf.\n"
        "  3. Utiliser tf.app.use('bhsa') en ligne (réseau + quota GitHub).\n"
        f"Erreur en ligne : {online_error}"
    )


class _OnlineAPI:
    """Adaptateur minimal pour uniformiser l'API locale et en ligne."""

    def __init__(self, ns):
        self.F = ns["F"]
        self.L = ns["L"]
        self.T = ns["T"]
        self.E = ns.get("E")
