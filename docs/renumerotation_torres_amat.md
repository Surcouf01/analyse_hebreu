# Renumérotation de la traduction espagnole Torres Amat (Vulgate → massorétique)

Ce document décrit la conversion de versification appliquée à
`data/torres_amat_1823.txt`, la traduction espagnole de l'application.
Il documente les tables utilisées par `scripts/extract_torres_amat.py`
et se veut la référence pour toute maintenance future.

## 1. Contexte

La **Biblia Torres Amat** (Félix Torres Amat, 1772-1847, dominio
público, publiée 1823-1825) traduit la **Vulgate latine**, pas le texte
massorétique. Sa numérotation des versets suit donc la versification
Vulgate, qui diffère de la numérotation massorétique (BHS, celle de la
base BHSA) sur plusieurs points :

- versets placés **en tête du chapitre suivant** (le fameux « 29:1 »
  de Deut 29 Vulgate = 28:69 massorétique) ;
- **fusions de versets** (Psaumes 9/10, 113-116, 145-147 ; Joël,
  Malachie comptent un chapitre de plus) ;
- **scissions inverses** (quelques versets massorétiques portés par le
  verset Vulgate suivant) ;
- **additions deutérocanoniques** (Daniel 3, 13-14 ; Esther grec).

Le texte numérique utilisé est le module SWORD **TorresAmat** du projet
OmarGonD/biblia-elim (reconstruction OCR de l'édition de 1882,
GPL-2.0-or-later ; le texte de Torres Amat lui-même est dominio
público). Ce module présente en outre des **défauts propres à l'OCR**
(doublons, index collés, versets perdus, versets mal numérotés) qui
sont gérés par les mêmes tables.

L'objectif : que le fichier final soit **indexé selon la numérotation
BHSA** (nom de livre BHSA, chapitre, verset), afin que le verset affiché
par l'application pour `Deut 4:10` soit le bon texte espagnol.

## 2. Méthode

Chaque règle a été **calibrée verset par verset contre la base BHSA
locale** (`bhsa_repo/tf`, feature `text-orig-full`) : pour chaque
chapitre divergent, les textes espagnols et hébreux ont été comparés
mot à mot (noms propres, chiffres, mots-clés caractéristiques) afin de
déterminer le décalage exact. Deux vérifications automatiques couvrent
le résultat final :

- **bornes** : zéro référence du fichier final n'est hors des bornes
  de la BHSA (23213 versets de référence) ;
- **couverture** : 21 852 versets couverts (94,1 %), les manquants
  étant les lacunes de l'OCR source (laissées « en creux » : la ligne
  n'existe pas, l'application affiche « verset absent de la
  traduction »).

La conversion distingue :

1. **décalages** (`_VERSE_SHIFTS` dans le script) : la référence
   Vulgate `(livre, chapitre, verset)` devient une référence BHSA
   `(livre, chapitre, verset + delta)` ;
2. **Psaumes** (`_PSALMS_MAP`) : renumérotation complète des 150
   psaumes (voir § 5) ;
3. **exclusions** (`_EXCLUDE`) : versets Vulgate sans équivalent
   massorétique (additions) ou corrompus par l'OCR ;
4. **troncatures ciblées** (`_TRIM`) : additions collées après le
   texte canonique, coupées au marqueur.

## 3. Cas général : livres et chapitres identiques

Pour la grande majorité des versets (environ 95 % des versets
convertis), la référence est inchangée : mêmes livres, mêmes chapitres,
mêmes numéros de versets. Les 39 livres protocanoniques de l'AT sont
mappés du nom OSIS SWORD vers le nom BHSA :

| OSIS (SWORD) | BHSA | OSIS (SWORD) | BHSA |
|---|---|---|---|
| Gen | Genesis | Josh | Josua |
| Exod | Exodus | Judg | Judices |
| Lev | Leviticus | Ruth | Ruth |
| Num | Numeri | 1Sam / 2Sam | Samuel_I / Samuel_II |
| Deut | Deuteronomium | 1Kgs / 2Kgs | Reges_I / Reges_II |
| 1Chr / 2Chr | Chronica_I / II | Ezra | Esra |
| Neh | Nehemia | Esth | Esther |
| Job | Iob | Ps | Psalmi |
| Prov | Proverbia | Eccl | Ecclesiastes |
| Song | Canticum | Isa | Jesaia |
| Jer | Jeremia | Lam | Threni |
| Ezek | Ezechiel | Dan | Daniel |
| Hos | Hosea | Joel | Joel |
| Amos | Amos | Obad | Obadia |
| Jonah | Jona | Mic | Micha |
| Nah | Nahum | Hab | Habakuk |
| Zeph | Zephania | Hag | Haggai |
| Zech | Sacharia | Mal | Maleachi |

Les livres deutérocanoniques du module (Tob, Jdt, Wis, Sir, 1Macc,
2Macc, Bar, etc.) sont ignorés.

## 4. Décalages de versets et de chapitres

Notation : `TA x:y → TM a:b` signifie que le verset x:y du fichier
source (Torres Amat, versification Vulgate) est réécrit à la référence
a:b du fichier final (numérotation massorétique BHSA). Les règles
s'appliquent à des **intervalles** de versets ; les versets hors
intervalle suivent la règle suivante ou l'identité.

### 4.1 Verset Vulgate placé en tête du chapitre suivant

Motif classique de la Vulgate : le dernier verset d'un chapitre (en
hébreu) est compté comme premier verset du chapitre suivant.

