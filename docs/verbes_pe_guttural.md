# Les verbes pe-gutturaux (פ״ג) — liste et règles de conjugaison

Un **verbe pe-guttural** (פ״ע/פ״ח/פ״ה/פ״א) est un verbe dont la **1ʳᵉ radicale est une gutturale** (א, ע, ה, ח) : הלך « marcher », עבר « passer », חזק « être fort ». La gutturale refuse le sheva et ne prend pas de daguesh fort : la conjugaison s'adapte par des voyelles brèves de compensation (hatef).

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense **183 lexèmes verbaux pe-gutturaux** (1ʳᵉ radicale ה/ח/ע) ; **77** d'entre eux sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `pe_guttural`).

## Règles générales de conjugaison (qal)

1. **Refus du sheva.** La gutturale initiale ne peut pas porter de sheva simple : après un préfixe (יִ, תִּ, נִ, אֶ), le sheva attendu devient une **hatef** (hatef-patah ײֲ le plus souvent, hatef-sere ױֱ ou hatef-qamats ׳ֳ selon la voyelle suivante) — יַעֲבֹד « il servira », non *יַעְבֹד.
2. **Refus du daguesh fort.** La gutturale ne se redouble pas : dans les binyanim à redoublement (piel, pual), la 2ᵉ radicale porte le daguesh et la gutturale initiale reçoit une voyelle de compensation ; au qal, le prétéritif à daguesh (יִקְטֹל → יִפֹּל pour pe-nun) n'existe pas ici — la gutturale garde sa voyelle.
3. **Voyelle de préfixe allongée.** Dans de nombreuses formes à préfixe, la voyelle du préfixe s'allonge ou change (pathah au lieu de hireq dans certains imperfecta : יַעֲבֹד ; au hifil, le préfixe prend souvent pathah : הֶחֱזִיק, יַעֲמִיד « il fera tenir »).
4. **Préférence pour les voyelles a.** Les gutturales favorisent les voyelles de timbre **a** (pathah/hatef-patah) : parfait עָבַד, imparfait יַעֲבֹד, impératif עֲבֹד, infinitif construit לַעֲבֹד (préfixe לְ → לַ devant sheva composé), participe עֹבֵד.
5. **Parfait régulier.** Le parfait est celui du verbe fort, seule la 2ᵉ syllabe peut prendre pathah au lieu de tsere dans quelques verbes : עָבַד, עָבַדְתָּ, עָבַדְתְּ, עָבַדְתִּי, עָבֵדָה (3ᵉ f.), עָבְדוּ.
6. **Imparfait.** 3ᵉ m. sg. יַעֲבֹד ; 3ᵉ f. sg. תַּעֲבֹד ; 2ᵉ m. sg. תַּעֲבֹד ; 2ᵉ f. sg. תַּעַבְדִי ; 1ʳᵉ c. sg. אֶעֱבֹד (hatef-sere) ; 3ᵉ m. pl. יַעֲבֹדוּ ; 3ᵉ f. pl. תַּעֲבֹדְנָה.
7. **Jussif et volitifs.** Le jussif suit l'imparfait (יַעֲבֹד) ; wayyiqtol : וַיַּעֲבֹד (pathah sous le waw conversif, daguesh dans le préfixe) ; cohortatif : אֶעֱבֹדָה.
8. **Impératif.** Construit sur l'imparfait sans préfixe : 2ᵉ m. sg. עֲבֹד (hatef-patah initial) ; 2ᵉ f. sg. עַבְדִי ; 2ᵉ m. pl. עַבְדוּ ; 2ᵉ f. pl. עַבְדְנָה.
9. **Infinitifs.** Infinitif construit : עֲבֹד (hatef initial ; avec préfixe לְ, le plus souvent לַעֲבֹד). Infinitif absolu : עָבֹד.
10. **Participe.** Actif m. sg. עֹבֵד (holam sur la gutturale) ; f. sg. עֹבֵדָה ; m. pl. עֹבְדִים ; f. pl. עֹבְדוֹת. Passif qal : עָבוּד.
11. **Cumul avec d'autres faiblesses.** Un pe-guttural peut être aussi ayin-guttural ou lamed-guttural/lamed-he (חנה « camper », חרה « brûler », עלה « monter » n'est pas pe-guttural au sens strict mais guttural initial ; חטא « manquer » est en réalité classé `lamed_alef`, l'alef final primant). La classification `classify_root` priorise : double > lamed_he > lamed_alef > lamed_guttural > ayin_vav > ayin_guttural > pe_nun > pe_alef > pe_yod > pe_guttural.
12. **Frontière avec le pe-alef.** La grammaire traditionnelle compte comme « gutturales et assimilées » **א ע ה ח ר** : les cinq refusent le daguesh fort et favorisent les voyelles a. Le project en distingue deux groupes dans `classify_root` : א forme une catégorie propre (`pe_alef` — quiescence : אמר « dire »), tandis que ה, ח, ע forment les `pe_guttural` proprement dits ; **ר** (רדף « poursuivre », רגז « trembler ») est traité comme un verbe **fort** (`GUTTURALS` dans `binyan_gen.py` ne comprend que א ה ח ע).

