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

### En interface graphique

Une fenêtre graphique (Tkinter) reprend chacune des fonctions du CLI. Elle se
lance par :

```bash
python gui_hebreu.py
```

Pré-requis : `tkinter` (inclus dans la plupart des distributions Python ; sur
Debian/Ubuntu : `sudo apt install python3-tk`).

L'interface comporte quatre onglets :

- **Livre** : sélection d'abord du **corpus** — **Bible (BHSA)** ou
  **Mishna (Sefaria)** — puis du livre, du chapitre et du verset au moyen de
  listes déroulantes liées et remplies selon le contexte. Pour la Bible,
  les livres sont présentés **dans l'ordre canonique de la Bible
  hébraïque** (Torah en tête : Genèse, Exode, Lévitique, Nombres,
  Deutéronome, …) et les listes sont **bornées aux limites réelles** de la
  base BHSA. Formats disponibles : texte, synthèse, JSON ; option
  « masquer le détail mot à mot ». Des **traductions française et anglaise**
  du verset (Louis Segond 1910, King James Version 1611, toutes deux
  domaine public) sont affichées en tête du résultat ; elles sont
  activables individuellement par cases à cocher.

  Pour la **Mishna**, les six *sedarim* (Zeraim, Moed, Nashim, Nezikin,
  Kodashim, Tahorot) et leurs 63 traités sont listés dans l'ordre canonique
  (structure issue de l'API Sefaria, intégrée au projet : aucun réseau
  n'est nécessaire pour les listes). L'affichage d'une mishna donne le
  **texte hébreu** (« Torat Emet 357 », domaine public) et, quand le traité
  est couvert, la **traduction française** de **Moïse Schwab** (« Le Talmud
  de Jérusalem, traduit par Moise Schwab, 1878-1890 », domaine public — 38
  traités sur 63 : Zeraim, Moed, Nashim et la plupart de Nezikin ; les
  ordres Kodashim et Tahorot ne sont pas couverts). Les options d'analyse
  grammaticale (formats, traductions Segond/KJV) sont grisées dans ce mode,
  car elles ne s'appliquent pas à la Mishna.
- **Mot** : analyse d'un mot hébreu isolé, saisi à l'aide d'un **clavier
  hébreu virtuel** (consonnes + points-voyelles/nikkud + daguesh, en UTF-8).
  Un clavier physique en hébreu reste utilisable : la saisie se fait toujours
  en UTF-8. Formats : texte ou JSON.
- **Phrase** : analyse d'une phrase hébreu libre, saisie via le même clavier
  hébreu virtuel (UTF-8). Formats : texte ou JSON.
- **Binyanim** : conjugaison d'un verbe hébreu (mot conjugué ou racine
  trilitaire) dans les 7 binyanim, pour toutes les personnes. Le résultat est
  présenté en **sous-onglets, un par binyan**, dont le libellé combine le nom
  français et le nom hébreu (ex. « qal (paal) · פָּעַל ») ; un marqueur ✓
  signale le binyan attesté dans la BHSA pour la forme saisie. L'onglet
  « Verbe » affiche la racine, le lemme, la traduction et la **catégorie du
  verbe** (fort, ou faible avec sa classe : lamed-he, creux, pe-nun, etc.).
  Le GUI parse la sortie marquée du CLI (`###BINYAN|...###`). Formats :
  texte ou JSON.

La base BHSA est chargée en arrière-plan au démarrage ; les boutons restent
inactifs jusqu'à la fin du chargement. Les analyses s'exécutent dans des
threads séparés afin de ne pas figer la fenêtre.

#### Personnalisation de l'affichage