| Source (TA/Vulgate) | Cible (TM/BHSA) | Contenu |
|---|---|---|
| Gen 31:55 | Gen 32:1 | Laban bénit ses fils et les quitte |
| Exod 8:1-4 | Exod 7:26-29 | « Va vers Pharaon… » |
| Lev 6:1-7 | Lev 5:20-26 | sacrifice de réparation |
| Num 13:1 | Num 12:16 | Miryam exclue du camp |
| Deut 29:1 | Deut 28:69 | « Ce sont les paroles de l'alliance » |
| Josh 4:25 | Josh 4:24 | texte de 5:1 collé par l'OCR, recalé |
| 1Sam 20:43 | 1Sam 21:1 | « se levanta David… » |
| 2Sam 18:33 | 2Sam 19:1 | « El rey David lloraba… » |
| 2Kgs 11:21 | 2Kgs 12:1 | Joas roi de Juda |
| 2Chr 14:1 | 2Chr 13:23 | clôture du ch. 13 |
| Neh 4:1-6 | Neh 3:33-38 | mur interrompu |
| Neh 9:38 | Neh 10:1 | « Nos obligamos… » |
| Job 39:32-35 | Job 40:2-5 | réponse de Job |
| Dan 5:31 | Dan 6:1 | Darius prend le royaume |
| Isa 9:1 | Isa 8:23 | « En el primeramente… » |
| Jer 9:1 | Jer 8:23 | « Quien dará… » |
| Ezek 20:45-49 | Ezek 21:1-5 | prophétie contre le Midi |
| Hag 2:1 | Hag 1:15 | « en el año segundo de Darío » |
| Mic 5:1 | Mic 4:14 | « blasfeman contra Israel » |
| Nah 1:15 | Nah 2:1 | « Mira sobre los montes… » |
| Zech 1:18-21 | Zech 2:1-4 | cornes et forgerons |

Réciproquement, le premier verset du chapitre Vulgate suivant reprend
la numérotation massorétique avec le décalage correspondant : TA Exod
8:5+ → TM 8:1+, TA Deut 29:2+ → TM 29:1+ (verset « en trop » côté
Vulgate, delta −1), mais TA 2Sam 19:1+ → TM 19:2+, TA 1Sam 21:1+ →
TM 21:2+, TA 2Kgs 12:1+ → TM 12:2+ (verset « manquant » côté Vulgate,
delta +1).

### 4.2 Changements de numérotation de chapitres

| Source (TA/Vulgate) | Cible (TM/BHSA) | Note |
|---|---|---|
| Deut 12:32 | Deut 13:1 | « Lo que yo te prescribo… » |
| 1Kgs 4:29-34 | 1Kgs 5:9-14 | sagesse de Salomon |
| 1Kgs 5:1-18 | 1Kgs 5:15-32 | fusion Vulgate des ch. 4-5 |
| Num 16:36-48 | Num 17:1-13 |Aaron fleurit, encensoirs |
| Num 17:1+ | Num 17:16+ | 28 versets hébreux au ch. 17 |
| 1Chr 6:1-15 | 1Chr 5:27-41 | généalogie de Lévi |
| 1Chr 6:16+ | 1Chr 6:1+ | reprise normale |
| Job 40:1-19 | Job 40:6-24 | discours de Dieu |
| Job 40:20-28 | Job 41:1-9 | Léviathan |
| Job 41:1+ | Job 41:2+ | suite |
| Dan 3:91-100 | Dan 3:24-33 | après exclusion de l'addition |
| Jer 49:1-2 | Jer 50:1-2 | vrai Jer 49 perdu par l'OCR |
| Jer 1 (tout) | Jer 2:1-7 | copie de TM 2:1-7 (le vrai Jer 1 est perdu) |
| Josh 21:37-43 | Josh 21:38-44 | décalage +1 (numérotation OCR) |
| Joel 2:28+ | Joel 3:1+ | BHSA compte 4 chapitres |
| Joel 3:1+ | Joel 4:1+ | le ch. 4 du module est vide |
| Mal 4:1+ | Mal 3:19+ | BHSA compte 3 chapitres |

### 4.3 Versets isolés rescédés (lacunes ou défauts OCR du module)

Ces cas proviennent de **défauts du module OCR** (verset perdu, texte
porté par le verset suivant), pas de la versification Vulgate :

| Source (TA) | Cible (TM) | Cause |
|---|---|---|
| Exod 22:2+ | Exod 22:1+ | Exod 22:1 manquant (lacune OCR) |
| 2Chr 2:2+ | 2Chr 2:1+ | 2Chr 2:1 manquant (lacune OCR) |
| Num 20:30 | Num 20:29 | 20:29 manquant, texte porté par 20:30 |
| Deut 22:30 | Deut 23:1 | la Vulgate place ce verset en fin de ch. 22 |
| Deut 23:1-23 | Deut 23:2-24 | conséquence du précédent |
| Deut 23:25 | Deut 23:25 | recalage ponctuel (verset de la vigne) |
| Neh 7:69-73 | Neh 7:68-72 | verset des chevaux exclu (addition) |
| Job 16:7-23 | Job 16:6-22 | numérotation OCR décalée d'un verset |
| Amos 6:12-15 | Amos 6:11-14 | idem (recalé sur « caballos », « casa grande ») |
| Isa 1:5 | Isa 1:8 | texte de TM 1:8 mal positionné par l'OCR |
| Isa 45:26 | Isa 45:25 | 45:25 manquant, texte porté par 45:26 |
| Jer 37:5+ | Jer 37:6+ | numérotation décalée |
| Hos 11:12 | Hos 12:1 | fusion Vulgate (Ephraim/Judá) |
| Hos 12:1+ | Hos 12:2+ | conséquence |
| Hos 2:1-23 | Hos 2:3-25 | index collé en 1:10-11 (exclu) |
| Eccl 7:1 | Eccl 7:6 | texte de 7:6 mal positionné (« risas del insensato ») |
| Eccl 7:2+ | Eccl 7:1+ | conséquence |

