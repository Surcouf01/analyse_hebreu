# Les verbes verbes doubles (ע״ע) — liste et règles de conjugaison

Un **verbe double** (ע״ע) est un verbe dont la **2ᵉ et la 3ᵉ radicales sont identiques** : סבב « entourer », חלם « rêver », קץ n'est pas trilitère... Les deux dernières radicales se comportent comme une seule : au qal imparfait la 3ᵉ radicale s'assimile à la 2ᵉ, d'où le daguesh fort.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **46** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `double`).

## Règles générales de conjugaison (qal)

1. **Redoublement apparent.** Au qal imparfait, aux volitifs et à l'impératif, la 3ᵉ radicale s'assimile à la 2ᵉ avec daguesh fort : יָסֹב « il entourera », תָּסֹב ; wayyiqtol וַיָּסָב ; impératif סֹב « tourne ! », סֹבִי, סֹבּוּ.
2. **Parfait régulier.** Le parfait qal garde les deux radicales : סָבַב, סָבְבָה, סָבַבְתָּ, סָבָבְתִּי, סָבָבוּ.
3. **Infinitifs et participes.** Infinitif construit : סוֹב (forme courte) ou סֹוב ; participe : סָבֵב, סָבְבִים (le pl. révèle les deux radicales).
4. **Hifil et autres binyanim.** Au hifil, les deux radicales se séparent à nouveau : הֵסֵב « il fit tourner » ; piel סִבֵּב « il entoura ».
5. **Verbes fréquents.** סבב « entourer » (162), הלל « louer » (147, avec ה initial), חלל « profaner » (135), רעע « briser » (107), קלל « maudire » (83), פלל « juger, prier » (81). La catégorie correspond aux « ayin-ayin » de la grammaire classique.

## Exemple de conjugaison complète : סבב « entourer » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | סָבַב |
| Parfait | 3 | f. sg. | סָבָה |
| Parfait | 2 | m. sg. | סַבֹּותָ |
| Parfait | 2 | f. sg. | סָבַבְתְּ |
| Parfait | 1 | c. sg. | סַבֹּתִי |
| Parfait | 3 | m. pl. | סַבּוּ |
| Imparfait | 3 | m. sg. | יָסֹב |
| Imparfait | 3 | f. sg. | תִּסְבַּב |
| Imparfait | 2 | m. sg. | תָּסֹב |
| Imparfait | 2 | f. sg. | תִסְבְּבִי |
| Imparfait | 1 | c. sg. | אֶסְבֹב |
| Imparfait | 3 | m. pl. | יָסֹבּוּ |
| Jussif | 3 | m. sg. | יָּסָב |
| Impératif | 2 | m. sg. | סֹב |
| Impératif | 2 | f. sg. | סֹבִּי |
| Impératif | 2 | m. pl. | סֹבּוּ |
| Infinitif construit | — | — | סֹב |
| Infinitif absolu | — | — | סָבֹוב |
| Participe actif | — | m. sg. | סֹבֵב |

