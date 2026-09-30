# Les verbes pe-yod (פ״י) — liste et règles de conjugaison

Un **verbe pe-yod** (פ״י) est un verbe dont la **1ʳᵉ radicale est un י** : ישׁב « habiter », ילד « enfanter », ירד « descendre ». Le י initial s'assimile en voyelle aux formes à préfixe : la 2ᵉ radicale prend le daguesh fort.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **24** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `pe_yod`).

## Règles générales de conjugaison (qal)

1. **Assimilation du י.** Aux formes à préfixe, le י initial s'assimile : יֵשֵׁב « il habitera », תֵּשֵׁב, אֵשֵׁב — le préfixe porte une voyelle longue (sere) au lieu du hireq du verbe fort, et la 2ᵉ radicale porte le daguesh (שׁ → שּׁ après voyelle).
2. **Parfait régulier.** Le parfait conserve le י : יָשַׁב, יָשְׁבָה, יָשַׁבְתָּ, יָשְׁבוּ.
3. **Imparfait en sere.** L'imparfait qal des pe-yod a une voyelle de préfixe sere et la voyelle radicale sere : יֵשֵׁב (au lieu de la forme mixte *יִישַׁב) ; jussif יֵשֵׁב ; wayyiqtol וַיֵּשֶׁב.
4. **Verbes « mi ».** Certains pe-yod au qal imparfait présentent la séquence hireq-yod initiale (forme « verbe mi ») : יִירָשׁ « il prendra possession », יִיקַץ « il s'éveillera », יִירָא « il craindra » — le י matériel s'entend, distinct de l'assimilation complète.
5. **Verbes fréquents.** ישׁב « habiter » (1083 occ.), ילד « enfanter » (493), ירד « descendre » (378), ירשׁ « prendre possession » (232), יסף « ajouter » (215), יכל « pouvoir » (207). À noter : יצא « sortir » (1071 occ.) est classé `lamed_alef` (l'alef final prime sur le י initial).

## Exemple de conjugaison complète : ישׁב « habiter » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | יָשַׁב |
| Parfait | 3 | f. sg. | יָשְׁבָה |
| Parfait | 2 | m. sg. | יָשַׁבְתָּ |
| Parfait | 2 | f. sg. | יָשַׁבְתְּ |
| Parfait | 1 | c. sg. | יָשַׁבְתִּי |
| Parfait | 3 | m. pl. | יָשְׁבוּ |
| Imparfait | 3 | m. sg. | יִישַׁב |
| Imparfait | 3 | f. sg. | תֵּשֵׁב |
| Imparfait | 2 | m. sg. | תֵשֵׁב |
| Imparfait | 2 | f. sg. | תִיְשְׁבִי |
| Imparfait | 1 | c. sg. | אֵשֵׁב |
| Imparfait | 3 | m. pl. | יֵשְׁבוּ |
| Jussif | 3 | m. sg. | יִּישַׁב |
| Impératif | 2 | m. sg. | שֵׁב |
| Impératif | 2 | f. sg. | שְׁבִי |
| Impératif | 2 | m. pl. | שְׁבוּ |
| Infinitif construit | — | — | שֶׁבֶת |
| Infinitif absolu | — | — | יָשֹׁב |
| Participe actif | — | m. sg. | יֹשֵׁב |

## Les 24 verbes pe-yod (פ״י) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `pe_yod` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | יבשׁ | se dessécher | be dry | 78 | יָבַשׁ | יִיבַשׁ | בֵשׁ | בֶשֶׁת | יֹבֵשׁ |
| 2 | יבל | conduire | bring | 23 | יָבַל | יִיבַל | בֵל | בֶלֶת | יֹבֵל |
| 3 | ישׁב | demeurer | sit | 1083 | יָשַׁב | יִישַׁב | שֵׁב | שֶׁבֶת | יֹשֵׁב |
| 4 | ישׁן | dormir | sleep | 17 | יָשַׁן | יִישַׁן | שֵׁן | שֶׁנֶת | יֹשֵׁן |
| 5 | ישׁר | droit | be right | 26 | יָשַׁר | יִישַׁר | שֵׁר | שֶׁרֶת | יֹשֵׁר |
| 6 | יכל | pouvoir | be able | 207 | יָכַל | יִיכַל | כֵל | כֶלֶת | יֹכֵל |
| 7 | ילד | engendrer | bear | 493 | יָלַד | יִילַד | לֵד | לֶדֶת | יֹלֵד |
| 8 | ינק | nourrice | suck | 28 | יָנַק | יִינַק | נֵק | נֶקֶת | יֹנֵק |
| 9 | יקד | brûler | burn | 18 | יָקַד | יִיקַד | קֵד | קֶדֶת | יֹקֵד |
| 10 | יקר | précieux | be precious | 12 | יָקַר | יִיקַר | קֵר | קֶרֶת | יֹקֵר |
| 11 | יקץ | s’éveiller | awake | 12 | יָקַץ | יִיקַץ | קֵץ | קֶצֶת | יֹקֵץ |
| 12 | ירשׁ | prendre | trample down | 232 | יָרַשׁ | יִירַשׁ | רֵשׁ | רֶשֶׁת | יֹרֵשׁ |
| 13 | ירד | descendre | descend | 378 | יָרַד | יִירַד | רֵד | רֶדֶת | יֹרֵד |
| 14 | יסד | fonder | found | 42 | יָסַד | יִיסַד | סֵד | סֶדֶת | יֹסֵד |
| 15 | יסף | ajouter | add | 215 | יָסַף | יִיסַף | סֵף | סֶפֶת | יֹסֵף |
| 16 | יסר | discipliner | admonish | 44 | יָסַר | יִיסַר | סֵר | סֶרֶת | יֹסֵר |
| 17 | יתר | rester | remain | 107 | יָתַר | יִיתַר | תֵר | תֶרֶת | יֹתֵר |
| 18 | יטב | être bon | be good | 120 | יָטַב | יִיטַב | טֵב | טֶבֶת | יֹטֵב |
| 19 | יצב | se tenir debout | stand | 51 | יָצַב | יִיצַב | צֵב | צֶבֶת | יֹצֵב |
| 20 | יצג | placer | set | 17 | יָצַג | יִיצַג | צֵג | צֶגֶת | יֹצֵג |
| 21 | יצק | verser | pour | 55 | יָצַק | יִיצַק | צֵק | צֶקֶת | יֹצֵק |
| 22 | יצר | formé | shape | 46 | יָצַר | יִיצַר | צֵר | צֶרֶת | יֹצֵר |
| 23 | יצת | allumer | kindle | 28 | יָצַת | יִיצַת | צֵת | צֶתֶת | יֹצֵת |
| 24 | יזב |  | save | 10 | יָזַב | יִיזַב | זֵב | זֶבֶת | יֹזֵב |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `pe_yod`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