## Exemple de conjugaison complète : עבד « servir » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | עָבַד |
| Parfait | 3 | f. sg. | עָבַדָה |
| Parfait | 2 | m. sg. | עָבַדְתָּ |
| Parfait | 2 | f. sg. | עָבַדְתְּ |
| Parfait | 1 | c. sg. | עָבַדְתִּי |
| Parfait | 3 | m. pl. | עָבַדּוּ |
| Imparfait | 3 | m. sg. | יַעֲבֹד |
| Imparfait | 3 | f. sg. | תַּעֲבֹד |
| Imparfait | 2 | m. sg. | תַּעֲבֹד |
| Imparfait | 2 | f. sg. | תַּעַבְדִי |
| Imparfait | 1 | c. sg. | אֶעֱבֹד |
| Imparfait | 3 | m. pl. | יַעֲבֹדוּ |
| Imparfait | 3 | f. pl. | תַּעֲבֹדְנָה |
| Jussif | 3 | m. sg. | יַעֲבֹד |
| Cohortatif | 1 | c. sg. | אֶעֱבֹדָה |
| Impératif | 2 | m. sg. | עֲבֹד |
| Impératif | 2 | f. sg. | עַבְדִי |
| Impératif | 2 | m. pl. | עַבְדוּ |
| Impératif | 2 | f. pl. | עַבְדְנָה |
| Infinitif construit | — | — | עֲבֹד |
| Infinitif absolu | — | — | עָבֹד |
| Participe actif | — | m. sg. | עֹבֵד |