### 4.4 Cantique des cantiques

Le module OCR a perdu Song 1:1-3 et décalé toute la suite d'un verset,
puis fusionné différemment vers la fin :

| Source (TA) | Cible (TM) |
|---|---|
| Song 1:4-16 | Song 1:5-17 |
| Song 2-4 (entiers), Song 5:1-16 | identité |
| Song 5:17 | Song 6:1 |
| Song 6:2-11 | Song 6:3-12 |
| Song 6:12 | Song 7:1 |
| Song 7:1 | laissé en TM 7:1 (fusion fin 7:1 + début 7:2) |
| Song 7:2+ | Song 7:3+ |

## 5. Psaumes

La versification Vulgate des Psaumes diffère profondément de la
massorétique (fusions et décalages). La table `_PSALMS_MAP` convertit
chaque chapitre/verset Vulgate vers le psaume massorétique. Les
psaumes 1-8, 148-150 et l'intervalle 12-113 (décalé d'une unité) sont
les cas simples. Cas fusionnés :

| Vulgate | Massorétique | Détail |
|---|---|---|
| Ps 9 | Ps 9 + Ps 10 | Ps 9 Vulgate (39 v. dans Torres Amat) fusionne 9+10 : v. 1-21 → Ps 9:1-21, v. 22+ → Ps 10:1+ |
| Ps 10 | Ps 11 | v. 1 (titre seul) auto-exclu, v. 2+ → Ps 11:1+ |
| Ps 113 | Ps 114 + Ps 115 | v. 1-8 → Ps 114, v. 9+ → Ps 115 |
| Ps 114 | Ps 116:1-9 | |
| Ps 115 | Ps 116:10-19 | |
| Ps 116 | Ps 117 | |
| Ps 145 | Ps 146 | v. 1 (titre égaré) exclu, v. 2+ → Ps 146:2+ |
| Ps 146 | Ps 147:1-11 | |
| Ps 147 | Ps 147:12-20 | |

Convention des titres : la BHSA compte le titre (« Aleluya… ») comme
verset 1 du psaume ; Torres Amat fait de même, sauf rares exceptions
couvertes par les exclusions ci-dessous. Les lacunes OCR des psaumes
(ex. Ps 145:2-3 du module) laissent les versets correspondants en
creux (Ps 146:2-3).

## 6. Exclusions

Trois catégories, toutes absentes du fichier final.

### 6.1 Additions deutérocanoniques (versification Vulgate)

| Référence Vulgate | Contenu |
|---|---|
| Dan 3:24-90 | prière d'Azarias, cantique des trois enfants |
| Dan 13-14 | Suzanne, Bel et le dragon |
| Esth 10:4-13 | addition grecque (rêve expliqué) |
| Esth 11-16 | additions grecques d'Esther |
| Neh 7:68 | « verset des chevaux » (addition) |

### 6.2 Secondes moitiés de versets massorétiques (doublons du module)

La Vulgate coupe parfois un verset massorétique en deux ; le module
n'en porte qu'une partie, l'autre étant un doublon :

| Exclu | Raison |
|---|---|
| Judg 5:32 | 2e moitié de TM 5:31 |
| Josh 4:24 | 2e moitié de TM 4:23 |
| Hos 2:24 | 2e moitié de TM 2:25 (« CAPITULO III » collé) |
| Isa 64:1 | 2e moitié de TM 63:19 |
| Ps 2:13 | 2e moitié de TM 2:12 |
| Ps 4:10 | 2e moitié de TM 4:9 |

### 6.3 Défauts OCR du module

| Exclu | Raison |
|---|---|
| 1Kgs 4:1-28 | doublon OCR du chapitre 3 (le vrai 1Kgs 4:1-28 est perdu) |
| Hos 1:1-2, 1:6-7, 1:9-11 | index des prophètes collé par l'OCR dans Osée 1 |
| Isa 1:1-4, 1:6-7 | commentaire de Torres Amat sur « Profeta » collé à la place des versets (le vrai texte est perdu) |
| Esth 10:1 (tronqué) | addition grecque « Acuérdome de un sueño… » collée après le texte canonique |
| Esth 10:3 (tronqué) | note du traducteur « HE TRADUCIDO CON TODA FIDELIDAD… » collée après le texte canonique |
| titres seuls Ps 10:1, Ps 145:1 | titres de psaume sans texte, sans équivalent BHSA |

Enfin, un nettoyage OCR léger (`_clean` dans le script) retire les
espaces parasites, tirets conditionnels, « ¿¿ » doublés, et tronque les
résidus « CAPITULO … » / « HASTA AQUÍ … » collés en fin de verset
(ex. Neh 7:73, Josh 4:25).

## 7. Résultat

- **21 852 versets** écrits dans `data/torres_amat_1823.txt` (94,1 %
  des 23 213 versets de la BHSA ; les manquants sont des lacunes OCR
  du module source, laissées en creux — la liste exacte figure en
  **annexe A**).
