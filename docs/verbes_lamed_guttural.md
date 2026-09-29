# Les verbes lamed-guttural (ל״ג) — liste et règles de conjugaison

Un **verbe lamed-guttural** (ל״ג) est un verbe dont la **3ᵉ radicale est une gutturale** (א, ה, ח, ע) : שׁלח « envoyer », שׁמע n'est pas ל״ג, לקח « prendre », שׁמע... Les formes réelles prennent un patah furtif sous la gutturale finale et des voyelles de compensation.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **69** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `lamed_guttural`).

## Règles générales de conjugaison (qal)

1. **Patah furtif.** Après une voyelle non-pathah, un patah furtif s'insère devant la gutturale finale (surtout avec ח/ע) : שָׁמֵחַ « joyeux », נָכֹחַ ; au parfait, la gutturale porte pathah : שָׁלַח, יָדַע.
2. **Voyelles de compensation.** La gutturale finale refuse le sheva : לָקַחְתְּ, שָׁלְחִי (impératif f. avec hatef), לְשַׁלֵּחַ (piel infinitif avec pathah final) ; sérées compensatoires fréquentes.
3. **Parfait.** שָׁלַח, שָׁלְחָה, שָׁלַחְתָּ, שָׁלַחְתִּי, שָׁלְחוּ.
4. **Imparfait.** יִשְׁלַח, תִּשְׁלַח (pathah sous la gutturale) ; wayyiqtol וַיִּשְׁלַח ; impératif שְׁלַח « envoie ! », שִׁלְחִי, שִׁלְחוּ.
5. **Verbes fréquents.** שָׁמַע « entendre » est ע״ג (2ᵉ radicale gutturale), pas ל״ג ; les lamed-gutturaux fréquents : שׁמע « entendre » (1170 occ.), ידע « connaître » (993, ע final), לקח « prendre » (966, ח final), שׁלח « envoyer » (863, ח final), ישׁע « sauver » (206), שׁבע « jurer » (186).

## Exemple de conjugaison complète : שׁלח « envoyer » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | שָׁלַח |
| Parfait | 3 | f. sg. | שָׁלְחָה |
| Parfait | 2 | m. sg. | שָׁלַחְתָּ |
| Parfait | 2 | f. sg. | שָׁלַחַתְּ |
| Parfait | 1 | c. sg. | שָׁלַחְתִּי |
| Parfait | 3 | m. pl. | שָׁלְחוּ |
| Imparfait | 3 | m. sg. | יִשְׁלַח |
| Imparfait | 3 | f. sg. | תִּשְׁלַח |
| Imparfait | 2 | m. sg. | תִּשְׁלַח |
| Imparfait | 2 | f. sg. | תִּשְׁלְחִי |
| Imparfait | 1 | c. sg. | אֶשְׁלַח |
| Imparfait | 3 | m. pl. | יִשְׁלְחוּ |
| Jussif | 3 | m. sg. | יִּשְׁלַח |
| Impératif | 2 | m. sg. | שְׁלַח |
| Impératif | 2 | f. sg. | שִׁלְחִי |
| Impératif | 2 | m. pl. | שִׁלְחוּ |
| Infinitif construit | — | — | שְׁלֹחַ |
| Infinitif absolu | — | — | שָׁלֹחַ |
| Participe actif | — | m. sg. | שֹׁלֵחַ |

