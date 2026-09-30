# Les verbes faibles de l'hébreu biblique — index

Ce document est le point d'entrée de la série consacrée aux **verbes faibles** (שְׁלֵמִים לֹא, *lo' shlemim*, « verbes non parfaits ») de l'hébreu biblique. Il donne une introduction générale et historique, puis renvoie aux dix documentations détaillées, une par catégorie du moteur de conjugaison du projet.

## Introduction

### Verbes forts et verbes faibles

L'hébreu biblique conjugue ses verbes à partir d'une **racine consonantique**, le plus souvent trilitaire (שׁמר « garder », קטל-type « tuer » en grammaire des langues sémitiques). Un **verbe fort** (שָׁלֵם, *shalem*) ne contient aucune radicale « faible » : ses formes suivent régulièrement le paradigme de référence. Un **verbe faible** contient au moins une radicale dont le comportement phonétique perturbe ce paradigme :

- les **gutturales** (א ה ח ע, auxquelles la tradition ajoute ר) refusent le sheva et le daguesh fort, et attirent les voyelles de timbre *a* ;
- les **semi-consonnes** (ו י) servent de *matres lectionis* : elles s'assimilent, s'élide ou s'allongent en voyelles ;
- le **נ** initial s'assimile à la radicale suivante ;
- le **א** quiescent ne se prononce qu'avec une voyelle.

La grammaire hébraïque traditionnelle des Massorètes et des grammairiens médiévaux (cf. les tableaux de conjugaison de la Massorah) classe donc les verbes selon la position de la radicale faible : *pe* (פ״), *ʿayin* (ע״) et *lamed* (ל״) désignant respectivement la première, la deuxième et la troisième radicale. D'où les appellations pe-nun, ayin-waw, lamed-he, etc. Les racines dont les 2ᵉ et 3ᵉ radicales sont identiques forment les verbes « doubles » (ע״ע).

### Le classement du projet

Le moteur de conjugaison du projet (`bhsa_grammar/binyan_gen.py`) reprend cette classification traditionnelle dans `classify_root`, avec dix catégories et un ordre de priorité (une racine entre dans la première catégorie qui la matche) :

`double > lamed_he > lamed_alef > lamed_guttural > ayin_vav > ayin_guttural > pe_nun > pe_alef > pe_yod > pe_guttural > strong`

Deux choix du projet diffèrent de la tradition et sont documentés dans les fichiers concernés :

- les gutturales du projet sont **א ה ח ע** (`GUTTURALS`) : **ר** est traité comme un verbe fort, alors que la grammaire traditionnelle compte « gutturales et assimilées » א ע ה ח ר ;
- l'alef initial a sa catégorie propre (`pe_alef`, par quiescence) et l'alef final prime sur les autres faiblesses (בוא, יצא, נשׂא sont `lamed_alef`).

### Les dix catégories

| # | Document | Catégorie | Radicale faible | Verbes (≥ 10 occ.) | Exemple type |
|---|---|---|---|---|---|
| 1 | [verbes_lamed_he.md](verbes_lamed_he.md) | lamed-he (ל״ה) | 3ᵉ radicale ה | 93 | בנה « bâtir » |
| 2 | [verbes_ayin_guttural.md](verbes_ayin_guttural.md) | ayin-guttural (ע״ג) | 2ᵉ radicale gutturale | 78 | שׁאל « demander » |
| 3 | [verbes_pe_guttural.md](verbes_pe_guttural.md) | pe-guttural (פ״ג) | 1ʳᵉ radicale ה/ח/ע | 77 | עבד « servir » |
| 4 | [verbes_lamed_guttural.md](verbes_lamed_guttural.md) | lamed-guttural (ל״ג) | 3ᵉ radicale gutturale | 69 | שׁלח « envoyer » |
| 5 | [verbes_ayin_vav_yod.md](verbes_ayin_vav_yod.md) | creux (ע״ו/ע״י) | 2ᵉ radicale ו/י | 65 | קום « se lever » |
| 6 | [verbes_doubles.md](verbes_doubles.md) | doubles (ע״ע) | 2ᵉ = 3ᵉ radicale | 46 | סבב « entourer » |
| 7 | [verbes_pe_nun.md](verbes_pe_nun.md) | pe-nun (פ״נ) | 1ʳᵉ radicale נ | 35 | נפל « tomber » |
| 8 | [verbes_pe_yod.md](verbes_pe_yod.md) | pe-yod (פ״י) | 1ʳᵉ radicale י | 24 | ישׁב « habiter » |
| 9 | [verbes_lamed_alef.md](verbes_lamed_alef.md) | lamed-alef (ל״א) | 3ᵉ radicale א | 23 | מצא « trouver » |
| 10 | [verbes_pe_alef.md](verbes_pe_alef.md) | pe-alef (פ״א) | 1ʳᵉ radicale א | 21 | אכל « manger » |

Chaque documentation détaille : la définition de la catégorie, les règles de conjugaison au qal, un paradigme complet en exemple, et le tableau des lexèmes attestés au moins 10 fois dans la **BHSA** (base morphologique de l'ETCBC, branche `data2021`), avec pour chaque verbe cinq formes générées par le moteur du projet (`binyan_gen.py`, gabarits de `binyan_templates.json`).

### Perspective historique

La notion de verbe faible est née du travail des **Massorètes** de Tibériade (viiᵉ-xᵉ siècles), qui ont vocalisé le texte consonantique et fixé par écrit les variations des verbes à radicales faibles ; leurs listes de formes (la Massorah petite et grande) recensent déjà les assimilations du נ, les élisions du ה final et les voyelles de compensation des gutturales. Les grammairiens juifs médiévaux ont systématisé ce savoir : **Judah Ḥayyūj** (xᵉ s., Cordoue), considéré comme le père de la grammaire hébraïque scientifique, a démontré que les verbes dits « irréguliers » ont eux aussi trois lettres radicales — les faibles étant des *matres lectionis* ; **Abu al-Faraj** et **David Qimḥi** (xiiᵉ-xiiiᵉ s., le « Radak ») ont diffusé la classification pe/ʿayin/lamed encore en usage, suivie des grammairiens de la Renaissance et de la période moderne (Buxtorf, Gesenius — dont la *Hebräische Grammatik* du xixe siècle reste la référence ; Joüon-Muraoka, Waltke-O'Connor aujourd'hui). La classification du projet suit directement cette tradition, appliquée aux données de la Biblia Hebraica Stuttgartensia.

### Pour aller plus loin dans l'application

Le mode **« Binyanim »** de l'application affiche, pour n'importe quelle racine ou forme conjuguée, la catégorie reconnue (`classify_root`), les règles correspondantes (onglet « Règles du verbe faible ») et le paradigme complet de tous les binyanim et temps, avec les mêmes gabarits que ceux utilisés pour produire les tableaux de cette série.