- **Zéro référence hors bornes** de la BHSA (vérification automatique
  contre `bhsa_repo/tf`).
- Les versets convertis affichent le **texte espagnol correspondant au
  verset massorétique** : p. ex. `Deut 4:10` affiche « Comenzando de
  aquel dia que te presentaste delante del Señor Dios tuyo en Horeb,
  cuando el Señor me habló diciendo: Junta el pueblo delante de mí,
  para que oigan mis palabras… ».

Pour toute divergence constatée entre le texte espagnol affiché et le
verset hébreu, le diagnostic est le suivant : (1) vérifier dans
`scripts/extract_torres_amat.py` la règle `_VERSE_SHIFTS` du livre et
du chapitre concernés ; (2) comparer le texte du module source avec la
BHSA locale ; (3) ajuster la règle ou l'exclusion, régénérer avec
`python scripts/extract_torres_amat.py <module>`, et relancer les deux
vérifications de bornes et de couverture.

## Annexe A. Références des versets non traduits (lacunes OCR)

Il s'agit des versets **absents du module OCR TorresAmat** et donc
absents de `data/torres_amat_1823.txt` : pour ces références,
l'application affiche « verset absent de la traduction ».
Cette liste a été générée automatiquement par différence entre les
23 213 versets de la base BHSA locale et les 21 852 versets du
fichier de traduction : **1 361 versets manquants (5,9 %)**,
répartis sur les 39 livres (aucun livre n'est complet).

Vue par livre :

| Livre | Versets manquants | Chapitres concernés |
|---|---:|---:|
| Genèse | 130 | 39 |
| Exode | 91 | 31 |
| Lévitique | 48 | 20 |
| Nombres | 103 | 33 |
| Deutéronome | 57 | 25 |
| Josué | 64 | 21 |
| Juges | 35 | 16 |
| Ruth | 2 | 1 |
| 1 Samuel | 40 | 18 |
| 2 Samuel | 37 | 18 |
| 1 Rois | 57 | 15 |
| 2 Rois | 29 | 13 |
| 1 Chroniques | 50 | 23 |
| 2 Chroniques | 35 | 22 |
| Esdras | 25 | 8 |
| Néhémie | 34 | 9 |
| Esther | 5 | 4 |
| Job | 69 | 28 |
| Psaumes | 123 | 58 |
| Proverbes | 37 | 19 |
| Ecclésiaste | 6 | 5 |
| Cantique | 9 | 4 |
| Isaïe | 58 | 31 |
| Jérémie | 114 | 32 |
| Lamentations | 3 | 2 |
| Ézéchiel | 47 | 25 |
| Daniel | 11 | 8 |
| Osée | 14 | 6 |
| Joël | 2 | 1 |
| Amos | 4 | 4 |
| Abdias | 1 | 1 |
| Jonas | 1 | 1 |
| Michée | 5 | 3 |
| Nahum | 2 | 2 |
| Habaquq | 3 | 2 |
| Sophonie | 1 | 1 |
| Zacharie | 7 | 6 |
| Malachie | 2 | 2 |
| **Total** | **1361** | |

Détail chapitre par chapitre (références BHSA, numérotation
massorétique) :

**Genèse**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 24-25 | 2 |
| 3 | 14 | 1 |
| 5 | 32 | 1 |
| 6 | 8, 13 | 2 |
| 7 | 5 | 1 |
| 8 | 8 | 1 |
| 9 | 17, 23 | 2 |
| 10 | 9, 24, 26 | 3 |
| 11 | 1, 5, 9, 23 | 4 |
| 14 | 7, 9, 24 | 3 |
| 15 | 1, 3-4, 7 | 4 |
| 16 | 4, 13 | 2 |
| 17 | 7 | 1 |
| 18 | 4, 14, 33 | 3 |
| 19 | 8 | 1 |
| 20 | 6-8, 13 | 4 |
| 21 | 1, 7, 9, 31, 34 | 5 |
| 24 | 8, 13, 25, 37-39, 52-53, 55-56, 58-59, 61-63 | 15 |
| 25 | 24 | 1 |
| 26 | 24, 35 | 2 |
| 27 | 10, 18, 29, 39 | 4 |
| 29 | 14, 18, 34 | 3 |
| 30 | 24, 36 | 2 |
| 31 | 1, 3-9, 23, 26, 34-35, 49 | 13 |
| 32 | 8, 32 | 2 |
| 34 | 11 | 1 |
| 35 | 7 | 1 |
| 36 | 7-9, 14, 34-35 | 6 |
| 37 | 1, 3 | 2 |
| 38 | 24 | 1 |
| 39 | 9, 14, 23 | 3 |
| 40 | 8-9 | 2 |
| 41 | 28 | 1 |
| 44 | 1, 3-15, 21 | 15 |
| 45 | 1, 8, 21-23 | 5 |
| 46 | 18-20, 22-23 | 5 |
| 47 | 7-9, 14 | 4 |
| 49 | 33 | 1 |
| 50 | 26 | 1 |

**Exode**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-10 | 10 |
| 2 | 21 | 1 |
| 4 | 6, 14, 16, 19, 24, 31 | 6 |
| 5 | 1, 9, 21 | 3 |
| 6 | 9, 29 | 2 |
| 8 | 24 | 1 |
| 9 | 17-18 | 2 |
| 10 | 3, 8-9 | 3 |
| 11 | 9 | 1 |
| 12 | 49 | 1 |
| 13 | 9, 12 | 2 |
| 14 | 24-25 | 2 |
| 15 | 5, 13 | 2 |
| 16 | 4-5, 28-29, 35 | 5 |
| 17 | 8 | 1 |
| 18 | 18 | 1 |
| 19 | 12, 25 | 2 |
| 21 | 7, 9, 29, 37 | 4 |
| 25 | 1-9, 24 | 10 |
| 26 | 19-20 | 2 |
| 27 | 7 | 1 |
| 28 | 8, 25 | 2 |
| 29 | 7-9, 25, 39 | 5 |
| 30 | 2, 36 | 2 |
| 32 | 12, 34 | 2 |
| 34 | 15 | 1 |
| 35 | 9, 29, 35 | 3 |
| 36 | 8, 24 | 2 |
| 37 | 1 | 1 |
| 39 | 7, 9, 13, 18-19, 25-28 | 9 |
| 40 | 37-38 | 2 |

**Lévitique**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 3 | 13, 17 | 2 |
| 4 | 15, 24 | 2 |
| 5 | 26 | 1 |
| 6 | 20 | 1 |
| 9 | 20 | 1 |
| 10 | 7-9, 11, 19 | 5 |
| 11 | 11, 28, 35 | 3 |
| 12 | 8 | 1 |
| 13 | 1-2, 5, 34, 51, 55, 57 | 7 |
| 14 | 54-56 | 3 |
| 16 | 19 | 1 |
| 17 | 1-2, 11, 13 | 4 |
| 18 | 9 | 1 |
| 19 | 8 | 1 |
| 20 | 5 | 1 |
| 21 | 9 | 1 |
| 24 | 7-8 | 2 |
| 25 | 5, 34-35, 51, 55 | 5 |
| 26 | 9, 15, 21, 35, 46 | 5 |
| 27 | 12 | 1 |

**Nombres**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-4, 6-15, 27, 39 | 16 |
| 2 | 9, 29, 34 | 3 |
| 3 | 24, 34 | 2 |
| 4 | 2, 33, 38 | 3 |
| 5 | 8, 18, 29 | 3 |
| 6 | 7 | 1 |
| 7 | 4, 35, 71-73, 77 | 6 |
| 8 | 9, 21-22 | 3 |
| 9 | 7, 22 | 2 |
| 10 | 7, 27 | 2 |
| 11 | 1, 6, 25, 29, 32, 35 | 6 |
| 13 | 4, 21 | 2 |
| 14 | 35, 37, 39 | 3 |
| 15 | 17, 20, 35 | 3 |
| 16 | 29, 33, 35 | 3 |
| 17 | 1, 14-15 | 3 |
| 18 | 6-7, 18 | 3 |
| 19 | 14 | 1 |
| 20 | 5, 7, 23 | 3 |
| 21 | 27 | 1 |
| 22 | 8-9, 38-39 | 4 |
| 23 | 9 | 1 |
| 24 | 9, 24 | 2 |
| 25 | 9, 19 | 2 |
| 26 | 35 | 1 |
| 27 | 8 | 1 |
| 28 | 8, 19, 27, 29 | 4 |
| 29 | 1, 5, 34 | 3 |
| 30 | 14 | 1 |
| 31 | 8-9, 17, 29, 34, 36 | 6 |
| 32 | 5, 15, 24, 35 | 4 |
| 33 | 5, 24, 34 | 3 |
| 35 | 33-34 | 2 |

**Deutéronome**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 29, 35, 44-45 | 4 |
| 2 | 7, 16-17, 34 | 4 |
| 3 | 3, 9 | 2 |
| 4 | 48-49 | 2 |
| 7 | 1, 19 | 2 |
| 8 | 5, 13 | 2 |
| 9 | 7 | 1 |
| 10 | 5 | 1 |
| 11 | 8, 12, 24 | 3 |
| 13 | 6 | 1 |
| 14 | 26 | 1 |
| 15 | 8, 13, 18 | 3 |
| 16 | 7 | 1 |
| 17 | 4, 8, 18 | 3 |
| 18 | 1 | 1 |
| 20 | 4, 8-9 | 3 |
| 22 | 3, 7, 29 | 3 |
| 23 | 26 | 1 |
| 24 | 4, 8-9 | 3 |
| 25 | 1, 12 | 2 |
| 26 | 5, 8 | 2 |
| 28 | 26, 33, 55 | 3 |
| 29 | 13-14, 25, 28 | 4 |
| 32 | 20, 34 | 2 |
| 33 | 8, 12, 29 | 3 |

**Josué**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 9, 15, 18 | 3 |
| 3 | 3 | 1 |
| 4 | 8-9 | 2 |
| 5 | 1, 9-15 | 8 |
| 6 | 4, 24, 26 | 3 |
| 7 | 9 | 1 |
| 8 | 1, 8, 34-35 | 4 |
| 9 | 9 | 1 |
| 10 | 5, 34-35 | 3 |
| 11 | 1 | 1 |
| 12 | 11, 16-22 | 8 |
| 13 | 21, 25 | 2 |
| 15 | 31 | 1 |
| 16 | 8 | 1 |
| 17 | 9, 14 | 2 |
| 18 | 16, 18, 26-28 | 5 |
| 19 | 4, 6, 8-9, 33-34, 39, 44, 49 | 9 |
| 21 | 33, 35-37, 45 | 5 |
| 22 | 9, 34 | 2 |
| 23 | 7 | 1 |
| 24 | 5 | 1 |

**Juges**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 9, 15, 34 | 3 |
| 2 | 2 | 1 |
| 5 | 29 | 1 |
| 6 | 9 | 1 |
| 7 | 1 | 1 |
| 8 | 8-9, 13, 34-35 | 5 |
| 9 | 7-9, 28-29, 51, 55-56 | 8 |
| 11 | 5 | 1 |
| 12 | 12 | 1 |
| 13 | 5, 24 | 2 |
| 15 | 9, 13, 19 | 3 |
| 16 | 8, 23 | 2 |
| 17 | 7 | 1 |
| 18 | 9 | 1 |
| 20 | 9, 33 | 2 |
| 21 | 9, 25 | 2 |

**Ruth**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 4 | 1, 7 | 2 |

**1 Samuel**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-6 | 6 |
| 2 | 1, 22 | 2 |
| 4 | 17, 21 | 2 |
| 7 | 1, 8 | 2 |
| 8 | 8 | 1 |
| 10 | 8 | 1 |
| 13 | 16, 19 | 2 |
| 14 | 27 | 1 |
| 15 | 12 | 1 |
| 16 | 18 | 1 |
| 17 | 5, 22 | 2 |
| 19 | 16, 18 | 2 |
| 20 | 28, 33 | 2 |
| 23 | 7-8, 11, 13, 16 | 5 |
| 25 | 29 | 1 |
| 27 | 6, 8 | 2 |
| 28 | 20-25 | 6 |
| 30 | 27 | 1 |

**2 Samuel**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 5 | 1 |
| 3 | 31, 33-38 | 7 |
| 5 | 23 | 1 |
| 6 | 8-9 | 2 |
| 8 | 14 | 1 |
| 9 | 7 | 1 |
| 10 | 1-2, 17 | 3 |
| 11 | 1, 6, 18, 22 | 4 |
| 12 | 17, 19 | 2 |
| 13 | 5, 31 | 2 |
| 14 | 33 | 1 |
| 15 | 31, 33 | 2 |
| 16 | 5 | 1 |
| 18 | 14 | 1 |
| 19 | 34, 43 | 2 |
| 20 | 14 | 1 |
| 21 | 8 | 1 |
| 22 | 7, 22, 25, 45 | 4 |

**1 Rois**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 5, 13, 40, 42 | 4 |
| 2 | 1 | 1 |
| 4 | 1-20 | 20 |
| 5 | 1-8, 31 | 9 |
| 6 | 35 | 1 |
| 7 | 14-15, 36, 38 | 4 |
| 8 | 33, 49, 59 | 3 |
| 9 | 1 | 1 |
| 10 | 26 | 1 |
| 11 | 21, 26, 28 | 3 |
| 12 | 7, 21 | 2 |
| 14 | 1-2 | 2 |
| 15 | 13 | 1 |
| 20 | 22, 33, 36 | 3 |
| 21 | 5, 26 | 2 |

**2 Rois**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 5 | 1 |
| 2 | 3, 24 | 2 |
| 3 | 1, 7 | 2 |
| 4 | 23, 35 | 2 |
| 7 | 18 | 1 |
| 9 | 15, 24, 28 | 3 |
| 10 | 23-24 | 2 |
| 11 | 4, 11 | 2 |
| 14 | 18 | 1 |
| 19 | 8-9, 13, 17 | 4 |
| 21 | 13 | 1 |
| 22 | 2-3, 7, 9, 18-20 | 7 |
| 23 | 4 | 1 |

**1 Chroniques**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 33 | 1 |
| 2 | 20, 23, 35, 44 | 4 |
| 4 | 1, 14, 21 | 3 |
| 6 | 29, 31, 36, 39, 55, 60, 66 | 7 |
| 7 | 5, 28, 33, 35 | 4 |
| 8 | 2-6, 18 | 6 |
| 9 | 34-35 | 2 |
| 10 | 1 | 1 |
| 11 | 1, 30, 47 | 3 |
| 12 | 7, 41 | 2 |
| 13 | 3 | 1 |
| 14 | 6-8 | 3 |
| 15 | 3, 22 | 2 |
| 16 | 3, 17 | 2 |
| 17 | 1 | 1 |
| 18 | 15 | 1 |
| 19 | 12 | 1 |
| 20 | 8 | 1 |
| 21 | 5 | 1 |
| 23 | 15 | 1 |
| 24 | 8 | 1 |
| 26 | 18 | 1 |
| 27 | 20 | 1 |

**2 Chroniques**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 3, 18 | 2 |
| 2 | 7 | 1 |
| 5 | 5, 7 | 2 |
| 7 | 1, 9, 13 | 3 |
| 9 | 8, 13 | 2 |
| 10 | 4 | 1 |
| 12 | 8 | 1 |
| 14 | 7 | 1 |
| 15 | 13 | 1 |
| 16 | 3 | 1 |
| 19 | 10-11 | 2 |
| 20 | 6, 14 | 2 |
| 23 | 8 | 1 |
| 25 | 8, 11 | 2 |
| 26 | 7, 13 | 2 |
| 27 | 3, 5 | 2 |
| 28 | 5, 27 | 2 |
| 29 | 9 | 1 |
| 30 | 5 | 1 |
| 31 | 21 | 1 |
| 32 | 13, 30 | 2 |
| 34 | 13, 28 | 2 |

**Esdras**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 6-11 | 6 |
| 2 | 1, 23, 46 | 3 |
| 5 | 15-16 | 2 |
| 6 | 12 | 1 |
| 7 | 8, 26, 28 | 3 |
| 8 | 13, 27, 33 | 3 |
| 9 | 5 | 1 |
| 10 | 33, 35-36, 38, 40, 44 | 6 |

**Néhémie**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 5 | 1 |
| 3 | 8, 32, 34 | 3 |
| 4 | 9 | 1 |
| 7 | 1, 26, 42, 57, 63 | 5 |
| 8 | 1 | 1 |
| 9 | 1, 22, 35 | 3 |
| 10 | 3-10, 14, 25, 36 | 11 |
| 11 | 7-8, 26, 28, 34 | 5 |
| 12 | 14, 27, 33, 47 | 4 |

**Esther**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 4 | 1 | 1 |
| 5 | 1 | 1 |
| 6 | 8 | 1 |
| 9 | 13, 31 | 2 |

**Job**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-8 | 8 |
| 3 | 3 | 1 |
| 5 | 15 | 1 |
| 8 | 17 | 1 |
| 11 | 2, 8, 10, 15 | 4 |
| 13 | 3, 11, 13 | 3 |
| 15 | 1 | 1 |
| 16 | 12 | 1 |
| 17 | 7 | 1 |
| 19 | 8 | 1 |
| 20 | 3 | 1 |
| 21 | 2-4, 33 | 4 |
| 23 | 8 | 1 |
| 24 | 15 | 1 |
| 25 | 1-2 | 2 |
| 26 | 2, 8 | 2 |
| 27 | 13 | 1 |
| 29 | 9 | 1 |
| 30 | 8 | 1 |
| 31 | 18, 33 | 2 |
| 32 | 7, 12, 18 | 3 |
| 33 | 7, 27 | 2 |
| 34 | 13, 33, 35, 37 | 4 |
| 35 | 1-2, 8, 13 | 4 |
| 36 | 33 | 1 |
| 38 | 23, 34-36, 39 | 5 |
| 40 | 1, 5, 25-32 | 10 |
| 42 | 1, 17 | 2 |

**Psaumes**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 7 | 13 | 1 |
| 8 | 2, 8 | 2 |
| 10 | 2-18 | 17 |
| 18 | 3, 31, 37-38 | 4 |
| 20 | 6 | 1 |
| 23 | 5 | 1 |
| 25 | 19 | 1 |
| 27 | 10 | 1 |
| 33 | 3, 8 | 2 |
| 34 | 13-14, 22 | 3 |
| 37 | 33, 35 | 2 |
| 39 | 2-3, 12 | 3 |
| 44 | 27 | 1 |
| 45 | 4, 14 | 2 |
| 48 | 5 | 1 |
| 49 | 7 | 1 |
| 51 | 18 | 1 |
| 54 | 8 | 1 |
| 56 | 14 | 1 |
| 60 | 7-8, 12 | 3 |
| 61 | 7, 9 | 2 |
| 62 | 3, 7, 9-10 | 4 |
| 66 | 2 | 1 |
| 68 | 24 | 1 |
| 71 | 8-9 | 2 |
| 73 | 11, 23, 28 | 3 |
| 76 | 3, 8 | 2 |
| 78 | 13, 31, 35, 54, 72 | 5 |
| 79 | 3 | 1 |
| 83 | 5 | 1 |
| 88 | 14 | 1 |
| 89 | 33, 43 | 2 |
| 92 | 10-11 | 2 |
| 93 | 3 | 1 |
| 94 | 8 | 1 |
| 96 | 5 | 1 |
| 99 | 8 | 1 |
| 102 | 12, 22 | 2 |
| 103 | 8-9, 20 | 3 |
| 104 | 35 | 1 |
| 105 | 35 | 1 |
| 106 | 9, 26, 42 | 3 |
| 107 | 7, 27, 39, 41 | 4 |
| 109 | 4 | 1 |
| 111 | 4 | 1 |
| 118 | 22-23 | 2 |
| 119 | 9, 95, 103, 115, 133 | 5 |
| 120 | 3, 5 | 2 |
| 121 | 3 | 1 |
| 127 | 3 | 1 |
| 129 | 2-3 | 2 |
| 135 | 12 | 1 |
| 136 | 5-6, 13, 25 | 4 |
| 138 | 3 | 1 |
| 139 | 3, 12 | 2 |
| 143 | 8 | 1 |
| 144 | 11 | 1 |
| 146 | 1-3, 8 | 4 |

**Proverbes**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 2-3, 23 | 3 |
| 3 | 33 | 1 |
| 5 | 21 | 1 |
| 6 | 11, 26, 30-31, 33, 35 | 6 |
| 7 | 7 | 1 |
| 8 | 33 | 1 |
| 10 | 23, 31 | 2 |
| 13 | 1 | 1 |
| 14 | 12, 24, 28, 34-35 | 5 |
| 16 | 3, 18 | 2 |
| 20 | 1 | 1 |
| 22 | 20-21 | 2 |
| 23 | 6, 13, 15, 28 | 4 |
| 24 | 5 | 1 |
| 26 | 28 | 1 |
| 27 | 7 | 1 |
| 28 | 13 | 1 |
| 30 | 33 | 1 |
| 31 | 25, 30 | 2 |

**Ecclésiaste**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 5 | 8 | 1 |
| 6 | 12 | 1 |
| 7 | 4 | 1 |
| 8 | 8, 13 | 2 |
| 11 | 1 | 1 |

**Cantique**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-4 | 4 |
| 2 | 1, 3, 16 | 3 |
| 6 | 2 | 1 |
| 7 | 2 | 1 |

**Isaïe**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-7 | 7 |
| 3 | 12-13 | 2 |
| 4 | 1 | 1 |
| 9 | 11 | 1 |
| 17 | 5 | 1 |
| 19 | 19, 21 | 2 |
| 20 | 5 | 1 |
| 21 | 5 | 1 |
| 22 | 8 | 1 |
| 23 | 8 | 1 |
| 25 | 8 | 1 |
| 28 | 19 | 1 |
| 29 | 1 | 1 |
| 30 | 2, 7-9 | 4 |
| 31 | 7 | 1 |
| 32 | 18 | 1 |
| 33 | 9, 19 | 2 |
| 36 | 1-9 | 9 |
| 37 | 8, 38 | 2 |
| 40 | 8 | 1 |
| 41 | 6, 23, 27 | 3 |
| 43 | 1 | 1 |
| 45 | 5, 7 | 2 |
| 48 | 5 | 1 |
| 49 | 1 | 1 |
| 51 | 14, 19 | 2 |
| 52 | 1, 8 | 2 |
| 59 | 1, 13 | 2 |
| 60 | 18 | 1 |
| 64 | 7 | 1 |
| 65 | 13 | 1 |

**Jérémie**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-19 | 19 |
| 2 | 5, 35 | 2 |
| 3 | 1, 9 | 2 |
| 4 | 23, 26 | 2 |
| 5 | 23, 31 | 2 |
| 6 | 1, 8 | 2 |
| 7 | 5 | 1 |
| 11 | 7 | 1 |
| 12 | 6 | 1 |
| 13 | 1, 3-5, 11 | 5 |
| 15 | 8, 17-18 | 3 |
| 16 | 5 | 1 |
| 18 | 2, 5 | 2 |
| 19 | 1 | 1 |
| 22 | 5, 28 | 2 |
| 23 | 1 | 1 |
| 30 | 1, 13 | 2 |
| 31 | 7 | 1 |
| 32 | 7, 33 | 2 |
| 33 | 1, 22-23 | 3 |
| 35 | 8-9 | 2 |
| 36 | 18, 30 | 2 |
| 37 | 1, 5 | 2 |
| 38 | 7-8, 25 | 3 |
| 39 | 5 | 1 |
| 41 | 7 | 1 |
| 46 | 15 | 1 |
| 48 | 35 | 1 |
| 49 | 1-39 | 39 |
| 50 | 38 | 1 |
| 51 | 35, 37, 39, 43, 54 | 5 |
| 52 | 27 | 1 |

**Lamentations**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 13 | 1 |
| 3 | 8, 61 | 2 |

**Ézéchiel**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 10 | 1 |
| 3 | 3 | 1 |
| 5 | 15 | 1 |
| 7 | 23 | 1 |
| 13 | 18 | 1 |
| 14 | 3, 18, 22 | 3 |
| 16 | 1, 31 | 2 |
| 17 | 3, 22 | 2 |
| 18 | 28 | 1 |
| 20 | 21, 23, 31, 33 | 4 |
| 21 | 23 | 1 |
| 23 | 2, 12, 31-33, 35 | 6 |
| 27 | 30-31 | 2 |
| 29 | 5 | 1 |
| 32 | 31 | 1 |
| 33 | 17 | 1 |
| 35 | 5 | 1 |
| 36 | 7, 17, 23, 35 | 4 |
| 37 | 15, 20, 22 | 3 |
| 38 | 8 | 1 |
| 39 | 1, 23 | 2 |
| 40 | 30, 33, 49 | 3 |
| 42 | 1, 3 | 2 |
| 44 | 23 | 1 |
| 48 | 3 | 1 |

**Daniel**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 17 | 1 |
| 3 | 8 | 1 |
| 4 | 23, 33 | 2 |
| 5 | 1 | 1 |
| 8 | 1, 13 | 2 |
| 9 | 8 | 1 |
| 11 | 27 | 1 |
| 12 | 3, 9 | 2 |

**Osée**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 1-3, 6-7, 9 | 6 |
| 2 | 1-2, 13, 24 | 4 |
| 4 | 13 | 1 |
| 9 | 12 | 1 |
| 11 | 1 | 1 |
| 14 | 5 | 1 |

**Joël**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 1, 3 | 2 |

**Amos**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 9 | 1 |
| 2 | 1 | 1 |
| 4 | 1 | 1 |
| 7 | 15 | 1 |

**Abdias**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 13 | 1 |

**Jonas**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 13 | 1 |

**Michée**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 1 | 1 |
| 5 | 7, 12, 14 | 3 |
| 7 | 7 | 1 |

**Nahum**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 10 | 1 |
| 2 | 6 | 1 |

**Habaquq**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 2 | 1, 19 | 2 |
| 3 | 11 | 1 |

**Sophonie**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 3 | 8 | 1 |

**Zacharie**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 3 | 1 | 1 |
| 6 | 8 | 1 |
| 7 | 1 | 1 |
| 8 | 23 | 1 |
| 10 | 5 | 1 |
| 14 | 8, 13 | 2 |

**Malachie**

| Chapitre | Versets manquants | Nombre |
|---:|---|---:|
| 1 | 8 | 1 |
| 3 | 3 | 1 |
