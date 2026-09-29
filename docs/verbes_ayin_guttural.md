# Les verbes ayin-guttural (ע״ג) — liste et règles de conjugaison

Un **verbe ayin-guttural** (ע״ג) est un verbe dont la **2ᵉ radicale est une gutturale** (א, ה, ח, ע) : שׁמע « entendre », אהב « aimer », בחר « choisir ». La gutturale médiane refuse le sheva et le daguesh fort, et attire les voyelles de timbre a.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **78** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `ayin_guttural`).

## Règles générales de conjugaison (qal)

1. **Refus du sheva.** La 2ᵉ radicale gutturale ne porte pas de sheva : שָׁמְעוּ (3ᵉ pl. parfait, voyelle de compensation qamets-hatef) ; à l'imparfait la gutturale ouvre la syllabe : יִשְׁמַע (voyelle pathah, pas de daguesh).
2. **Refus du daguesh fort.** Au piel/pual où le verbe fort redouble la 2ᵉ radicale, la gutturale refuse le daguesh et la voyelle précédente s'allonge en compensation : ex. le hifil de שׁאל : הִשְׁאִיל « il a prêté » (sans daguesh sur א) ; le piel de בדר/בדל allonge la voyelle du préfixe.
3. **Attirance des voyelles a.** Les formes préfèrent pathah/hatef-patah autour de la gutturale : שָׁמַע, יִשְׁמַע, שְׁמַע, שָׁמְעָה ; אָהַב, יֶאֱהַב (hifil avec hatef), בָּחַר, יִבְחַר.
4. **Parfait 3ᵉ fém. et pl..** Devant תָ/וּ, la gutturale prend une hatef de compensation : שָׁמְעָה, שָׁמְעוּ ; l'impératif 2ᵉ f. pl. שְׁמַעְנָה.
5. **Verbes fréquents.** אהב « aimer » (212), שׁאל « demander » (179), לחם « combattre » (172), בחר « choisir » (170), שׁחת « détruire » (150), שׁאר « rester » (134). À noter : שׁמע « entendre » (1170 occ.) est classé `lamed_guttural` (l'ע final prime sur la gutturale médiane).

## Exemple de conjugaison complète : שׁמע « entendre » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | שָׁמַע |
| Parfait | 3 | f. sg. | שָׁמֲעָה |
| Parfait | 2 | m. sg. | שָׁמַעְתָּ |
| Parfait | 2 | f. sg. | שָׁמַעְתְּ |
| Parfait | 1 | c. sg. | שָׁמַעְתִּי |
| Parfait | 3 | m. pl. | שָׁמֲעוּ |
| Imparfait | 3 | m. sg. | יִשְׁמַע |
| Imparfait | 3 | f. sg. | תִּשְׁמַע |
| Imparfait | 2 | m. sg. | תִּשְׁמַע |
| Imparfait | 2 | f. sg. | תִשְׁמְעִי |
| Imparfait | 1 | c. sg. | אֶשְׁמַע |
| Imparfait | 3 | m. pl. | יִשְׁמֲעוּ |
| Jussif | 3 | m. sg. | יִּשְׁמַע |
| Impératif | 2 | m. sg. | שְׁמַע |
| Impératif | 2 | f. sg. | שַֽׁמֲעִי |
| Impératif | 2 | m. pl. | שַׁמֲעוּ |
| Infinitif construit | — | — | שְׁמֹע |
| Infinitif absolu | — | — | שָׁמֹע |
| Participe actif | — | m. sg. | שֹׁמֵע |

## Les 78 verbes ayin-guttural (ע״ג) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `ayin_guttural` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | אהב | aimer | love | 212 | אָהַב | יִאְהַב | אְהַב | אְהֹב | אֹהֵב |
| 2 | אחר | après | be behind | 18 | אָחַר | יִאְחַר | אְחַר | אְחֹר | אֹחֵר |
| 3 | אחז | saisir | seize | 66 | אָחַז | יִאְחַז | אְחַז | אְחֹז | אֹחֵז |
| 4 | בעל | maître | own | 17 | בָעַל | יִבְעַל | בְעַל | בְעֹל | בֹעֵל |
| 5 | בער | brûler | burn | 88 | בָעַר | יִבְעַר | בְעַר | בְעֹר | בֹעֵר |
| 6 | בעת | terrifier | terrify | 17 | בָעַת | יִבְעַת | בְעַת | בְעֹת | בֹעֵת |
| 7 | באשׁ | puer | stink | 20 | בָאַשׁ | יִבְאַשׁ | בְאַשׁ | בְאֹשׁ | בֹאֵשׁ |
| 8 | בהל | consterner | disturb | 52 | בָהַל | יִבְהַל | בְהַל | בְהֹל | בֹהֵל |
| 9 | בחן | éprouver | examine | 30 | בָחַן | יִבְחַן | בְחַן | בְחֹן | בֹחֵן |
| 10 | בחר | choisir | examine | 170 | בָחַר | יִבְחַר | בְחַר | בְחֹר | בֹחֵר |
| 11 | שׁען | s’appuyer | lean | 23 | שָׁעַן | יִשְׁעַן | שְׁעַן | שְׁעֹן | שֹׁעֵן |
| 12 | שׁאב | puiser | draw water | 20 | שָׁאַב | יִשְׁאַב | שְׁאַב | שְׁאֹב | שֹׁאֵב |
| 13 | שׁאג | rugir | roar | 21 | שָׁאַג | יִשְׁאַג | שְׁאַג | שְׁאֹג | שֹׁאֵג |
| 14 | שׁאל | demander | ask | 179 | שָׁאַל | יִשְׁאַל | שְׁאַל | שְׁאֹל | שֹׁאֵל |
| 15 | שׁאף | écraser | gasp | 15 | שָׁאַף | יִשְׁאַף | שְׁאַף | שְׁאֹף | שֹׁאֵף |
| 16 | שׁאר | rester | remain | 134 | שָׁאַר | יִשְׁאַר | שְׁאַר | שְׁאֹר | שֹׁאֵר |
| 17 | שׁחר | aube | look for | 14 | שָׁחַר | יִשְׁחַר | שְׁחַר | שְׁחֹר | שֹׁחֵר |
| 18 | שׁחת | ruiner | destroy | 150 | שָׁחַת | יִשְׁחַת | שְׁחַת | שְׁחֹת | שֹׁחֵת |
| 19 | שׁחט | abattre | slaughter | 81 | שָׁחַט | יִשְׁחַט | שְׁחַט | שְׁחֹט | שֹׁחֵט |
| 20 | דעך | éteindra | be extinguished | 10 | דָעַך | יִדְעַך | דְעַך | דְעֹך | דֹעֵך |
| 21 | שׂחק | rire | laugh | 37 | שָׂחַק | יִשְׂחַק | שְׂחַק | שְׂחֹק | שֹׂחֵק |
| 22 | געשׁ | secouer | shake | 10 | גָעַשׁ | יִגְעַשׁ | גְעַשׁ | גְעֹשׁ | גֹעֵשׁ |
| 23 | געל | horreur | abhor | 11 | גָעַל | יִגְעַל | גְעַל | גְעֹל | גֹעֵל |
| 24 | גער | réprimander | rebuke | 15 | גָעַר | יִגְעַר | גְעַר | גְעֹר | גֹעֵר |
| 25 | גאל | racheter | pollute | 12 | גָאַל | יִגְאַל | גְאַל | גְאֹל | גֹאֵל |
| 26 | גאל | racheter | redeem | 104 | גָאַל | יִגְאַל | גְאַל | גְאֹל | גֹאֵל |
| 27 | יעד | désigner | appoint | 30 | יָעַד | יִיְעַד | יְעַד | יְעֹד | יֹעֵד |
| 28 | יעל | profit | profit | 24 | יָעַל | יִיְעַל | יְעַל | יְעֹל | יֹעֵל |
| 29 | יעף | fatiguent | be weary | 10 | יָעַף | יִיְעַף | יְעַף | יְעֹף | יֹעֵף |
| 30 | יעץ | conseiller | advise | 81 | יָעַץ | יִיְעַץ | יְעַץ | יְעֹץ | יֹעֵץ |
| 31 | יאל | osé | begin | 20 | יָאַל | יִיְאַל | יְאַל | יְאֹל | יֹאֵל |
| 32 | יהב | donner | give | 64 | יָהַב | יִיְהַב | יְהַב | יְהֹב | יֹהֵב |
| 33 | יחשׂ | généalogies | register | 21 | יָחַשׂ | יִיְחַשׂ | יְחַשׂ | יְחֹשׂ | יֹחֵשׂ |
| 34 | יחל | attendre | wait, to hope | 42 | יָחַל | יִיְחַל | יְחַל | יְחֹל | יֹחֵל |
| 35 | כעס | provoquer | be discontent | 55 | כָעַס | יִכְעַס | כְעַס | כְעֹס | כֹעֵס |
| 36 | כהן | prêtre | act as priest | 24 | כָהַן | יִכְהַן | כְהַן | כְהֹן | כֹהֵן |
| 37 | כחשׁ | tromper | grow lean | 23 | כָחַשׁ | יִכְחַשׁ | כְחַשׁ | כְחֹשׁ | כֹחֵשׁ |
| 38 | כחד | cacher | hide | 33 | כָחַד | יִכְחַד | כְחַד | כְחֹד | כֹחֵד |
| 39 | לעג | se moquer | mock | 19 | לָעַג | יִלְעַג | לְעַג | לְעֹג | לֹעֵג |
| 40 | להט | embraser | devour | 12 | לָהַט | יִלְהַט | לְהַט | לְהֹט | לֹהֵט |
| 41 | לחם | pain | fight | 172 | לָחַם | יִלְחַם | לְחַם | לְחֹם | לֹחֵם |
| 42 | לחץ | opprimer | press | 20 | לָחַץ | יִלְחַץ | לְחַץ | לְחֹץ | לֹחֵץ |
| 43 | מעל | au-dessus | be unfaithful | 37 | מָעַל | יִמְעַל | מְעַל | מְעֹל | מֹעֵל |
| 44 | מעט | peu | be little | 23 | מָעַט | יִמְעַט | מְעַט | מְעֹט | מֹעֵט |
| 45 | מאן | refuser | refuse | 47 | מָאַן | יִמְאַן | מְאַן | מְאֹן | מֹאֵן |
| 46 | מאס | rejeter | reject | 76 | מָאַס | יִמְאַס | מְאַס | מְאֹס | מֹאֵס |
| 47 | מהר | se hâter | hasten | 82 | מָהַר | יִמְהַר | מְהַר | מְהֹר | מֹהֵר |
| 48 | מחץ | blesser | break | 15 | מָחַץ | יִמְחַץ | מְחַץ | מְחֹץ | מֹחֵץ |
| 49 | נער | jeune homme | shake off | 12 | נָעַר | יִנְעַר | נְעַר | נְעֹר | נֹעֵר |
| 50 | נאף | commettre l’adultère | commit adultery | 32 | נָאַף | יִנְאַף | נְאַף | נְאֹף | נֹאֵף |
| 51 | נאץ | méprisé | contemn | 25 | נָאַץ | יִנְאַץ | נְאַץ | נְאֹץ | נֹאֵץ |
| 52 | נהג | conduire | drive | 31 | נָהַג | יִנְהַג | נְהַג | נְהֹג | נֹהֵג |
| 53 | נהל | guider | lead | 11 | נָהַל | יִנְהַל | נְהַל | נְהֹל | נֹהֵל |
| 54 | נחשׁ | serpent | divine | 12 | נָחַשׁ | יִנְחַשׁ | נְחַשׁ | נְחֹשׁ | נֹחֵשׁ |
| 55 | נחל | torrent | take possession | 60 | נָחַל | יִנְחַל | נְחַל | נְחֹל | נֹחֵל |
| 56 | נחם | se désoler, consoler | repent, console | 109 | נָחַם | יִנְחַם | נְחַם | נְחֹם | נֹחֵם |
| 57 | נחת | descendre | come down | 16 | נָחַת | יִנְחַת | נְחַת | נְחֹת | נֹחֵת |
| 58 | פעל | travailler | make | 58 | פָעַל | יִפְעַל | פְעַל | פְעֹל | פֹעֵל |
| 59 | פאר | embellir | glorify | 14 | פָאַר | יִפְאַר | פְאַר | פְאֹר | פֹאֵר |
| 60 | פחד | effroi | tremble | 26 | פָחַד | יִפְחַד | פְחַד | פְחֹד | פֹחֵד |
| 61 | קהל | assemblée | assemble | 40 | קָהַל | יִקְהַל | קְהַל | קְהֹל | קֹהֵל |
| 62 | רעב | famine | be hungry | 14 | רָעַב | יִרְעַב | רְעַב | רְעֹב | רֹעֵב |
| 63 | רעשׁ | secouer | quake | 30 | רָעַשׁ | יִרְעַשׁ | רְעַשׁ | רְעֹשׁ | רֹעֵשׁ |
| 64 | רעם | tonner | thunder | 12 | רָעַם | יִרְעַם | רְעַם | רְעֹם | רֹעֵם |
| 65 | רחב | largeur | be wide | 26 | רָחַב | יִרְחַב | רְחַב | רְחֹב | רֹחֵב |
| 66 | רחם | avoir compassion | have compassion | 46 | רָחַם | יִרְחַם | רְחַם | רְחֹם | רֹחֵם |
| 67 | רחק | lointain | be far | 58 | רָחַק | יִרְחַק | רְחַק | רְחֹק | רֹחֵק |
| 68 | רחץ | laver | wash | 75 | רָחַץ | יִרְחַץ | רְחַץ | רְחֹץ | רֹחֵץ |
| 69 | סעד | soutenir | support | 15 | סָעַד | יִסְעַד | סְעַד | סְעֹד | סֹעֵד |
| 70 | סחר | commercer | go about | 22 | סָחַר | יִסְחַר | סְחַר | סְחֹר | סֹחֵר |
| 71 | תעב | avoir en horreur | be abhorrent | 23 | תָעַב | יִתְעַב | תְעַב | תְעֹב | תֹעֵב |
| 72 | טעם | commandement | eat | 16 | טָעַם | יִטְעַם | טְעַם | טְעֹם | טֹעֵם |
| 73 | טהר | être pur | be clean | 95 | טָהַר | יִטְהַר | טְהַר | טְהֹר | טֹהֵר |
| 74 | צעק | crier | cry | 56 | צָעַק | יִצְעַק | צְעַק | צְעֹק | צֹעֵק |
| 75 | צחק | ri | laugh | 14 | צָחַק | יִצְחַק | צְחַק | צְחֹק | צֹחֵק |
| 76 | זעם | indignation | curse | 13 | זָעַם | יִזְעַם | זְעַם | זְעֹם | זֹעֵם |
| 77 | זעק | crier | cry | 76 | זָעַק | יִזְעַק | זְעַק | זְעֹק | זֹעֵק |
| 78 | זהר | avertir | warn | 22 | זָהַר | יִזְהַר | זְהַר | זְהֹר | זֹהֵר |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `ayin_guttural`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