## Les 46 verbes verbes doubles (ע״ע) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `double` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | עלל | moquée | deal with | 35 | עָלַל | יָעֹל | עֹל | עֹל | עֹלֵל |
| 2 | עזז | être fort | be strong | 11 | עָזַז | יָעֹז | עֹז | עֹז | עֹזֵז |
| 3 | ארר | maudire | curse | 64 | אָרַר | יָאֹר | אֹר | אֹר | אֹרֵר |
| 4 | בלל | mélanger | moisten, confound | 45 | בָלַל | יָבֹל | בֹל | בֹל | בֹלֵל |
| 5 | בקק | vider | lay waste | 10 | בָקַק | יָבֹק | בֹק | בֹק | בֹקֵק |
| 6 | ברר | purifier | purge | 17 | בָרַר | יָבֹר | בֹר | בֹר | בֹרֵר |
| 7 | בזז | piller | spoil | 44 | בָזַז | יָבֹז | בֹז | בֹז | בֹזֵז |
| 8 | שׁדד | dévaster | despoil | 59 | שָׁדַד | יָשֹׁד | שֹׁד | שֹׁד | שֹׁדֵד |
| 9 | שׁלל | butin | plunder | 15 | שָׁלַל | יָשֹׁל | שֹׁל | שֹׁל | שֹׁלֵל |
| 10 | שׁחח | se courber | bow down | 19 | שָׁחַח | יָשֹׁח | שֹׁח | שֹׁח | שֹׁחֵח |
| 11 | דקק | réduisit | crush | 24 | דָקַק | יָדֹק | דֹק | דֹק | דֹקֵק |
| 12 | גדד | couper | cut down | 12 | גָדַד | יָגֹד | גֹד | גֹד | גֹדֵד |
| 13 | גלל | rouler | roll | 18 | גָלַל | יָגֹל | גֹל | גֹל | גֹלֵל |
| 14 | גזז | tondeurs | shear | 16 | גָזַז | יָגֹז | גֹז | גֹז | גֹזֵז |
| 15 | הלל | louer | be infatuated | 16 | הָלַל | יָהֹל | הֹל | הֹל | הֹלֵל |
| 16 | הלל | louer | praise | 147 | הָלַל | יָהֹל | הֹל | הֹל | הֹלֵל |
| 17 | ילל | se lamenter | howl | 31 | יָלַל | יָיֹל | יֹל | יֹל | יֹלֵל |
| 18 | כהה | s’obscurcir | grow dim | 10 | כָהַה | יָכֹה | כֹה | כֹה | כֹהֵה |
| 19 | כלל | achevée | finish | 12 | כָלַל | יָכֹל | כֹל | כֹל | כֹלֵל |
| 20 | כתת | écraser | crush | 18 | כָתַת | יָכֹת | כֹת | כֹת | כֹתֵת |
| 21 | משׁשׁ | fouilla | grope | 11 | מָשַׁשׁ | יָמֹשׁ | מֹשׁ | מֹשׁ | מֹשֵׁשׁ |
| 22 | מדד | mesurer | measure | 54 | מָדַד | יָמֹד | מֹד | מֹד | מֹדֵד |
| 23 | מהה | tardait | tarry | 10 | מָהַה | יָמֹה | מֹה | מֹה | מֹהֵה |
| 24 | מלל | dit | speak | 12 | מָלַל | יָמֹל | מֹל | מֹל | מֹלֵל |
| 25 | מקק | pourrir | putrefy | 11 | מָקַק | יָמֹק | מֹק | מֹק | מֹקֵק |
| 26 | מרר | provoquer | be bitter | 18 | מָרַר | יָמֹר | מֹר | מֹר | מֹרֵר |
| 27 | מסס | fondre | melt | 22 | מָסַס | יָמֹס | מֹס | מֹס | מֹסֵס |
| 28 | נדד | errer | flee | 30 | נָדַד | יָנֹד | נֹד | נֹד | נֹדֵד |
| 29 | פלל | prier | pray | 81 | פָלַל | יָפֹל | פֹל | פֹל | פֹלֵל |
| 30 | פרר | briser | break | 47 | פָרַר | יָפֹר | פֹר | פֹר | פֹרֵר |
| 31 | קבב | maudire | curse | 15 | קָבַב | יָקֹב | קֹב | קֹב | קֹבֵב |
| 32 | קדד | se prosterner | kneel down | 16 | קָדַד | יָקֹד | קֹד | קֹד | קֹדֵד |
| 33 | קלל | alléger | be slight | 83 | קָלַל | יָקֹל | קֹל | קֹל | קֹלֵל |
| 34 | רעע | être mauvais | be evil | 107 | רָעַע | יָרֹע | רֹע | רֹע | רֹעֵע |
| 35 | רבב | multiplier | be much | 24 | רָבַב | יָרֹב | רֹב | רֹב | רֹבֵב |
| 36 | סבב | entourer | turn | 162 | סָבַב | יָסֹב | סֹב | סֹב | סֹבֵב |
| 37 | סלל | bâtir | build | 13 | סָלַל | יָסֹל | סֹל | סֹל | סֹלֵל |
| 38 | סרר | se rebeller | rebel | 18 | סָרַר | יָסֹר | סֹר | סֹר | סֹרֵר |
| 39 | תלל | tromper | mock | 10 | תָלַל | יָתֹל | תֹל | תֹל | תֹלֵל |
| 40 | חגג | célébrer | jump | 17 | חָגַג | יָחֹג | חֹג | חֹג | חֹגֵג |
| 41 | חלל | profaner | defile | 135 | חָלַל | יָחֹל | חֹל | חֹל | חֹלֵל |
| 42 | חקק | décréter | engrave | 20 | חָקַק | יָחֹק | חֹק | חֹק | חֹקֵק |
| 43 | חתת | être consterné | be terrified | 55 | חָתַת | יָחֹת | חֹת | חֹת | חֹתֵת |
| 44 | צרר | tourmenter | be hostile | 29 | צָרַר | יָצֹר | צֹר | צֹר | צֹרֵר |
| 45 | צרר | tourmenter | wrap, be narrow | 44 | צָרַר | יָצֹר | צֹר | צֹר | צֹרֵר |
| 46 | זלל | secouer | be lavish | 12 | זָלַל | יָזֹל | זֹל | זֹל | זֹלֵל |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `double`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
