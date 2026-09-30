# Les verbes pe-nun (פ״נ) — liste et règles de conjugaison

Un **verbe pe-nun** (פ״נ) est un verbe dont la **1ʳᵉ radicale est un נ** : נפל « tomber », נתן « donner », נגשׁ « approcher ». Le נ initial s'assimile aux formes à préfixe : il disparaît et la 2ᵉ radicale prend un daguesh fort.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **35** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `pe_nun`).

## Règles générales de conjugaison (qal)

1. **Assimilation du נ.** Aux formes à préfixe (imparfait, impératif, participe, wayyiqtol, infinitif), le נ s'assimile à la 2ᵉ radicale : יִפֹּל « il tombera » (racine נפל), et non *יִנְפֹּל ; וַיִּפֹּל ; participe נֹפֵל conservant le נ initial de syllabe.
2. **Formes à suffixe.** Au parfait et partout où le נ ouvre une syllabe, il est conservé : נָפַל « il est tombé », נָפַלְתִּי. À l'impératif, la forme attendue avec assimilation (פֹּל) a généralement été remplacée par la forme en נ (נְפֹל, נִפְלִי) par analogie avec le parfait.
3. **Verbes très fréquents.** נתן « donner » (2019 occ.), נפל « tomber » (447), נגד « être en face, déclarer » (373), נצל « arracher » (218), נגשׁ « approcher » (126), נצב « se tenir » (75). À noter : נשׂא « porter » (658 occ.) est classé `lamed_alef` par `classify_root` (l'alef final prime sur le נ initial).

## Exemple de conjugaison complète : נפל « tomber » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | נָפַל |
| Parfait | 3 | f. sg. | נָפְלָה |
| Parfait | 2 | m. sg. | נָפַלְתָּ |
| Parfait | 2 | f. sg. | נָפַלְתְּ |
| Parfait | 1 | c. sg. | נָפַלְתִּי |
| Parfait | 3 | m. pl. | נָפְלוּ |
| Imparfait | 3 | m. sg. | יִפֹּל |
| Imparfait | 3 | f. sg. | תִּפֹּל |
| Imparfait | 2 | m. sg. | תִּפֹּל |
| Imparfait | 2 | f. sg. | תִנְפְּלִי |
| Imparfait | 1 | c. sg. | אֶפֹּול |
| Imparfait | 3 | m. pl. | יִפְּלוּ |
| Jussif | 3 | m. sg. | יִּפֹּל |
| Impératif | 2 | m. sg. | נְפֹל |
| Impératif | 2 | f. sg. | נִפְלִי |
| Impératif | 2 | m. pl. | נִפְלוּ |
| Infinitif construit | — | — | נְפֹל |
| Infinitif absolu | — | — | נָפֹול |
| Participe actif | — | m. sg. | נֹפֵל |

## Les 35 verbes pe-nun (פ״נ) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `pe_nun` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | נבל | harpe | wither | 25 | נָבַל | יִבֹּל | נְבֹל | נְבֹל | נֹבֵל |
| 2 | נבט | regarder | look at | 70 | נָבַט | יִבֹּט | נְבֹט | נְבֹט | נֹבֵט |
| 3 | נשׁך | payer des intérêts | bite | 12 | נָשַׁך | יִשֹּׁך | נְשֹׁך | נְשֹׁך | נֹשֵׁך |
| 4 | נשׁק | embrasser | kiss | 33 | נָשַׁק | יִשֹּׁק | נְשֹׁק | נְשֹׁק | נֹשֵׁק |
| 5 | נדב | Nadab | incite | 23 | נָדַב | יִדֹּב | נְדֹב | נְדֹב | נֹדֵב |
| 6 | נדף | chasser | scatter | 10 | נָדַף | יִדֹּף | נְדֹף | נְדֹף | נֹדֵף |
| 7 | נדר | vœu | vow | 32 | נָדַר | יִדֹּר | נְדֹר | נְדֹר | נֹדֵר |
| 8 | נשׂג | rattraper | overtake | 50 | נָשַׂג | יִשֹּׂג | נְשֹׂג | נְשֹׂג | נֹשֵׂג |
| 9 | נגשׁ | s’approcher | approach | 126 | נָגַשׁ | יִגֹּשׁ | נְגֹשׁ | נְגֹשׁ | נֹגֵשׁ |
| 10 | נגד | dire | report | 373 | נָגַד | יִגֹּד | נְגֹד | נְגֹד | נֹגֵד |
| 11 | נגשׂ | s’approcher | drive | 24 | נָגַשׂ | יִגֹּשׂ | נְגֹשׂ | נְגֹשׂ | נֹגֵשׂ |
| 12 | נגן | jouer | play harp | 16 | נָגַן | יִגֹּן | נְגֹן | נְגֹן | נֹגֵן |
| 13 | נגף | frapper | hurt | 50 | נָגַף | יִגֹּף | נְגֹף | נְגֹף | נֹגֵף |
| 14 | נגר | verser | run | 11 | נָגַר | יִגֹּר | נְגֹר | נְגֹר | נֹגֵר |
| 15 | נכר | reconnaître | recognise | 50 | נָכַר | יִכֹּר | נְכֹר | נְכֹר | נֹכֵר |
| 16 | נפל | tomber | fall | 447 | נָפַל | יִפֹּל | נְפֹל | נְפֹל | נֹפֵל |
| 17 | נפק | sorti | go out | 12 | נָפַק | יִפֹּק | נְפֹק | נְפֹק | נֹפֵק |
| 18 | נפץ | fracasser | shatter | 22 | נָפַץ | יִפֹּץ | נְפֹץ | נְפֹץ | נֹפֵץ |
| 19 | נקב | percer | bore | 20 | נָקַב | יִקֹּב | נְקֹב | נְקֹב | נֹקֵב |
| 20 | נקם | venger | avenge | 36 | נָקַם | יִקֹּם | נְקֹם | נְקֹם | נֹקֵם |
| 21 | נקף | entourer | go around | 18 | נָקַף | יִקֹּף | נְקֹף | נְקֹף | נֹקֵף |
| 22 | נסך | libations | pour | 28 | נָסַך | יִסֹּך | נְסֹך | נְסֹך | נֹסֵך |
| 23 | נתשׁ | déraciner | root out | 22 | נָתַשׁ | יִתֹּשׁ | נְתֹשׁ | נְתֹשׁ | נֹתֵשׁ |
| 24 | נתך | fondus | pour | 22 | נָתַך | יִתֹּך | נְתֹך | נְתֹך | נֹתֵך |
| 25 | נתן | donner | give | 2019 | נָתַן | יִתֹּן | נְתֹן | נְתֹן | נֹתֵן |
| 26 | נתק | rompit | pull off | 28 | נָתַק | יִתֹּק | נְתֹק | נְתֹק | נֹתֵק |
| 27 | נתר | sauter | drop | 11 | נָתַר | יִתֹּר | נְתֹר | נְתֹר | נֹתֵר |
| 28 | נתץ | démolir | break | 43 | נָתַץ | יִתֹּץ | נְתֹץ | נְתֹץ | נֹתֵץ |
| 29 | נטשׁ | laisser | abandon | 41 | נָטַשׁ | יִטֹּשׁ | נְטֹשׁ | נְטֹשׁ | נֹטֵשׁ |
| 30 | נטף | dégoutter/prophétiser | drop | 19 | נָטַף | יִטֹּף | נְטֹף | נְטֹף | נֹטֵף |
| 31 | נצב | se tenir debout | stand | 75 | נָצַב | יִצֹּב | נְצֹב | נְצֹב | נֹצֵב |
| 32 | נצל | délivrer | deliver | 218 | נָצַל | יִצֹּל | נְצֹל | נְצֹל | נֹצֵל |
| 33 | נצר | veiller | watch | 63 | נָצַר | יִצֹּר | נְצֹר | נְצֹר | נֹצֵר |
| 34 | נזל | couler | flow | 16 | נָזַל | יִזֹּל | נְזֹל | נְזֹל | נֹזֵל |
| 35 | נזר | couronne | dedicate | 11 | נָזַר | יִזֹּר | נְזֹר | נְזֹר | נֹזֵר |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `pe_nun`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