## Les 77 verbes pe-gutturaux attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `pe_guttural` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---|---|---|---|---|---|---|---|---|---|
| 1 | עבד | serviteur | work, serve | 318 | עָבַד | יַעֲבֹד | עֲבֹד | עֲבֹד | עֹבֵד |
| 2 | עבר | passer | pass | 549 | עָבַר | יַעֲבֹר | עֲבֹר | עֲבֹר | עֹבֵר |
| 3 | עשׁק | opprimer | oppress | 38 | עָשַׁק | יַעֲשֹׁק | עֲשֹׁק | עֲשֹׁק | עֹשֵׁק |
| 4 | עשׁר | dix | become rich | 18 | עָשַׁר | יַעֲשֹׁר | עֲשֹׁר | עֲשֹׁר | עֹשֵׁר |
| 5 | עדף | trop | remain | 10 | עָדַף | יַעֲדֹף | עֲדֹף | עֲדֹף | עֹדֵף |
| 6 | עשׂר | dix | take tenth | 10 | עָשַׂר | יַעֲשֹׂר | עֲשֹׂר | עֲשֹׂר | עֹשֵׂר |
| 7 | עכר | troubler | taboo | 15 | עָכַר | יַעֲכֹר | עֲכֹר | עֲכֹר | עֹכֵר |
| 8 | עלם | cacher | hide | 29 | עָלַם | יַעֲלֹם | עֲלֹם | עֲלֹם | עֹלֵם |
| 9 | עלז | exulter | rejoice | 17 | עָלַז | יַעֲלֹז | עֲלֹז | עֲלֹז | עֹלֵז |
| 10 | עמד | se tenir | stand | 522 | עָמַד | יַעֲמֹד | עֲמֹד | עֲמֹד | עֹמֵד |
| 11 | עמל | peine | labour | 12 | עָמַל | יַעֲמֹל | עֲמֹל | עֲמֹל | עֹמֵל |
| 12 | עמק | vallée | be deep | 10 | עָמַק | יַעֲמֹק | עֲמֹק | עֲמֹק | עֹמֵק |
| 13 | עמס | charger | load | 10 | עָמַס | יַעֲמֹס | עֲמֹס | עֲמֹס | עֹמֵס |
| 14 | ענג | délices | be dainty | 11 | עָנַג | יַעֲנֹג | עֲנֹג | עֲנֹג | עֹנֵג |
| 15 | ענן | nuage | appear | 12 | עָנַן | יַעֲנֹן | עֲנֹן | עֲנֹן | עֹנֵן |
| 16 | עקר | stérile | root up | 10 | עָקַר | יַעֲקֹר | עֲקֹר | עֲקֹר | עֹקֵר |
| 17 | ערב | soir | stand bail | 23 | עָרַב | יַעֲרֹב | עֲרֹב | עֲרֹב | עֹרֵב |
| 18 | ערך | disposer | arrange | 76 | עָרַך | יַעֲרֹך | עֲרֹך | עֲרֹך | עֹרֵך |
| 19 | ערץ | trembler | tremble | 16 | עָרַץ | יַעֲרֹץ | עֲרֹץ | עֲרֹץ | עֹרֵץ |
| 20 | עתק | avancer | advance | 10 | עָתַק | יַעֲתֹק | עֲתֹק | עֲתֹק | עֹתֵק |
| 21 | עתר | prier | entreat | 23 | עָתַר | יַעֲתֹר | עֲתֹר | עֲתֹר | עֹתֵר |
| 22 | עטף | être faible | faint | 12 | עָטַף | יַעֲטֹף | עֲטֹף | עֲטֹף | עֹטֵף |
| 23 | עצב | blesser | hurt | 16 | עָצַב | יַעֲצֹב | עֲצֹב | עֲצֹב | עֹצֵב |
| 24 | עצם | os | be mighty | 19 | עָצַם | יַעֲצֹם | עֲצֹם | עֲצֹם | עֹצֵם |
| 25 | עצר | retenir | restrain | 47 | עָצַר | יַעֲצֹר | עֲצֹר | עֲצֹר | עֹצֵר |
| 26 | עזב | quitter | leave | 215 | עָזַב | יַעֲזֹב | עֲזֹב | עֲזֹב | עֹזֵב |
| 27 | עזר | aider | help | 82 | עָזַר | יַעֲזֹר | עֲזֹר | עֲזֹר | עֹזֵר |
| 28 | הדף | repousser | push | 12 | הָדַף | יַהֲדֹף | הֲדֹף | הֲדֹף | הֹדֵף |
| 29 | הדר | gloire | honour | 11 | הָדַר | יַהֲדֹר | הֲדֹר | הֲדֹר | הֹדֵר |
| 30 | הלך | aller | walk | 1556 | הָלַך | יַהֲלֹך | הֲלֹך | הֲלֹך | הֹלֵך |
| 31 | המם | confondre | confuse | 14 | הָמַם | יַהֲמֹם | הֲמֹם | הֲמֹם | הֹמֵם |
| 32 | הפך | renverser | turn | 95 | הָפַך | יַהֲפֹך | הֲפֹך | הֲפֹך | הֹפֵך |
| 33 | הרג | tuer | kill | 168 | הָרַג | יַהֲרֹג | הֲרֹג | הֲרֹג | הֹרֵג |
| 34 | הרס | abattre | tear down | 44 | הָרַס | יַהֲרֹס | הֲרֹס | הֲרֹס | הֹרֵס |
| 35 | חבשׁ | seller/lier | saddle | 34 | חָבַשׁ | יַחֲבֹשׁ | חֲבֹשׁ | חֲבֹשׁ | חֹבֵשׁ |
| 36 | חבל | corde | be corrupt | 12 | חָבַל | יַחֲבֹל | חֲבֹל | חֲבֹל | חֹבֵל |
| 37 | חבל | corde | be harmful | 21 | חָבַל | יַחֲבֹל | חֲבֹל | חֲבֹל | חֹבֵל |
| 38 | חבק | embrassa | embrace | 14 | חָבַק | יַחֲבֹק | חֲבֹק | חֲבֹק | חֹבֵק |
| 39 | חבר | unir | be united | 29 | חָבַר | יַחֲבֹר | חֲבֹר | חֲבֹר | חֹבֵר |
| 40 | חשׁב | concevoir | account | 127 | חָשַׁב | יַחֲשֹׁב | חֲשֹׁב | חֲשֹׁב | חֹשֵׁב |
| 41 | חשׁך | ténèbres | be dark | 18 | חָשַׁך | יַחֲשֹׁך | חֲשֹׁך | חֲשֹׁך | חֹשֵׁך |
| 42 | חשׁק | attaché | love | 12 | חָשַׁק | יַחֲשֹׁק | חֲשֹׁק | חֲשֹׁק | חֹשֵׁק |
| 43 | חדשׁ | mois | be new | 11 | חָדַשׁ | יַחֲדֹשׁ | חֲדֹשׁ | חֲדֹשׁ | חֹדֵשׁ |
| 44 | חדל | cesser | cease | 59 | חָדַל | יַחֲדֹל | חֲדֹל | חֲדֹל | חֹדֵל |
| 45 | חשׂך | ténèbres | withhold | 29 | חָשַׂך | יַחֲשֹׂך | חֲשֹׂך | חֲשֹׂך | חֹשֵׂך |
| 46 | חשׂף | puiser | strip | 10 | חָשַׂף | יַחֲשֹׂף | חֲשֹׂף | חֲשֹׂף | חֹשֵׂף |
| 47 | חגר | ceindre | gird | 45 | חָגַר | יַחֲגֹר | חֲגֹר | חֲגֹר | חֹגֵר |
| 48 | חכם | sage | be wise | 28 | חָכַם | יַחֲכֹם | חֲכֹם | חֲכֹם | חֹכֵם |
| 49 | חלם | rêver | dream | 30 | חָלַם | יַחֲלֹם | חֲלֹם | חֲלֹם | חֹלֵם |
| 50 | חלף | passer | pass by | 32 | חָלַף | יַחֲלֹף | חֲלֹף | חֲלֹף | חֹלֵף |
| 51 | חלק | portion | be smooth | 10 | חָלַק | יַחֲלֹק | חֲלֹק | חֲלֹק | חֹלֵק |
| 52 | חלק | portion | divide | 57 | חָלַק | יַחֲלֹק | חֲלֹק | חֲלֹק | חֹלֵק |
| 53 | חלץ | délivrer | draw off | 45 | חָלַץ | יַחֲלֹץ | חֲלֹץ | חֲלֹץ | חֹלֵץ |
| 54 | חמד | désirer | desire | 22 | חָמַד | יַחֲמֹד | חֲמֹד | חֲמֹד | חֹמֵד |
| 55 | חמל | épargner | have compassion | 41 | חָמַל | יַחֲמֹל | חֲמֹל | חֲמֹל | חֹמֵל |
| 56 | חמם | réchauffer | be hot | 28 | חָמַם | יַחֲמֹם | חֲמֹם | חֲמֹם | חֹמֵם |
| 57 | חנן | faire grâce | favour | 81 | חָנַן | יַחֲנֹן | חֲנֹן | חֲנֹן | חֹנֵן |
| 58 | חנף | profane | alienate | 12 | חָנַף | יַחֲנֹף | חֲנֹף | חֲנֹף | חֹנֵף |
| 59 | חפשׂ | chercher | search | 24 | חָפַשׂ | יַחֲפֹשׂ | חֲפֹשׂ | חֲפֹשׂ | חֹפֵשׂ |
| 60 | חפר | chercher | dig | 24 | חָפַר | יַחֲפֹר | חֲפֹר | חֲפֹר | חֹפֵר |
| 61 | חפר | chercher | be ashamed | 18 | חָפַר | יַחֲפֹר | חֲפֹר | חֲפֹר | חֹפֵר |
| 62 | חפץ | prendre plaisir à | desire | 78 | חָפַץ | יַחֲפֹץ | חֲפֹץ | חֲפֹץ | חֹפֵץ |
| 63 | חפז | se hâter | hurry | 10 | חָפַז | יַחֲפֹז | חֲפֹז | חֲפֹז | חֹפֵז |
| 64 | חקר | rechercher | explore | 28 | חָקַר | יַחֲקֹר | חֲקֹר | חֲקֹר | חֹקֵר |
| 65 | חרב | épée | destroy | 39 | חָרַב | יַחֲרֹב | חֲרֹב | חֲרֹב | חֹרֵב |
| 66 | חרשׁ | se taire | plough | 28 | חָרַשׁ | יַחֲרֹשׁ | חֲרֹשׁ | חֲרֹשׁ | חֹרֵשׁ |
| 67 | חרשׁ | se taire | be deaf | 48 | חָרַשׁ | יַחֲרֹשׁ | חֲרֹשׁ | חֲרֹשׁ | חֹרֵשׁ |
| 68 | חרד | trembler | tremble | 40 | חָרַד | יַחֲרֹד | חֲרֹד | חֲרֹד | חֹרֵד |
| 69 | חרם | vouer/détruire | consecrate | 51 | חָרַם | יַחֲרֹם | חֲרֹם | חֲרֹם | חֹרֵם |
| 70 | חרף | railler | reproach | 39 | חָרַף | יַחֲרֹף | חֲרֹף | חֲרֹף | חֹרֵף |
| 71 | חרץ | remuera | cut off | 13 | חָרַץ | יַחֲרֹץ | חֲרֹץ | חֲרֹץ | חֹרֵץ |
| 72 | חסר | manquer | diminish | 25 | חָסַר | יַחֲסֹר | חֲסֹר | חֲסֹר | חֹסֵר |
| 73 | חתם | sceller | seal | 29 | חָתַם | יַחֲתֹם | חֲתֹם | חֲתֹם | חֹתֵם |
| 74 | חתן | beau-père | be father-in-law | 34 | חָתַן | יַחֲתֹן | חֲתֹן | חֲתֹן | חֹתֵן |
| 75 | חטב | couper | gather wood | 10 | חָטַב | יַחֲטֹב | חֲטֹב | חֲטֹב | חֹטֵב |
| 76 | חצב | tailler | hew | 26 | חָצַב | יַחֲצֹב | חֲצֹב | חֲצֹב | חֹצֵב |
| 77 | חזק | fortifier | be strong | 291 | חָזַק | יַחֲזֹק | חֲזֹק | חֲזֹק | חֹזֵק |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet (183 lexèmes) peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` et une 1ʳᵉ radicale ה/ח/ע (classification `classify_root` du projet).
- Le tableau n'inclut que les racines trilitaires classées `pe_guttural` (1ʳᵉ radicale ה/ח/ע, l'alef ayant sa catégorie propre) ; les verbes pe-gutturaux doubles ou lamed-he sont classés dans leur catégorie dominante (ex. חנה est `lamed_he`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
