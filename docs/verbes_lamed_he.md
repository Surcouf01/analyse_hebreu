# Les verbes lamed-he (ל״ה) — liste et règles de conjugaison

Un **verbe lamed-he** (ל״ה) est un verbe dont la **3ᵉ radicale est un ה** *mater lectionis* : בנה « bâtir », עשׂה « faire », היה « être », מצא « trouver ». Le ה n'est pas une consonne pleine : selon la terminaison, il s'élide, se contracte ou se convertit.

La base morphologique **BHSA** (branche `data2021`, features `lex`/`sp`) recense **179 lexèmes verbaux lamed-he** ; **93** d'entre eux sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `lamed_he`).

## Règles générales de conjugaison (qal)

1. **Terminaison vocalique.** Le ה final est une *mater lectionis* : les formes conjuguées se terminent par une voyelle longue ou une terminaison vocalique (ה, ת, י, וּ) — בָּנָה « il a bâti », תִּבְנֶה « elle bâtira ».
2. **Élision du ה aux formes à suffixe.** Dès qu'un suffixe s'ajoute (terminaison de personne ou suffixe pronominal), le ה s'élide et les voyelles se contractent : בָּנָה + תִּי → בָּנִיתִי « j'ai bâti » (jamais *בָּנָהְתִי) ; בְּנֹות + וֹ → בְּנֹתוֹ « en le bâtissant ».
3. **Parfait.** 3ᵉ m. sg. בָּנָה ; 3ᵉ f. sg. בָּנְתָה (élision du ה devant תָה) ; 2ᵉ m. sg. בָּנִיתָ ; 1ʳᵉ c. sg. בָּנִיתִי ; 3ᵉ pl. בָּנוּ (contraction ה + וּ → וּ).
4. **Imparfait (yiqtol).** Voyelle caractéristique **sere** (ֵ) devant le ה final : יִבְנֶה, תִּבְנֶה. Devant une terminaison en sheva, le ה s'élide avec contraction en **hireq + yod** : תִּבְנִי « tu bâtiras » ; 3ᵉ pl. יִבְנוּ ; 3ᵉ f. pl. תִּבְנֶינָה.
5. **Jussif (forme courte).** Le jussif élide le ה avec sa voyelle : יִּבֶן « qu'il bâtisse » (wayyiqtol וַיִּבֶן). Certains verbes ont un jussif court distinctif : היה → יְהִי.
6. **Cohortatif.** Le ה paragogique s'agglutine à une forme déjà vocalique : אֶבְנֶה « que je bâtisse », נִבְנֶה « bâtissons ».
7. **Impératif.** Construit sur l'imparfait sans préfixe : 2ᵉ m. sg. בְּנֵה (tsere, syllabe ouverte après élision du ה) ; 2ᵉ f. sg. בְּנִי ; 2ᵉ m. pl. בְּנוּ ; 2ᵉ f. pl. בְּנֹינָה.
8. **Infinitif construit.** Le ה final devient **ֹות** (holam + waw) : בְּנֹות « bâtir ». L'infinitif absolu garde la forme longue : בָּנֹה.
9. **Participe.** Actif : בֹּנֶה (m. sg.), בֹּנִים (m. pl.), בֹּנָה (f. sg.), בֹּנֹות (f. pl.). Passif qal : בָּנוּי « bâti ».
10. **Cumul avec d'autres faiblesses.** Un lamed-he peut cumuler une autre faiblesse radicale : pe-guttural (ענה « répondre », אהב « aimer » : refus du sheva, hatef-voyelle de compensation) ; pe-alef (אבה « consentir ») ; 2ᵉ radicale gutturale (voyelles de compensation, pas de daguesh fort). La catégorie racine reste `lamed_he` dans `classify_root` (le ה prime, sauf racine « double »).
11. **Verbes quasi-réguliers et exceptions.** La plupart des lamed-he sont réguliers ; les verbes « mixtes » (ל״ה + gutturale : שׂרה, ראה ; à 2ᵉ radicale faible : שׂים « placer », בנה reste régulier) présentent des variantes vocaliques. Le tableau ci-dessous donne les formes générées par les gabarits BHSA dominants ; pour quelques verbes, la forme attestée majoritaire peut différer légèrement.

