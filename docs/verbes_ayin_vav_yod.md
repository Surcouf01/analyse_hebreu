# Les verbes creux ayin-waw et ayin-yod (ע״ו/ע״י) — liste et règles de conjugaison

Un **verbe creux** (*ʿayin-waw* ע״ו ou *ʿayin-yod* ע״י) est un verbe dont la **2ᵉ radicale est un ו ou un י consonantique** : שׁוּם « placer », קוּם « se lever », בּוֹא « venir », מוּת « mourir ». La radicale médiane n'est jamais syllabée : la voyelle qui l'entoure s'allonge (holam pour ו, hireq-yod pour י) et la conjugaison présente des alternances vocaliques caractéristiques.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense **158 lexèmes verbaux creux** ; **65** d'entre eux sont attestés **au moins 10 fois** dans la Bible hébraïque (51 ע״ו et 14 ע״י). La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `ayin_vav`).

## Règles générales de conjugaison (qal)

1. **Radical non syllabé.** Le ו/י médian n'occupe jamais une position syllabique : entre les 1ʳᵉ et 3ᵉ radicales s'insère une voyelle longue qui « absorbe » la médiane — קָם (qamets) et non *קָוַם, בֵּן (tsere) et non *בָּיִן au qal parfait de בין.
2. **Parfait.** 3ᵉ m. sg. : voyelle longue unique entre P1 et P3 — קָם, בֵּן ; 3ᵉ f. sg. קָמָה, בִּינָה (mater lectionis ה) ; 2ᵉ m. sg. קַמְתָּ ; 1ʳᵉ c. sg. קַמְתִּי ; 3ᵉ pl. קָמוּ.
3. **Imparfait (yiqtol).** La voyelle radicale revient devant le suffixe : 3ᵉ m. sg. **יָקוּם / יָבִין** (qamets-holam, tsere→hireq selon le verbe) ; 3ᵉ f. sg. תָּקוּם ; 2ᵉ f. sg. תָּקְמִי ; 3ᵉ pl. יָקוּמוּ ; 1ʳᵉ c. sg. אָקוּם. Certains verbes (מוּת « mourir », בּוֹא « venir ») ont un imparfait court : יָמֻת/יָמוּת, יָבֹא.
4. **Wayyiqtol.** Forme courte à voyelle brève : וַיָּקָם, וַיָּמָת, וַיָּבֹא — la 1ʳᵉ radicale prend qamets (allongement de la syllabe ouverte) au lieu du sheva attendu.
5. **Jussif.** Souvent distinct de l'imparfait : יָקָם, יָמָת (voyelle longue, forme courte) ; pour בּוֹא : יָבֹא.
6. **Cohortatif.** אָקוּמָה « que je me lève » — ה paragogique sur la forme longue.
7. **Impératif.** 2ᵉ m. sg. קוּם (forme longue) ou קְמָה (variante avec ה paragogique) ; בֹּא « viens » ; שִׁים « place » (ע״י : hireq-yod) ; 2ᵉ f. sg. קוּמִי ; 2ᵉ m. pl. קוּמוּ ; 2ᵉ f. pl. קֹמְנָה.
8. **Infinitifs.** Construit : קוּם (ע״ו), בּוֹא (voyelle pleine), שִׁית (ע״י, forme ancienne) ; avec préfixe בְּ/לְ/מְ le plus souvent : לָקוּם, בּוֹא. Absolu : קָם, קוּם selon les verbes.
9. **Participe.** Actif m. sg. קָם (holam absent, qamets) ou קָם ; ע״י : בִּין, שָׂם (qamets) ; f. sg. קָמָה ; m. pl. קָמִים. Passif qal : קָם « être levé » (qamets-qamets).
10. **Cumul avec d'autres faiblesses.** Un verbe creux peut être aussi pe-guttural/lamed-guttural (חוּל « tourmenter », חוּשׁ « se hâter » ; עוּר « être éveillé »), pe-alef (אָב « consentir »), ou pe-nun/pe-yod (יָשֵׁב est ע״י avec yod initial historique). La classification `classify_root` priorise : double > lamed_he > lamed_alef > lamed_guttural > **ayin_vav** > ayin_guttural > pe_nun > pe_alef > pe_yod > pe_guttural.
11. **Frontière ע״ו/ע״י.** Les deux sous-types partagent la même catégorie `ayin_vav` dans le projet (le ו et le י médians sont traités pareillement) ; la différence est purement orthographique/phonétique : holam (ע״ו) contre hireq-yod (ע״י). Certains verbes oscillent historiquement entre les deux (שׁוּם/שִׁים « placer »).
12. **Verbes très fréquents.** שׁוּב « retourner » (1039 occ.), מוּת « mourir » (836), קוּם « se lever » (666), שִׂים « placer » (611, ע״י), סוּר « détourner » (298), אֵיב « être hostile » (284). À noter : בּוֹא « venir » (2570 occ.) est classé `lamed_alef` (l'alef final prime sur le ו médian dans `classify_root`) et יָשֵׁב « habiter » est `pe_yod` ; נוּחַ « se reposer » est `lamed_guttural`.

## Exemple de conjugaison complète : קום « se lever » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | קָם |
| Parfait | 3 | f. sg. | קָמָה |
| Parfait | 2 | m. sg. | קַמְתָּ |
| Parfait | 2 | f. sg. | קַמְתְּ |
| Parfait | 1 | c. sg. | קַמְתִּי |
| Parfait | 3 | m. pl. | קָמוּ |
| Imparfait | 3 | m. sg. | יָקוּם |
| Imparfait | 3 | f. sg. | תָּקוּם |
| Imparfait | 2 | m. sg. | תָּקוּם |
| Imparfait | 2 | f. sg. | תָּקְמִי |
| Imparfait | 1 | c. sg. | אָקוּם |
| Imparfait | 3 | m. pl. | יָקוּמוּ |
| Imparfait | 3 | f. pl. | תָּקֹמְנָה |
| Jussif | 3 | m. sg. | יָקָם |
| Cohortatif | 1 | c. sg. | אָקוּמָה |
| Impératif | 2 | m. sg. | קוּם |
| Impératif | 2 | f. sg. | קוּמִי |
| Impératif | 2 | m. pl. | קוּמוּ |
| Impératif | 2 | f. pl. | קֹמְנָה |
| Infinitif construit | — | — | קוּם |
| Participe actif | — | m. sg. | קָם |
| Participe passif | — | m. sg. | קָם |

## Les 65 verbes creux (ע״ו/ע״י) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `ayin_vav` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Type | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | עוד | ע״ו | encore | warn, to witness | 45 | עָד | יָעוּד | עוּדָה | עוּד | עָד |
| 2 | עוף | ע״ו | oiseau | fly | 25 | עָף | יָעוּף | עוּפָה | עוּף | עָף |
| 3 | עור | ע״ו | peau | be awake | 81 | עָר | יָעוּר | עוּרָה | עוּר | עָר |
| 4 | עות | ע״ו | courbent | be crooked | 12 | עָת | יָעוּת | עוּתָה | עוּת | עָת |
| 5 | איב | ע״י | ennemi | be hostile | 284 | אָב | יָאוּב | אוּבָה | אוּב | אָב |
| 6 | אור | ע״ו | lumière | be light | 50 | אָר | יָאוּר | אוּרָה | אוּר | אָר |
| 7 | אוץ | ע״ו | pressaient | urge | 11 | אָץ | יָאוּץ | אוּצָה | אוּץ | אָץ |
| 8 | בין | ע״י | entre | understand | 171 | בָן | יָבוּן | בוּנָה | בוּן | בָן |
| 9 | בושׁ | ע״ו | avoir honte | be ashamed | 110 | בָשׁ | יָבוּשׁ | בוּשָׁה | בוּשׁ | בָשׁ |
| 10 | בוס | ע״ו | fouler aux pieds | tread down | 13 | בָס | יָבוּס | בוּסָה | בוּס | בָס |
| 11 | בוז | ע״ו | méprise | despise | 15 | בָז | יָבוּז | בוּזָה | בוּז | בָז |
| 12 | שׁיר | ע״י | chant | sing | 89 | שָׁר | יָשׁוּר | שׁוּרָה | שׁוּר | שָׁר |
| 13 | שׁית | ע״י | établir | put | 86 | שָׁת | יָשׁוּת | שׁוּתָה | שׁוּת | שָׁת |
| 14 | שׁוב | ע״ו | retourner | gather | 19 | שָׁב | יָשׁוּב | שׁוּבָה | שׁוּב | שָׁב |
| 15 | שׁוב | ע״ו | retourner | return | 1039 | שָׁב | יָשׁוּב | שׁוּבָה | שׁוּב | שָׁב |
| 16 | שׁור | ע״ו | bétail | regard | 16 | שָׁר | יָשׁוּר | שׁוּרָה | שׁוּר | שָׁר |
| 17 | שׁוט | ע״ו | là | rove about | 14 | שָׁט | יָשׁוּט | שׁוּטָה | שׁוּט | שָׁט |
| 18 | דין | ע״י | juger | judge | 26 | דָן | יָדוּן | דוּנָה | דוּן | דָן |
| 19 | דושׁ | ע״ו | fouler | tread on | 18 | דָשׁ | יָדוּשׁ | דוּשָׁה | דוּשׁ | דָשׁ |
| 20 | דור | ע״ו | génération | dwell | 11 | דָר | יָדוּר | דוּרָה | דוּר | דָר |
| 21 | שׂים | ע״י |  | put | 611 | שָׂם | יָשׂוּם | שׂוּמָה | שׂוּם | שָׂם |
| 22 | שׂושׂ | ע״ו | se réjouir | rejoice | 28 | שָׂשׂ | יָשׂוּשׂ | שׂוּשָׂה | שׂוּשׂ | שָׂשׂ |
| 23 | גיל | ע״י | se réjouir | rejoice | 46 | גָל | יָגוּל | גוּלָה | גוּל | גָל |
| 24 | גור | ע״ו | séjourner | be afraid | 11 | גָר | יָגוּר | גוּרָה | גוּר | גָר |
| 25 | גור | ע״ו | séjourner | dwell | 84 | גָר | יָגוּר | גוּרָה | גוּר | גָר |
| 26 | כול | ע״ו | soutenir | comprehend | 39 | כָל | יָכוּל | כוּלָה | כוּל | כָל |
| 27 | כון | ע״ו | établir | be firm | 217 | כָן | יָכוּן | כוּנָה | כוּן | כָן |
| 28 | לין | ע״י |  | lodge | 71 | לָן | יָלוּן | לוּנָה | לוּן | לָן |
| 29 | ליץ | ע״י | se moquer | boast | 13 | לָץ | יָלוּץ | לוּצָה | לוּץ | לָץ |
| 30 | לון | ע״ו | loger | murmur | 15 | לָן | יָלוּן | לוּנָה | לוּן | לָן |
| 31 | מושׁ | ע״ו | enlever | depart | 21 | מָשׁ | יָמוּשׁ | מוּשָׁה | מוּשׁ | מָשׁ |
| 32 | מוג | ע״ו | fondre | faint | 18 | מָג | יָמוּג | מוּגָה | מוּג | מָג |
| 33 | מול | ע״ו | circoncire | circumcise | 31 | מָל | יָמוּל | מוּלָה | מוּל | מָל |
| 34 | מור | ע״ו | changer | exchange | 15 | מָר | יָמוּר | מוּרָה | מוּר | מָר |
| 35 | מות | ע״ו | mourir | die | 836 | מָת | יָמוּת | מוּתָה | מוּת | מָת |
| 36 | מוט | ע״ו | chanceler | totter | 37 | מָט | יָמוּט | מוּטָה | מוּט | מָט |
| 37 | נוד | ע״ו | errer | flee | 28 | נָד | יָנוּד | נוּדָה | נוּד | נָד |
| 38 | נוף | ע״ו | agiter | swing | 35 | נָף | יָנוּף | נוּפָה | נוּף | נָף |
| 39 | נוס | ע״ו | fuir | flee | 160 | נָס | יָנוּס | נוּסָה | נוּס | נָס |
| 40 | פוק | ע״ו | promouvoir | totter | 10 | פָק | יָפוּק | פוּקָה | פוּק | פָק |
| 41 | פוץ | ע״ו | disperser | disperse | 66 | פָץ | יָפוּץ | פוּצָה | פוּץ | פָץ |
| 42 | קיץ | ע״י | s'éveiller | pass summer | 23 | קָץ | יָקוּץ | קוּצָה | קוּץ | קָץ |
| 43 | קום | ע״ו | se lever | arise | 666 | קָם | יָקוּם | קוּמָה | קוּם | קָם |
| 44 | ריב | ע״י | contester | contend | 68 | רָב | יָרוּב | רוּבָה | רוּב | רָב |
| 45 | ריק | ע״י | vider | be empty | 20 | רָק | יָרוּק | רוּקָה | רוּק | רָק |
| 46 | רושׁ | ע״ו | être pauvre | be poor | 25 | רָשׁ | יָרוּשׁ | רוּשָׁה | רוּשׁ | רָשׁ |
| 47 | רום | ע״ו | exalter | be high | 194 | רָם | יָרוּם | רוּמָה | רוּם | רָם |
| 48 | רוץ | ע״ו | courir | run | 105 | רָץ | יָרוּץ | רוּצָה | רוּץ | רָץ |
| 49 | סוג | ע״ו | se détourner | turn | 26 | סָג | יָסוּג | סוּגָה | סוּג | סָג |
| 50 | סוך | ע״ו | oindre | anoint | 10 | סָך | יָסוּך | סוּכָה | סוּך | סָך |
| 51 | סור | ע״ו | ôter | turn aside | 298 | סָר | יָסוּר | סוּרָה | סוּר | סָר |
| 52 | סות | ע״ו | inciter | incite | 19 | סָת | יָסוּת | סוּתָה | סוּת | סָת |
| 53 | תור | ע״ו | espionner | spy | 25 | תָר | יָתוּר | תוּרָה | תוּר | תָר |
| 54 | טוב | ע״ו | agréable | be good | 45 | טָב | יָטוּב | טוּבָה | טוּב | טָב |
| 55 | טול | ע״ו | jeter | cast | 15 | טָל | יָטוּל | טוּלָה | טוּל | טָל |
| 56 | חיל | ע״י | force | have labour pain, to cry | 41 | חָל | יָחוּל | חוּלָה | חוּל | חָל |
| 57 | חושׁ | ע״ו | se hâter | make haste | 20 | חָשׁ | יָחוּשׁ | חוּשָׁה | חוּשׁ | חָשׁ |
| 58 | חול | ע״ו | se tordre | dance | 13 | חָל | יָחוּל | חוּלָה | חוּל | חָל |
| 59 | חוס | ע״ו | avoir pitié | pity | 25 | חָס | יָחוּס | חוּסָה | חוּס | חָס |
| 60 | צוד | ע״ו | chasser | hunt | 18 | צָד | יָצוּד | צוּדָה | צוּד | צָד |
| 61 | צום | ע״ו | jeûne | fast | 22 | צָם | יָצוּם | צוּמָה | צוּם | צָם |
| 62 | צוק | ע״ו | oppresseur | oppress | 14 | צָק | יָצוּק | צוּקָה | צוּק | צָק |
| 63 | צור | ע״ו | rocher | bind | 32 | צָר | יָצוּר | צוּרָה | צוּר | צָר |
| 64 | זיד | ע״י | orgueil | be presumptuous | 13 | זָד | יָזוּד | זוּדָה | זוּד | זָד |
| 65 | זוב | ע״ו | flux | flow | 43 | זָב | יָזוּב | זוּבָה | זוּב | זָב |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet (158 lexèmes) peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` et une 2ᵉ radicale ו/י (classification `classify_root` du projet).
- Le projet regroupe ע״ו et ע״י dans une catégorie unique `ayin_vav` ; la colonne « Type » du tableau distingue les deux sous-types.
- Les formes générées sont celles du gabarit dominant attesté ; certains verbes creux très irréguliers (בּוֹא, נוּחַ, מוּת) présentent des variantes (formes brèves/longues) que le gabarit dominant ne couvre qu'en partie. Le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
