# analyse_hebreu — Analyseur grammatical de l'hébreu biblique

Programme Python qui analyse n'importe quel verset de la Bible hébraïque et
sort, pour chaque construction, **les règles de grammaire appliquées** :
partie du discours, genre/nombre/personne/état, binyan et temps verbal, fonction
des syntagmes, type et relation des clauses, état construit (סְמִיכוּת),
wayyiqtol, waw conversif, objet direct marqué par אֵת, suffixes pronominaux,
clauses nominales/participiales/infinitives, topicalisation, etc.

L'analyse s'appuie sur la base morphologique et syntaxique **BHSA** de l'ETCBC
(Eep Talstra Centre for Bible and Computer), chargée via **Text-Fabric**. La base
contient l'annotation de chacun des ~426 000 mots de la Bible hébraïque, organisés
en mots, syntagmes (phrase), clauses, phrases et versets.

## Installation

```bash
pip install text-fabric
# Optionnel (chargement en ligne uniquement) :
pip install "text-fabric[github]"
```

### Données BHSA

Le programme cherche automatiquement la base, dans cet ordre :

1. Variable d'environnement `BHSA_DATA` pointant vers le dossier contenant les
   features `.tf` (`otype.tf`, `oslots.tf`, `otext.tf`, etc.) — par exemple
   `…/bhsa/tf/c`.
2. Un sous-dossier `bhsa_data/` à côté du paquet.
3. Un dépôt cloné en local à `bhsa_repo/tf/c` (obtenu ci-dessous).
4. Le chargement en ligne `tf.app.use('bhsa')` (nécessite réseau + quota GitHub).

**Méthode recommandée (clone local, hors ligne) :**

```bash
git clone --branch data2021 https://github.com/ETCBC/bhsa.git bhsa_repo
```

Le dossier `bhsa_repo/tf/c` est alors détecté automatiquement depuis le
répertoire de travail courant ou depuis `/workspace`.

## Utilisation

### En ligne de commande

Analyse d'un verset complet :
```bash
python analyse_hebreu.py "Genèse 1:1"
python analyse_hebreu.py "Gen 1:1" --no-words        # sans détail mot à mot
python analyse_hebreu.py "Genesis 1:1" --format json # sortie JSON
python analyse_hebreu.py "Psaume 23:1" --format summary
python analyse_hebreu.py --list-books                # livres disponibles
```

Analyse d'un mot isolé (avec nikkud, sans teamim) :
```bash
python analyse_hebreu.py --word "בָּרָא"           # verbe « créer » (qatal qal)
python analyse_hebreu.py --word "בְּרֵאשִׁית"        # ב préfixe + nom « commencement »
python analyse_hebreu.py --word "וַיֹּאמֶר"         # waw + wayyiqtol « il dit »
python analyse_hebreu.py --word "אֶעֱשֶׂה"          # cohortif (1re personne volitive)
python analyse_hebreu.py --word --file mots.txt     # un mot par ligne
python analyse_hebreu.py --word "בָּרָא" --format json
```

Le mode `--word` cherche le mot dans toutes les occurrences de la Bible hébraïque
et renvoie les analyses morphologiques distinctes trouvées (lemme, partie du
discours, genre/nombre/personne/état, binyan, temps verbal, suffixe), avec le
nombre d'occurrences et un verset exemple. Les préfixes prépositionnels/
conjonctifs (ב כ ל מ ו ה ש et leurs combinaisons) sont détachés automatiquement.
Le **cohortif** (1re personne, préfixe א + voyelle longue) est reconnu.

Analyse d'une phrase hébreu libre (sans référence de verset) :
```bash
python analyse_hebreu.py --phrase "וַיֹּאמֶר אֱלֹהִים יְהִי אוֹר"
python analyse_hebreu.py --phrase "לֹא יִהְיֶה לְךָ"   # négation + jussif potentiel
python analyse_hebreu.py --phrase --file phrases.txt  # une phrase par ligne
python analyse_hebreu.py --phrase "בְּרֵאשִׁית בָּרָא" --format json
```

Le mode `--phrase` découpe la phrase par espaces, analyse chaque token comme un
mot isolé, puis ajoute des **règles contextuelles** : waw conjonctif, négation
gouvernant un verbe, **jussif potentiel** (yiqtol 3e pers court sous לֹא/אַל),
article défini déterminant le nom suivant, état construit (סְמִיכוּת) entre deux
noms consécutifs, marqueur d'objet direct אֵת.

Formats de sortie :
- `text` (défaut) : arbre hiérarchique phrase → clause → syntagme → mot,
  chaque niveau suivi de ses règles (↳).
- `json` : structure `{"reference", "text", "sentences": [...]}` exploitable
  par un autre programme.
- `summary` : liste dédoublonnée des règles détectées par niveau (clause, phrase, word).

### Références acceptées

Le résolveur de référence accepte français, abrégés français, anglais, latin et
hébreu : `Genèse 1:1`, `Gn 1:1`, `Gen 1:1`, `Genesis 1:1`, `בראשית 1:1`,
`1 Rois 19:3`, `Psaume 23:1`, `Cantique 1:2`, etc. Séparateurs `:`, `.` ou `,`.

### En bibliothèque

```python
from bhsa_grammar import (
    load_corpus, analyze_verse_by_reference, format_text
)

api = load_corpus()                       # charge la base BHSA
analyse = analyze_verse_by_reference(api, "Genèse 1:1")
print(format_text(analyse))
```