## Exemple de conjugaison complète : בנה « bâtir » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | בָּנָה |
| Parfait | 3 | f. sg. | בָּנְתָה |
| Parfait | 2 | m. sg. | בָּנִיתָ |
| Parfait | 2 | f. sg. | בָּנִיתְּ |
| Parfait | 1 | c. sg. | בָּנִיתִי |
| Parfait | 3 | m. pl. | בָּנוּ |
| Imparfait | 3 | m. sg. | יִבְנֶה |
| Imparfait | 3 | f. sg. | תִּבְנֶה |
| Imparfait | 2 | m. sg. | תִּבְנֶה |
| Imparfait | 2 | f. sg. | תִּבְנִי |
| Imparfait | 1 | c. sg. | אֶבְנֶה |
| Imparfait | 3 | m. pl. | יִבְנוּ |
| Imparfait | 3 | f. pl. | תִּבְנֶינָה |
| Jussif | 3 | m. sg. | יִּבֶן |
| Cohortatif | 1 | c. sg. | אֶבְנֶה |
| Impératif | 2 | m. sg. | בְּנֵה |
| Impératif | 2 | f. sg. | בְּנִי |
| Impératif | 2 | m. pl. | בְּנוּ |
| Impératif | 2 | f. pl. | בְּנֹינָה |
| Infinitif construit | — | — | בְּנֹות |
| Infinitif absolu | — | — | בָּנֹה |
| Participe actif | — | m. sg. | בֹּנֶה |
| Participe passif | — | m. sg. | בָּנוּי |

