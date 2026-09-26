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
  du module source, laissées en creux).
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