## Les 69 verbes lamed-guttural (ל״ג) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `lamed_guttural` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | אנח | soupirer | gasp | 13 | אָנַח | יִאְנַח | אְנַח | אְנֹחַ | אֹנֵחַ |
| 2 | בלע | engloutir | swallow | 42 | בָלַע | יִבְלַע | בְלַע | בְלֹעַ | בֹלֵעַ |
| 3 | בקע | ouvrir | split | 52 | בָקַע | יִבְקַע | בְקַע | בְקֹעַ | בֹקֵעַ |
| 4 | ברח | fuir | run away | 66 | בָרַח | יִבְרַח | בְרַח | בְרֹחַ | בֹרֵחַ |
| 5 | בטח | se confier | trust | 119 | בָטַח | יִבְטַח | בְטַח | בְטֹחַ | בֹטֵחַ |
| 6 | בצע | gain injuste | cut off | 18 | בָצַע | יִבְצַע | בְצַע | בְצֹעַ | בֹצֵעַ |
| 7 | שׁבע | sept | swear | 186 | שָׁבַע | יִשְׁבַע | שְׁבַע | שְׁבֹעַ | שֹׁבֵעַ |
| 8 | שׁבח | apaiser | praise | 15 | שָׁבַח | יִשְׁבַח | שְׁבַח | שְׁבֹחַ | שֹׁבֵחַ |
| 9 | שׁכח | oublier | find | 124 | שָׁכַח | יִשְׁכַח | שְׁכַח | שְׁכֹחַ | שֹׁכֵחַ |
| 10 | שׁלח | envoyer | send | 863 | שָׁלַח | יִשְׁלַח | שְׁלַח | שְׁלֹחַ | שֹׁלֵחַ |
| 11 | שׁמע | entendre | hear | 1170 | שָׁמַע | יִשְׁמַע | שְׁמַע | שְׁמֹעַ | שֹׁמֵעַ |
| 12 | שׁסע | fendre | cleave | 10 | שָׁסַע | יִשְׁסַע | שְׁסַע | שְׁסֹעַ | שֹׁסֵעַ |
| 13 | שׁוע | crier | cry | 22 | שָׁוַע | יִשְׁוַע | שְׁוַע | שְׁוֹעַ | שֹׁוֵעַ |
| 14 | שׂבע | sept | be sated | 98 | שָׂבַע | יִשְׂבַע | שְׂבַע | שְׂבֹעַ | שֹׂבֵעַ |
| 15 | שׂיח | méditer | be concerned with | 21 | שָׂיַח | יִשְׂיַח | שְׂיַח | שְׂיֹחַ | שֹׂיֵחַ |
| 16 | שׂמח | se réjouir | rejoice | 155 | שָׂמַח | יִשְׂמַח | שְׂמַח | שְׂמֹחַ | שֹׂמֵחַ |
| 17 | גדע | couper, retrancher | cut off | 23 | גָדַע | יִגְדַע | גְדַע | גְדֹעַ | גֹדֵעַ |
| 18 | גלח | rasera | shave | 24 | גָלַח | יִגְלַח | גְלַח | גְלֹחַ | גֹלֵחַ |
| 19 | גרע | diminuer | clip | 23 | גָרַע | יִגְרַע | גְרַע | גְרֹעַ | גֹרֵעַ |
| 20 | גוע | mourir | expire | 25 | גָוַע | יִגְוַע | גְוַע | גְוֹעַ | גֹוֵעַ |
| 21 | ישׁע | sauver | help | 206 | יָשַׁע | יִיְשַׁע | יְשַׁע | יְשֹׁעַ | יֹשֵׁעַ |
| 22 | ידע | connaître | know | 993 | יָדַע | יִיְדַע | יְדַע | יְדֹעַ | יֹדֵעַ |
| 23 | יגע | se fatiguer, peiner | be weary | 27 | יָגַע | יִיְגַע | יְגַע | יְגֹעַ | יֹגֵעַ |
| 24 | יכח | réprimander | reprove | 60 | יָכַח | יִיְכַח | יְכַח | יְכֹחַ | יֹכֵחַ |
| 25 | כנע | s’humilier | be humble | 37 | כָנַע | יִכְנַע | כְנַע | כְנֹעַ | כֹנֵעַ |
| 26 | כרע | s'incliner | kneel | 37 | כָרַע | יִכְרַע | כְרַע | כְרֹעַ | כֹרֵעַ |
| 27 | לקח | prendre | take | 966 | לָקַח | יִלְקַח | לְקַח | לְקֹחַ | לֹקֵחַ |
| 28 | משׁח | oindre | smear | 70 | מָשַׁח | יִמְשַׁח | מְשַׁח | מְשֹׁחַ | מֹשֵׁחַ |
| 29 | מנע | retenir | withhold | 30 | מָנַע | יִמְנַע | מְנַע | מְנֹעַ | מֹנֵעַ |
| 30 | נבע | bouillonner | bubble | 12 | נָבַע | יִנְבַע | נְבַע | נְבֹעַ | נֹבֵעַ |
| 31 | נדח | bannir | wield | 55 | נָדַח | יִנְדַח | נְדַח | נְדֹחַ | נֹדֵחַ |
| 32 | נגע | toucher | touch | 151 | נָגַע | יִנְגַע | נְגַע | נְגֹעַ | נֹגֵעַ |
| 33 | נגח | encorner | gore | 12 | נָגַח | יִנְגַח | נְגַח | נְגֹחַ | נֹגֵחַ |
| 34 | נפח | respirer | blow | 13 | נָפַח | יִנְפַח | נְפַח | נְפֹחַ | נֹפֵחַ |
| 35 | נסע | se mettre en route | pull out | 147 | נָסַע | יִנְסַע | נְסַע | נְסֹעַ | נֹסֵעַ |
| 36 | נתח | morceaux | cut | 10 | נָתַח | יִנְתַח | נְתַח | נְתֹחַ | נֹתֵחַ |
| 37 | נטע | planter | plant | 59 | נָטַע | יִנְטַע | נְטַע | נְטֹעַ | נֹטֵעַ |
| 38 | נוע | secouer | quiver | 41 | נָוַע | יִנְוַע | נְוַע | נְוֹעַ | נֹוֵעַ |
| 39 | נוח | se reposer | settle | 142 | נָוַח | יִנְוַח | נְוַח | נְוֹחַ | נֹוֵחַ |
| 40 | נצח | diriger | prevail | 68 | נָצַח | יִנְצַח | נְצַח | נְצֹחַ | נֹצֵחַ |
| 41 | פשׁע | transgression | rebel | 42 | פָשַׁע | יִפְשַׁע | פְשַׁע | פְשֹׁעַ | פֹשֵׁעַ |
| 42 | פגע | tomber sur | meet | 47 | פָגַע | יִפְגַע | פְגַע | פְגֹעַ | פֹגֵעַ |
| 43 | פלח | servir | serve | 17 | פָלַח | יִפְלַח | פְלַח | פְלֹחַ | פֹלֵחַ |
| 44 | פקח | ouvre | open | 21 | פָקַח | יִפְקַח | פְקַח | פְקֹחַ | פֹקֵחַ |
| 45 | פרע | désordre | let loose | 17 | פָרַע | יִפְרַע | פְרַע | פְרֹעַ | פֹרֵעַ |
| 46 | פרח | bourgeonner | sprout | 35 | פָרַח | יִפְרַח | פְרַח | פְרֹחַ | פֹרֵחַ |
| 47 | פתח | entrée | engrave | 10 | פָתַח | יִפְתַח | פְתַח | פְתֹחַ | פֹתֵחַ |
| 48 | פתח | entrée | open | 139 | פָתַח | יִפְתַח | פְתַח | פְתֹחַ | פֹתֵחַ |
| 49 | פוח | respirer | wheeze | 12 | פָוַח | יִפְוַח | פְוַח | פְוֹחַ | פֹוֵחַ |
| 50 | קרע | déchirer | tear | 64 | קָרַע | יִקְרַע | קְרַע | קְרֹעַ | קֹרֵעַ |
| 51 | רבע | carré | be square | 13 | רָבַע | יִרְבַע | רְבַע | רְבֹעַ | רֹבֵעַ |
| 52 | רשׁע | méchant | be guilty | 35 | רָשַׁע | יִרְשַׁע | רְשַׁע | רְשֹׁעַ | רֹשֵׁעַ |
| 53 | רגע | instant | stir | 14 | רָגַע | יִרְגַע | רְגַע | רְגֹעַ | רֹגֵעַ |
| 54 | רקע | battre | stamp | 12 | רָקַע | יִרְקַע | רְקַע | רְקֹעַ | רֹקֵעַ |
| 55 | רוע | crier | shout | 45 | רָוַע | יִרְוַע | רְוַע | רְוֹעַ | רֹוֵעַ |
| 56 | רוח | esprit | be spacious | 15 | רָוַח | יִרְוַח | רְוַח | רְוֹחַ | רֹוֵחַ |
| 57 | רצח | assassiner | kill | 48 | רָצַח | יִרְצַח | רְצַח | רְצֹחַ | רֹצֵחַ |
| 58 | סלח | pardonner | forgive | 47 | סָלַח | יִסְלַח | סְלַח | סְלֹחַ | סֹלֵחַ |
| 59 | תקע | souffler | blow | 68 | תָקַע | יִתְקַע | תְקַע | תְקֹעַ | תֹקֵעַ |
| 60 | טבע | s'enfoncer | sink | 11 | טָבַע | יִטְבַע | טְבַע | טְבֹעַ | טֹבֵעַ |
| 61 | טבח | gardes | slaughter | 12 | טָבַח | יִטְבַח | טְבַח | טְבֹחַ | טֹבֵחַ |
| 62 | טוח | revêtir | plaster | 12 | טָוַח | יִטְוַח | טְוַח | טְוֹחַ | טֹוֵחַ |
| 63 | צלח | prospérer | be strong | 71 | צָלַח | יִצְלַח | צְלַח | צְלֹחַ | צֹלֵחַ |
| 64 | צמח | germer | sprout | 34 | צָמַח | יִצְמַח | צְמַח | צְמֹחַ | צֹמֵחַ |
| 65 | צרע | lépreux | have skin-disease | 21 | צָרַע | יִצְרַע | צְרַע | צְרֹעַ | צֹרֵעַ |
| 66 | זבח | sacrifice | slaughter | 135 | זָבַח | יִזְבַח | זְבַח | זְבֹחַ | זֹבֵחַ |
| 67 | זנח | rejeter | reject | 20 | זָנַח | יִזְנַח | זְנַח | זְנֹחַ | זֹנֵחַ |
| 68 | זרע | semence | sow | 57 | זָרַע | יִזְרַע | זְרַע | זְרֹעַ | זֹרֵעַ |
| 69 | זרח | Zérach | flash up | 19 | זָרַח | יִזְרַח | זְרַח | זְרֹחַ | זֹרֵחַ |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `lamed_guttural`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
