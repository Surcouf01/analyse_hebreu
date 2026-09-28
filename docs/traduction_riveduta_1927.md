# Traduction italienne Riveduta Luzzi 1927 (`data/riveduta_1927.txt`)

Ce document décrit la traduction italienne de l'application : son
histoire, pourquoi elle a été préférée à la Diodati, sa source
numérique, le rendu du nom divin, et les particularités de maintenance
du fichier.

Comme les éditions chrétiennes courantes, le fichier OSIS source suit
la versification KJV (Joël et Malachie 3 chapitres, titres des psaumes
fusionnés au verset 1, Exode 7-8, Deut 28:69, Osée, etc.). Le fichier
`data/riveduta_1927.txt` a donc été renuméroté vers la versification
BHSA par `scripts/renumber_translations.py` (voir
`renumerotation_traductions.md`).

## 1. Contexte

La **Bibbia Riveduta** (« Versione Riveduta », Giovanni Luzzi,
1861-1927, public domain) est la révision protestante italienne de la
Bibbia Diodati, publiée en deux temps (NT 1916, Bible complète
1924-1927). Elle a été produite par un comité interdénominationnel
coordonné par Luzzi (pasteur valdois, professeur à la faculté
théologique de Rome) pour le compte de la Société Biblica Britannica
e Forestiera. Elle a longtemps été la version standard du
protestantisme italien, avant la « Nuova Riveduta » (1994, copyright).

## 2. Pourquoi la Riveduta plutôt que la Diodati

Deux traductions italiennes sont dans le domaine public : la **Diodati
1649** et la **Riveduta 1927**. Le choix s'est fait sur le rendu du nom
divin, seul critère discriminant pour un outil d'analyse de l'hébreu :

| | YHWH (tétragramme) | Adonaï | distingués ? |
|---|---|---|---|
| Diodati 1649 | il Signore | il Signore | non |
| **Riveduta 1927** | **l'Eterno** | **Signore** | **oui** |

La Diodati, comme la KJV avant normalisation typographique, emploie
« il Signore » pour YHWH et pour Adonaï : les deux se confondent. La
Riveduta au contraire marque explicitement la distinction (les notes
de l'éditeur, reprises par laparola.net, indiquent : *Eterno rende i
termini ebraici Jehôvâh e Yah. Signore rende il termine ebraico
Adônâi, che letteralmente significa mio Signore*).

Vérifié sur le texte du fichier :

- **Gn 15:2** (première occurrence d'Adonaï YHWH) : *E Abramo disse:
  "Signore, Eterno, che mi darai tu?…"*
- **Ps 110:1** (YHWH + Adoni) : *Salmo di Davide. L'Eterno ha detto
  al mio Signore: Siedi alla mia destra…*
- **Ex 23:17** (Adonaï YHWH) : *davanti al Signore, l'Eterno.*
- **Dt 10:17** (Adonaï des seigneurs) : *il Signor dei signori.*
- **Ex 3:14** : *Io sono quegli che sono* (même choix que Segond).

C'est le même rendu que la Segond 1910 (l'Éternel / Seigneur) : les
deux traductions se lisent en parallèle mot à mot.

## 3. Source numérique

1. **Fichier OSIS** — dépôt [seven1m/open-bibles](https://github.com/seven1m/open-bibles),
   fichier `ita-riveduta.osis.xml` (Public Domain, format OSIS) ;
   le titre interne du fichier indique « Riveduta ».
2. **Fichier du projet** — `data/riveduta_1927.txt`, extrait du
   fichier OSIS par `scripts/extract_riveduta.py` au format texte
   plat du projet :
   `nom_BHSA\tchapitre\tverset\ttexte_italien` (une ligne par verset,
   en-têtes `#`, UTF-8).

Le script d'extraction :

- parcourt les `<div type="book">` → `<chapter>` → `<verse>` OSIS ;
- mappe les identifiants OSIS vers les noms BHSA (table `_BOOK_MAP`,
   même correspondance que pour la Torres Amat) ;
- ne retient que les **39 livres protocanoniques de l'AT** (le fichier
  OSIS contient 66 livres, le NT est ignoré) ;
- normalise les reliquats d'encodage CP1252 du fichier source :
  U+0092 → apostrophe typographique `'` (33 992 occurrences) et
  U+0085 → points de suspension (70 occurrences) ;
- compacte les espaces multiples et supprime les tabulations du texte.

Usage :

```
python scripts/extract_riveduta.py <chemin ita-riveduta.osis.xml> [--out data/riveduta_1927.txt]
```

## 4. Contenu

- **39 livres** : AT protocanonique uniquement (noms BHSA).
- **23 145 versets** (couverture identique à la KJV).

## 5. Particularités du texte

- Italien littéraire du début du XXe siècle : *Iddio* (forme
  archaïque de « Dio »), *figliuoli*, *innanzi* ; le texte n'a pas
  été modernisé.
- Délimitations de versets parfois décalées par rapport à la BHSA
  (l'édition source place la fin de Gn 1:2 — *E Dio disse:* — en
  tête du verset suivant dans la BHSA). C'est inhérent à l'édition ;
  aucun remappage de verset n'est appliqué.
- Le titre du Psaume 110 est conservé dans le verset 1 (*Salmo di
  Davide.*), conformément à la convention BHSA (titre = verset 1).

## 6. Maintenance

- Fichier régénérable par `scripts/extract_riveduta.py` (voir § 3) ;
  le fichier OSIS source se trouve dans seven1m/open-bibles.
- Pour remplacer le fichier : variable d'environnement
  `TRANSLATION_IT_DATA` (chemin vers un `.txt` plat), sinon
  `data/riveduta_1927.txt`.
- Le format attendu est documenté dans la docstring de
  `bhsa_grammar/translation.py` et l'en-tête du fichier.