## Les 93 verbes lamed-he attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `lamed_he` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | עדה | assemblée | go | 19 | עָדָה | יִעְדֶה | עְדֵה | עְדֹות | עֹדֶה |
| 2 | עשׂה | agir | make | 2630 | עָשָׂה | יִעְשֶׂה | עְשֵׂה | עְשֹׂות | עֹשֶׂה |
| 3 | עלה | monter | ascend | 891 | עָלָה | יִעְלֶה | עְלֵה | עְלֹות | עֹלֶה |
| 4 | ענה | répondre | answer | 348 | עָנָה | יִעְנֶה | עְנֵה | עְנֹות | עֹנֶה |
| 5 | ערה | vider | pour out | 16 | עָרָה | יִעְרֶה | עְרֵה | עְרֹות | עֹרֶה |
| 6 | עטה | envelopper | cover | 14 | עָטָה | יִעְטֶה | עְטֵה | עְטֹות | עֹטֶה |
| 7 | עוה | pervertir | do wrong | 18 | עָוָה | יִעְוֶה | עְוֵה | עְוֹות | עֹוֶה |
| 8 | אבה | être disposé | want | 55 | אָבָה | יִאְבֶה | אְבֵה | אְבֹות | אֹבֶה |
| 9 | אפה | cuire au four | bake | 14 | אָפָה | יִאְפֶה | אְפֵה | אְפֹות | אֹפֶה |
| 10 | אתה | tu / toi (m.) | come | 39 | אָתָה | יִאְתֶה | אְתֵה | אְתֹות | אֹתֶה |
| 11 | אוה | désirer | wish | 28 | אָוָה | יִאְוֶה | אְוֵה | אְוֹות | אֹוֶה |
| 12 | בעה | s’enquérir | seek | 19 | בָעָה | יִבְעֶה | בְעֵה | בְעֹות | בֹעֶה |
| 13 | בכה | pleurer | weep | 115 | בָכָה | יִבְכֶה | בְכֵה | בְכֹות | בֹכֶה |
| 14 | בלה | devenir vieux | be worn out | 18 | בָלָה | יִבְלֶה | בְלֵה | בְלֹות | בֹלֶה |
| 15 | בנה | bâtir | build | 400 | בָנָה | יִבְנֶה | בְנֵה | בְנֹות | בֹנֶה |
| 16 | בזה | mépriser | despise | 44 | בָזָה | יִבְזֶה | בְזֵה | בְזֹות | בֹזֶה |
| 17 | שׁעה | regarder fixement | look | 16 | שָׁעָה | יִשְׁעֶה | שְׁעֵה | שְׁעֹות | שֹׁעֶה |
| 18 | שׁבה | emmener en captivité | take captive | 48 | שָׁבָה | יִשְׁבֶה | שְׁבֵה | שְׁבֹות | שֹׁבֶה |
| 19 | שׁגה | égarer | err | 22 | שָׁגָה | יִשְׁגֶה | שְׁגֵה | שְׁגֹות | שֹׁגֶה |
| 20 | שׁנה | année | change | 48 | שָׁנָה | יִשְׁנֶה | שְׁנֵה | שְׁנֹות | שֹׁנֶה |
| 21 | שׁקה | boire | give drink | 69 | שָׁקָה | יִשְׁקֶה | שְׁקֵה | שְׁקֹות | שֹׁקֶה |
| 22 | שׁרה | Sara | loosen | 10 | שָׁרָה | יִשְׁרֶה | שְׁרֵה | שְׁרֹות | שֹׁרֶה |
| 23 | שׁסה | piller | spoil | 11 | שָׁסָה | יִשְׁסֶה | שְׁסֵה | שְׁסֹות | שֹׁסֶה |
| 24 | שׁתה | boire | drink | 224 | שָׁתָה | יִשְׁתֶה | שְׁתֵה | שְׁתֹות | שֹׁתֶה |
| 25 | שׁוה | placer | be equal | 20 | שָׁוָה | יִשְׁוֶה | שְׁוֵה | שְׁוֹות | שֹׁוֶה |
| 26 | דמה | ressembler | resemble | 33 | דָמָה | יִדְמֶה | דְמֵה | דְמֹות | דֹמֶה |
| 27 | גבה | élevé | be high | 35 | גָבָה | יִגְבֶה | גְבֵה | גְבֹות | גֹבֶה |
| 28 | גלה | découvrir | uncover | 199 | גָלָה | יִגְלֶה | גְלֵה | גְלֹות | גֹלֶה |
| 29 | גרה | excite | stir | 15 | גָרָה | יִגְרֶה | גְרֵה | גְרֹות | גֹרֶה |
| 30 | הגה | murmurer | mutter | 26 | הָגָה | יִהְגֶה | הְגֵה | הְגֹות | הֹגֶה |
| 31 | היה | être | be | 3562 | הָיָה | יִהְיֶה | הְיֵה | הְיֹות | הֹיֶה |
| 32 | המה | ils | make noise | 35 | הָמָה | יִהְמֶה | הְמֵה | הְמֹות | הֹמֶה |
| 33 | הרה | concevoir | be pregnant | 44 | הָרָה | יִהְרֶה | הְרֵה | הְרֹות | הֹרֶה |
| 34 | הוה | désir | become | 78 | הָוָה | יִהְוֶה | הְוֵה | הְוֹות | הֹוֶה |
| 35 | ידה | rendre grâce | praise | 115 | יָדָה | יִיְדֶה | יְדֵה | יְדֹות | יֹדֶה |
| 36 | ינה | opprimer | oppress | 20 | יָנָה | יִיְנֶה | יְנֵה | יְנֹות | יֹנֶה |
| 37 | ירה | montrer | teach | 47 | יָרָה | יִיְרֶה | יְרֵה | יְרֹות | יֹרֶה |
| 38 | כבה | éteindre | go out | 25 | כָבָה | יִכְבֶה | כְבֵה | כְבֹות | כֹבֶה |
| 39 | כהה | s’obscurcir | grow dim | 10 | כָהַה | יָכֹה | כֹה | כֹה | כֹהֵה |
| 40 | כלה | détruire | be complete | 207 | כָלָה | יִכְלֶה | כְלֵה | כְלֹות | כֹלֶה |
| 41 | כרה | percer | dig | 17 | כָרָה | יִכְרֶה | כְרֵה | כְרֹות | כֹרֶה |
| 42 | כסה | couvrir | cover | 153 | כָסָה | יִכְסֶה | כְסֵה | כְסֹות | כֹסֶה |
| 43 | לאה | Léa | be weary | 20 | לָאָה | יִלְאֶה | לְאֵה | לְאֹות | לֹאֶה |
| 44 | לוה | joindre | accompany | 13 | לָוָה | יִלְוֶה | לְוֵה | לְוֹות | לֹוֶה |
| 45 | מהה | tardait | tarry | 10 | מָהַה | יָמֹה | מֹה | מֹה | מֹהֵה |
| 46 | מנה | compter | count | 35 | מָנָה | יִמְנֶה | מְנֵה | מְנֹות | מֹנֶה |
| 47 | מרה | se rebeller | rebel | 46 | מָרָה | יִמְרֶה | מְרֵה | מְרֹות | מֹרֶה |
| 48 | מחה | essuyer | wipe | 35 | מָחָה | יִמְחֶה | מְחֵה | מְחֹות | מֹחֶה |
| 49 | נכה | frapper | strike | 501 | נָכָה | יִנְכֶה | נְכֵה | נְכֹות | נֹכֶה |
| 50 | נקה | être pur | be clean | 45 | נָקָה | יִנְקֶה | נְקֵה | נְקֹות | נֹקֶה |
| 51 | נסה | éprouver | try | 37 | נָסָה | יִנְסֶה | נְסֵה | נְסֹות | נֹסֶה |
| 52 | נטה | étendre | extend | 215 | נָטָה | יִנְטֶה | נְטֵה | נְטֹות | נֹטֶה |
| 53 | נחה | conduire | lead | 40 | נָחָה | יִנְחֶה | נְחֵה | נְחֹות | נֹחֶה |
| 54 | נצה | lutter | decay | 14 | נָצָה | יִנְצֶה | נְצֵה | נְצֹות | נֹצֶה |
| 55 | נזה | asperger | spatter | 25 | נָזָה | יִנְזֶה | נְזֵה | נְזֹות | נֹזֶה |
| 56 | פדה | racheter | buy off | 59 | פָדָה | יִפְדֶה | פְדֵה | פְדֹות | פֹדֶה |
| 57 | פשׂה | étendue | spread | 23 | פָשָׂה | יִפְשֶׂה | פְשֵׂה | פְשֹׂות | פֹשֶׂה |
| 58 | פנה | devant | turn | 136 | פָנָה | יִפְנֶה | פְנֵה | פְנֹות | פֹנֶה |
| 59 | פרה | être fécond | be fertile | 28 | פָרָה | יִפְרֶה | פְרֵה | פְרֹות | פֹרֶה |
| 60 | פתה | séduire | seduce | 28 | פָתָה | יִפְתֶה | פְתֵה | פְתֹות | פֹתֶה |
| 61 | פצה | ouvrir | open | 16 | פָצָה | יִפְצֶה | פְצֵה | פְצֹות | פֹצֶה |
| 62 | קשׁה | dur | be hard | 29 | קָשָׁה | יִקְשֶׁה | קְשֵׁה | קְשֹׁות | קֹשֶׁה |
| 63 | קנה | acheter | buy | 81 | קָנָה | יִקְנֶה | קְנֵה | קְנֹות | קֹנֶה |
| 64 | קרה | arrivé | meet | 28 | קָרָה | יִקְרֶה | קְרֵה | קְרֹות | קֹרֶה |
| 65 | קוה | attendre | wait for | 47 | קָוָה | יִקְוֶה | קְוֵה | קְוֹות | קֹוֶה |
| 66 | רעה | faire paître | pasture | 169 | רָעָה | יִרְעֶה | רְעֵה | רְעֹות | רֹעֶה |
| 67 | ראה | voir | see | 1299 | רָאָה | יִרְאֶה | רְאֵה | רְאֹות | רֹאֶה |
| 68 | רבה | multiplier | be many | 232 | רָבָה | יִרְבֶה | רְבֵה | רְבֹות | רֹבֶה |
| 69 | רדה | dominer | tread, to rule | 26 | רָדָה | יִרְדֶה | רְדֵה | רְדֹות | רֹדֶה |
| 70 | רמה | Rama | throw | 18 | רָמָה | יִרְמֶה | רְמֵה | רְמֹות | רֹמֶה |
| 71 | רפה | se relâcher | be slack | 49 | רָפָה | יִרְפֶה | רְפֵה | רְפֹות | רֹפֶה |
| 72 | רוה | désaltérer | drink | 15 | רָוָה | יִרְוֶה | רְוֵה | רְוֹות | רֹוֶה |
| 73 | רצה | accepter | like | 50 | רָצָה | יִרְצֶה | רְצֵה | רְצֹות | רֹצֶה |
| 74 | ספה | emporter | sweep away | 19 | סָפָה | יִסְפֶה | סְפֵה | סְפֹות | סֹפֶה |
| 75 | תעה | s’égarer | err | 51 | תָעָה | יִתְעֶה | תְעֵה | תְעֹות | תֹעֶה |
| 76 | תלה | pendu | hang | 28 | תָלָה | יִתְלֶה | תְלֵה | תְלֹות | תֹלֶה |
| 77 | תמה | être stupéfait | be astounded | 10 | תָמָה | יִתְמֶה | תְמֵה | תְמֹות | תֹמֶה |
| 78 | חשׁה | se taire | be silent | 17 | חָשָׁה | יִחְשֶׁה | חְשֵׁה | חְשֹׁות | חֹשֶׁה |
| 79 | חיה | vivre | be alive | 291 | חָיָה | יִחְיֶה | חְיֵה | חְיֹות | חֹיֶה |
| 80 | חכה | attendre | wait | 15 | חָכָה | יִחְכֶה | חְכֵה | חְכֹות | חֹכֶה |
| 81 | חלה | être affligé | become weak | 76 | חָלָה | יִחְלֶה | חְלֵה | חְלֹות | חֹלֶה |
| 82 | חנה | camper | encamp | 144 | חָנָה | יִחְנֶה | חְנֵה | חְנֹות | חֹנֶה |
| 83 | חפה | couvrir | cover | 13 | חָפָה | יִחְפֶה | חְפֵה | חְפֹות | חֹפֶה |
| 84 | חרה | s’irriter | be hot | 93 | חָרָה | יִחְרֶה | חְרֵה | חְרֹות | חֹרֶה |
| 85 | חסה | chercher refuge | seek refuge | 38 | חָסָה | יִחְסֶה | חְסֵה | חְסֹות | חֹסֶה |
| 86 | חוה | montrer | bow down | 187 | חָוָה | יִחְוֶה | חְוֵה | חְוֹות | חֹוֶה |
| 87 | חצה | diviser | divide | 16 | חָצָה | יִחְצֶה | חְצֵה | חְצֹות | חֹצֶה |
| 88 | חזה | voir | see | 87 | חָזָה | יִחְזֶה | חְזֵה | חְזֹות | חֹזֶה |
| 89 | צבה | enfler | desire | 14 | צָבָה | יִצְבֶה | צְבֵה | צְבֹות | צֹבֶה |
| 90 | צפה | couvrit | look out | 38 | צָפָה | יִצְפֶה | צְפֵה | צְפֹות | צֹפֶה |
| 91 | צוה | commander | command | 495 | צָוָה | יִצְוֶה | צְוֵה | צְוֹות | צֹוֶה |
| 92 | זנה | forniquer | fornicate | 94 | זָנָה | יִזְנֶה | זְנֵה | זְנֹות | זֹנֶה |
| 93 | זרה | disperser | scatter | 41 | זָרָה | יִזְרֶה | זְרֵה | זְרֹות | זֹרֶה |

## Remarques

- Le seuil de 10 occurrences écarte 86 lexèmes rares (hapax ou quasi-hapax) ; le comptage complet (179 lexèmes) peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` et un lexème terminé par `H[`.
- Les formes générées sont celles du gabarit dominant attesté ; pour un verbe donné, le mode « Binyanim » de l'application affiche le paradigme complet (tous les binyanim, tous les temps), avec les mêmes gabarits.
- Les autres binyanim suivent le même principe d'élision/contraction du ה (ex. hifil de מצא : הִמְצִיא ; piel de כלה : כִּלָּה).
