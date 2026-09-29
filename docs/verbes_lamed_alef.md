# Les verbes lamed-alef (ל״א) — liste et règles de conjugaison

Un **verbe lamed-alef** (ל״א) est un verbe dont la **3ᵉ radicale est un א** : מצא « trouver », בוא « venir », קרא « appeler, lire ». L'alef final quiescent s'élide en syllabe ouverte, ce qui allonge la voyelle précédente.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **23** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `lamed_alef`).

## Règles générales de conjugaison (qal)

1. **Alef final quiescent.** L'alef ne se prononce qu'avec voyelle : en finale de mot il quiesce et la voyelle précédente s'allonge — מָצָא, קָרָא ; à l'imparfait, l'alef se maintient avec sa voyelle : יִמְצָא, יִקְרָא (pathah/qamets sous la 2ᵉ radicale).
2. **Parfait.** Formes pleines : מָצָא, מָצְאָה, מָצָאתָ (2ᵉ m., tsere+alef), מָצָאתִי ; pl. מָצְאוּ.
3. **Imparfait et volitifs.** יִמְצָא, תִּמְצָא ; jussif identique ; wayyiqtol וַיִּמְצָא ; impératif מְצָא « trouve ! », מִצְאִי, מִצְאוּ (l'alef s'entend après voyelle brève).
4. **Verbes fréquents.** בוא « venir » (2571 occ. — aussi ע״ו, mais l'alef final prime dans `classify_root`), יצא « sortir » (1071, aussi pe-yod), קרא « appeler » (745), נשׂא « porter » (658, aussi pe-nun), מצא « trouver » (454), ירא « craindre » (333, aussi ע״א).
5. **Cumul.** Un lamed-alef peut être aussi ע״ו (בוא), pe-yod (ישׁע), pe-alef (אמר n'est pas ל״א)… la priorité `classify_root` place `lamed_alef` avant `ayin_vav`, ce qui fait que בוא figure ici et non dans les verbes creux.

## Exemple de conjugaison complète : מצא « trouver » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | מָצָא |
| Parfait | 3 | f. sg. | מָצְאָה |
| Parfait | 2 | m. sg. | מָצָאתָ |
| Parfait | 2 | f. sg. | מָצָאת |
| Parfait | 1 | c. sg. | מָצָאתִי |
| Parfait | 3 | m. pl. | מָצְאוּ |
| Imparfait | 3 | m. sg. | יִמְצָא |
| Imparfait | 3 | f. sg. | תִּמְצָא |
| Imparfait | 2 | m. sg. | תִמְצָא |
| Imparfait | 2 | f. sg. | תִמְצְאִי |
| Imparfait | 1 | c. sg. | אֶמְצָא |
| Imparfait | 3 | m. pl. | יִמְצְאוּ |
| Jussif | 3 | m. sg. | יִּמְצָא |
| Impératif | 2 | m. sg. | מְצָא |
| Impératif | 2 | f. sg. | מִצְאִי |
| Impératif | 2 | m. pl. | מִצְאוּ |
| Infinitif construit | — | — | מְצֹא |
| Infinitif absolu | — | — | מָצֹא |
| Participe actif | — | m. sg. | מֹצֵא |

## Les 23 verbes lamed-alef (ל״א) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `lamed_alef` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | ברא | créer | create | 49 | בָרָא | יִבְרָא | בְרָא | בְרֹא | בֹרֵא |
| 2 | בוא | venir (dans) | come | 2571 | בָוָא | יִבְוָא | בְוָא | בְוֹא | בֹוֵא |
| 3 | דכא | écraser | oppress | 19 | דָכָא | יִדְכָא | דְכָא | דְכֹא | דֹכֵא |
| 4 | שׂנא | haïr | hate | 149 | שָׂנָא | יִשְׂנָא | שְׂנָא | שְׂנֹא | שֹׂנֵא |
| 5 | ירא | craindre | fear | 333 | יָרָא | יִיְרָא | יְרָא | יְרֹא | יֹרֵא |
| 6 | יצא | sortir | go out | 1071 | יָצָא | יִיְצָא | יְצָא | יְצֹא | יֹצֵא |
| 7 | כלא | retenir | restrain | 18 | כָלָא | יִכְלָא | כְלָא | כְלֹא | כֹלֵא |
| 8 | מלא | remplir | be full | 296 | מָלָא | יִמְלָא | מְלָא | מְלֹא | מֹלֵא |
| 9 | מצא | trouver | find | 454 | מָצָא | יִמְצָא | מְצָא | מְצֹא | מֹצֵא |
| 10 | נבא | prophétiser | speak as prophet | 118 | נָבָא | יִנְבָא | נְבָא | נְבֹא | נֹבֵא |
| 11 | נשׁא | élever | beguile | 17 | נָשָׁא | יִנְשָׁא | נְשָׁא | נְשֹׁא | נֹשֵׁא |
| 12 | נשׁא | élever | give loan | 20 | נָשָׁא | יִנְשָׁא | נְשָׁא | נְשֹׁא | נֹשֵׁא |
| 13 | נשׂא | élever | lift | 658 | נָשָׂא | יִנְשָׂא | נְשָׂא | נְשֹׂא | נֹשֵׂא |
| 14 | פלא | s’étonner | be miraculous | 74 | פָלָא | יִפְלָא | פְלָא | פְלֹא | פֹלֵא |
| 15 | קנא | être jaloux | be jealous | 35 | קָנָא | יִקְנָא | קְנָא | קְנֹא | קֹנֵא |
| 16 | קרא | appeler | encounter | 141 | קָרָא | יִקְרָא | קְרָא | קְרֹא | קֹרֵא |
| 17 | קרא | appeler | call | 745 | קָרָא | יִקְרָא | קְרָא | קְרֹא | קֹרֵא |
| 18 | רפא | guérir | heal | 66 | רָפָא | יִרְפָא | רְפָא | רְפֹא | רֹפֵא |
| 19 | טמא | impur | be unclean | 163 | טָמָא | יִטְמָא | טְמָא | טְמֹא | טֹמֵא |
| 20 | חבא | caché | hide | 35 | חָבָא | יִחְבָא | חְבָא | חְבֹא | חֹבֵא |
| 21 | חטא | pécher | miss | 238 | חָטָא | יִחְטָא | חְטָא | חְטֹא | חֹטֵא |
| 22 | צבא | Armées | serve | 14 | צָבָא | יִצְבָא | צְבָא | צְבֹא | צֹבֵא |
| 23 | צמא | soif | be thirsty | 11 | צָמָא | יִצְמָא | צְמָא | צְמֹא | צֹמֵא |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `lamed_alef`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