`analyze_verse_by_reference` renvoie un dictionnaire structuré :
```python
{
    "reference": ("Genesis", 1, 1),
    "text": "בְּרֵאשִׁית ...",
    "sentences": [
        {
            "text": "...",
            "clauses": [
                {
                    "text": "...",
                    "rules": ["Clause de type « ... », relation « ... ».", ...],
                    "phrases": [
                        {
                            "text": "...",
                            "rules": ["Syntagme (...) de fonction « ... ».", ...],
                            "words": [
                                {"text": "בְּ", "lex": "ב", "rules": ["Préposition ..."]},
                                ...
                            ],
                        }
                    ],
                }
            ],
        }
    ],
}
```

## Structure du projet

```
analyse_hebreu.py        # CLI (mode verset, mot, phrase)
bhsa_grammar/
  __init__.py            # API publique (load_corpus, analyze_*, format_*)
  loader.py              # localisation + chargement de la base BHSA (Text-Fabric)
  reference.py           # résolution de référence (alias FR/EN/Latin/Hébreu) -> nœud verset
  morph_fr.py            # dictionnaires de traduction des codes BHSA en français
  rules.py               # moteur de règles grammaticales (mot, syntagme, clause) + cohortif + qere/ketiv
  word_analyzer.py       # analyse d'un mot isolé (normalisation, préfixes, recherche)
  phrase_analyzer.py     # analyse d'une phrase libre (segmentation + règles contextuelles + jussif)
  report.py             # formatage text / json / summary (verset, mot, phrase)
```

## Règles grammaticales détectées

**Niveau mot** — partie du discours (article, substantif, nom propre, verbe,
préposition, pronom, négation, interrogatif), genre/nombre/personne, état
(absolu/construit/emphatique), binyan (les 7 de base : qal/paal, nifal, piel,
pual, hitpael, hifil, hofal ; plus les rares hsht, nit, shaf, poal, poel, htpa,
htpe, htpo, hotp), temps verbal (qatal, yiqtol, wayyiqtol, impératif, infinitif,
participe), suffixe pronominal (personne/genre/nombre), waw conjonctif, article défini.

**Niveau syntagme** — type (nominal, prépositionnel, verbal…) et fonction
(sujet, objet, prédicat, complément, circonstance de temps, frontalisé…),
détermination (défini/indéterminé), chaîne d'état construit (סְמִיכוּת),
marqueur d'objet direct אֵת.

**Niveau clause** — type (wayyiqtol, we-qatal, we-yiqtol, nominale,
participiale, infinitive, X-initial…) et relation (principale, coordonnée,
relative, complétive…), waw initial de coordination, topicalisation.

## Règles grammaticales détectées (extension)

Outre les règles de base (voir ci-dessus), les modes `--word` et `--phrase`
détectent :

- **Cohortif** : yiqtol de 1re personne marqué par le préfixe א + voyelle longue
  (« faisons… », « que je… »).
- **Jussif potentiel** (mode phrase) : yiqtol 3e personne court sous négation
  (לֹא / אַל) — forme volitive négative (« qu'il ne fasse pas »).
- **Qere/Ketiv** : quand la forme écrite (ketiv) diffère de la forme lue (qere),
  le programme signale les deux traditions.
- **Règles contextuelles** (mode phrase) : waw conjonctif, négation + verbe,
  article défini + nom, état construit entre deux noms, marqueur d'objet אֵת.
- **Traduction des mots (gloss)** : chaque mot hébreu est accompagné de sa
  traduction courte. Le programme privilégie la **traduction française**,
  issue du lexique Strong hébreu-français de Bible Strong (base interlinéaire
  STEP, CC BY 4.0), alignée sur les lemmes BHSA par les consonnes du lemme
  (~8 000 lemmes couverts, ≈98 % des occurrences). Les lemmes non couverts
  retombent sur le gloss anglais de la BHSA. En mode verset, la traduction
  s'affiche sous la forme `« Dieu »` après le lemme ; en mode mot, des lignes
  `Traduction (fr)` / `Traduction (en)` ; en mode phrase, dans les lectures
  possibles.

## Noms de livres

La base BHSA utilise des noms de livres en latin (ex. `Judices`, `Numeri`,
`Reges_I`, `Jesaia`, `Psalmi`). Le programme accepte indifféremment les
noms français (`Juges`, `Nombres`, `1 Rois`), anglais (`Judges`, `Numbers`,
`Kings_I`) ou latins (`Judices`, `Numeri`, `Reges_I`), ainsi que les
abreviations (`Jg`, `Nb`, `1R`) et les noms hébreux (`שופטים`). Tous sont
automatiquement normalisés vers le nom BHSA attendu.

## Limites

L'analyse repose sur l'annotation morphosyntaxique de la BHSA ; les « règles »
décrites sont des interprétations pédagogiques des features de la base, non une
analyse exégétique exhaustive. Les cas rares (araméen, formes defectives) peu-
vent nécessiter un complément manuel.

Pour le mode `--word` : la recherche porte sur les formes effectivement
attestées dans la Bible. Un mot qui n'existe pas tel quel dans le texte (forme
inédite, variante orthographique) ne sera pas trouvé. La base BHSA stocke les
préfixes prépositionnels comme des mots séparés, donc le détachement automatique
retrouve le radical ; mais en cas d'homographie (ex. בָּרָא = substantif araméen
« fils » ou verbe hébreu « il créa »), toutes les analyses possibles sont
renvoyées, à charge de l'utilisateur de choisir selon le contexte.

Pour le mode `--phrase` : la segmentation par espaces suppose que l'utilisateur
sépare les mots. L'analyse est indicative (pas de parsing syntaxique complet) ;
le jussif est marqué « potentiel » car il est morphologiquement ambigu avec le
yiqtol simple sans contexte large.