Les polices (saisie de l'hébreu et zone de résultat) sont paramétrables via
le fichier **`gui.properties`**, placé à côté de `gui_hebreu.py`. Les tailles
sont exprimées en points : modifier les valeurs et relancer `gui_hebreu.py`
 Suffit ; aucun changement de code n'est nécessaire.

```properties
font.input.family  = DejaVu Sans
font.input.size     = 14
font.output.family  = DejaVu Sans Mono
font.output.size    = 20
```

La zone de résultat dispose d'un **ascenseur vertical et horizontal** : les
longues lignes ne sont pas coupées (`wrap=none`) et peuvent être défiler
latéralement si elles dépassent du cadre.

#### Traductions française et anglaise

L'onglet **Livre** (mode Bible) affiche, en tête du résultat, une ou deux
traductions du verset analysé, toutes deux **domaine public** :

- **Louis Segond 1910** (français) — fichier `data/louis_segond_1910.txt` ;
- **King James Version 1611** (anglais) — fichier `data/kjv_1611.txt`.

Les deux fichiers sont fournis avec le projet (un verset par ligne, indexé
par nom BHSA / chapitre / verset). Dans le GUI, chaque traduction est
activable individuellement par une case à cocher. En ligne de commande,
options `--translation` (français) et `--translation-en` (anglais).

Le chargement est automatique si les fichiers sont présents ; s'ils sont
absents, l'analyse grammaticale fonctionne normalement (sans traduction). On
peut forcer un autre chemin via les variables d'environnement `TRANSLATION_DATA`
(français) et `TRANSLATION_EN_DATA` (anglais).

> **Note sur la numérotation** : la numérotation des versets en Segond 1910
> et en KJV diffère parfois de celle de la base BHSA (hébraïque). Par exemple
> *1 Rois 22* s'arrête à 22:53 en Segond/KJV mais à 22:54 dans la BHSA. Dans
> ce cas, le programme affiche un message indiquant que le verset est absent
> de la traduction.


### En ligne de commande

Analyse d'un verset complet :
```bash
python analyse_hebreu.py "Genèse 1:1"
python analyse_hebreu.py "Gen 1:1" --no-words        # sans détail mot à mot
python analyse_hebreu.py "Genesis 1:1" --format json # sortie JSON
python analyse_hebreu.py "Genèse 1:1" --translation # + traduction Louis Segond
python analyse_hebreu.py "Genèse 1:1" --translation --translation-en # + KJV anglaise
python analyse_hebreu.py "Psaume 23:1" --format summary
python analyse_hebreu.py --list-books                # livres de la Bible
```

Affichage d'une mishna (texte via l'API Sefaria, sans analyse BHSA) :
```bash
python analyse_hebreu.py --mishna "Bérakhot 1:1"     # hébreu + trad. Schwab
python analyse_hebreu.py --mishna "Berakhot 2:5"     # nom Sefaria accepté
python analyse_hebreu.py --mishna "Avot 1:3"          # nom français court
python analyse_hebreu.py --mishna --list-books        # les 63 traités
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

Conjugaison d'un verbe dans tous les binyanim :
```bash
python analyse_hebreu.py --binyanim "שָׁמַר"        # verbe fort, mot conjugué
python analyse_hebreu.py --binyanim "שמר"           # racine trilitaire nue
python analyse_hebreu.py --binyanim "בָּנָה"          # verbe lamed-he (faible)
python analyse_hebreu.py --binyanim --file verbes.txt  # un verbe par ligne
python analyse_hebreu.py --binyanim "קום" --format json
```

Le mode `--binyanim` identifie le verbe (lemme BHSA ou racine), détecte sa
catégorie (verbe **fort** ou **faible** : pe-alef/guttural/nun/yod,
ayin-guttural, creux, double, lamed-he/alef/guttural), puis génère la
conjugaison complète dans les **7 binyanim** (qal, nifal, piel, pual,
hitpael, hifil, hofal) : parfait, imparfait et impératif pour toutes les
personnes (1re/2e/3e, masculin/féminin, singulier/pluriel), plus infinitifs
et participes. Les gabarits vocaliques sont extraits des formes dominantes
attestées dans la base BHSA (`bhsa_grammar/binyan_templates.json`, généré
par `scripts/extract_binyan_templates.py`).

Chaque en-tête de binyan de la sortie texte est marqué pour être
identifiable/parsable par le GUI :
`###BINYAN|<code>|<nom fr>|<nom hébreu>|<attesté>###`, de même que l'en-tête
de verbe `###VERB|...###` et la catégorie de verbe faible `###WEAK|...###`.

La traduction du verbe par binyan (français + anglais) vient du lexique
`bhsa_grammar/binyan_senses_fr_en.json` : sens anglais extraits du **BDB**
(Brown-Driver-Briggs, domaine public) par `scripts/extract_binyan_senses.py`,
traductions françaises enrichies progressivement. La curation FR s'appuie
sur les occurrences réelles de chaque racine mises en regard de la **Bible
du Rabbinat 1899** (domaine public), récupérée via l'API Sefaria
(`bhsa_grammar/sefaria_client.py`). Sefaria ne fournit pas de lexique
hébreu→français : les versets français servent de contexte d'occurrence,
la traduction des sens reste une curation manuelle.

Workflow d'enrichissement (procédure incrémentale) :

```bash
# 1. Rapport de curation : pour les N racines sans FR les plus fréquentes,
#    sens BDB anglais + versets français d'occurrence, par binyan
#    (indicateur de progression : [i/n] racine (translit) — binyan).
python scripts/enrich_binyan_senses_fr.py --limit 40 --report rapport.txt

# 2. Traduction manuelle : rédiger un fichier de curation JSON
#    {racine: {binyan: [fr, en]}} — cf. docstring de merge_binyan_senses_fr.

# 3. Fusion dans le lexique (jamais d'écrasement du FR existant).
python scripts/merge_binyan_senses_fr.py curation.json            # applique
python scripts/merge_binyan_senses_fr.py curation.json --dry-run  # simule
python scripts/merge_binyan_senses_fr.py curation.json --check   # valide
```

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
analyse_hebreu.py        # CLI (mode verset/livre, mot, phrase, binyanim, mishna)
gui_hebreu.py           # interface graphique Tkinter (mêmes fonctions que le CLI)
gui.properties         # polices/tailles d'affichage du GUI (points)
data/
  louis_segond_1910.txt  # traduction française Louis Segond 1910 (domaine public)
  kjv_1611.txt          # traduction anglaise King James Version 1611 (domaine public)
bhsa_grammar/
  __init__.py            # API publique (load_corpus, analyze_*, format_*)
  loader.py              # localisation + chargement de la base BHSA (Text-Fabric)
  reference.py           # résolution de référence (alias FR/EN/Latin/Hébreu) -> nœud verset
  morph_fr.py            # dictionnaires de traduction des codes BHSA en français
  rules.py               # moteur de règles grammaticales (mot, syntagme, clause) + cohortif + qere/ketiv
  word_analyzer.py       # analyse d'un mot isolé (normalisation, préfixes, recherche)
  phrase_analyzer.py     # analyse d'une phrase libre (segmentation + règles contextuelles + jussif)
  binyan_diag.py         # diagnostics heuristiques du binyan d'une forme conjuguée
  binyan_gen.py          # conjugaison dans les 7 binyanim (mode --binyanim) + verbes faibles
  binyan_templates.json  # gabarits vocaliques extraits de la BHSA (par catégorie de verbe)
  binyan_senses_fr_en.json  # sens par (racine, binyan) — BDB (EN, domaine public) + curation FR
  sefaria_client.py     # client de l'API Sefaria (Rabbinat 1899, Mishna : Torat Emet
                        # + Schwab, domaine public)
  mishnah_catalog.py    # catalogue statique de la Mishna : 63 traités, sedarim,
                        # structure chapitres/mishnayot (source API Sefaria)
  report.py             # formatage text / json / summary (verset, mot, phrase)
scripts/
  extract_binyan_templates.py  # régénère binyan_templates.json depuis la BHSA
  extract_binyan_senses.py     # extrait les sens par binyan du lexique BDB (CSV)
  enrich_binyan_senses_fr.py   # rapport de curation FR : occurrences BHSA × versets
                               # Rabbinat 1899 (Sefaria) pour les racines sans FR
  merge_binyan_senses_fr.py    # fusionne une curation JSON dans le lexique
                               # (sans écraser le FR existant)
tests/
  test_binyanim.py       # non-régression du mode binyanim (formes vs BHSA)
```

## Règles grammaticales détectées

**Niveau mot** — partie du discours (article, substantif, nom propre, verbe,
préposition, pronom, négation, interrogatif), genre/nombre/personne, état
(absolu/construit/emphatique), binyan (les 7 de base : qal/paal, nifal, piel,
pual, hitpael, hifil, hofal ; plus les rares hsht, nit, shaf, poal, poel, htpa,
htpe, htpo, hotp), temps verbal (qatal, yiqtol, wayyiqtol, impératif, infinitif,
participe), suffixe pronominal (personne/genre/nombre), waw conjonctif, article défini.

**Diagnostics de binyan** — pour chaque verbe conjugué, des règles heuristiques
(`[binyan] ...`) expliquent comment on reconnaît le binyan et pourquoi ce n'est
pas un autre : marqueur de stem consonantique (`vbs` : H=hifil/hofal, HT=hitpael,
N=nifal, absent=qal/piel/pual, C=shafel…), préformative visible (ה, נ, ת), et
disambiguïsation par le schéma vocalique (hifil vs hofal : hireq/segol vs
shureq/qamats ; qal vs piel vs pual : qamats vs hireq vs shureq).

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
  retombent sur le gloss anglais de la BHSA. En mode livre (Bible), la traduction
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
