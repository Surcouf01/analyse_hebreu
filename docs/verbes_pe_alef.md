# Les verbes pe-alef (פ״א) — liste et règles de conjugaison

Un **verbe pe-alef** (פ״א) est un verbe dont la **1ʳᵉ radicale est un א** : אמר « dire », אכל « manger », אסף « rassembler ». L'alef n'est qu'un support de voyelle (consonne quiescente) : il ne se prononce qu'avec une voyelle et refuse le sheva.

La base morphologique **BHSA** (branche `data2021`, classification `classify_root` du projet) recense ces verbes ; **21** lexèmes sont attestés **au moins 10 fois** dans la Bible hébraïque. La liste ci-dessous donne, pour chacun, les formes principales générées par le paradigme **qal** du projet (`bhsa_grammar/binyan_gen.py`, gabarits de la catégorie `pe_alef`).

## Règles générales de conjugaison (qal)

1. **Alef quiescent.** L'alef n'existe phonétiquement qu'avec une voyelle : après un préfixe, le sheva attendu devient une voyelle brève pleine — אֹמֵר « disant » (participe), et à l'imparfait le préfixe porte une voyelle longue : יֹאמַר « il dira », תֹּאכַל « tu mangeras » (et non *תִּאכַל).
2. **Parfait régulier.** Le parfait garde l'alef avec sa voyelle : אָמַר, אָכַל, אָמְרָה, אָכְלוּ.
3. **Impératif.** La voyelle initiale s'allonge : אֱמֹר « dis ! », אֱכֹל « mange ! » — hatef-sere ou holam initial selon le verbe.
4. **Verbes fréquents.** אמר « dire » (5380 occ. — le verbe le plus fréquent de la Bible hébraïque), אכל « manger » (819), אסף « rassembler » (205), אבד « périr » (195), אמן « être fidèle » (110).
5. **Frontière avec le pe-guttural.** Le projet classe les verbes en א initial dans la catégorie `pe_alef` propre, distincte du `pe_guttural` (ה/ח/ע) ; les deux mécanismes (quiescence contre refus de sheva) sont documentés séparément dans l'onglet « Règles du verbe faible » de l'application.

## Exemple de conjugaison complète : אכל « manger » (qal)

| Forme | Pers. | Genre / Nb | Hébreu |
|---|---|---|---|
| Parfait | 3 | m. sg. | אָכַל |
| Parfait | 3 | f. sg. | אָכְלָה |
| Parfait | 2 | m. sg. | אָכַלְתָּ |
| Parfait | 2 | f. sg. | אָכַלְתְּ |
| Parfait | 1 | c. sg. | אָכַלְתִּי |
| Parfait | 3 | m. pl. | אָכְלוּ |
| Imparfait | 3 | m. sg. | יֹאכַל |
| Imparfait | 3 | f. sg. | תֹּאכַל |
| Imparfait | 2 | m. sg. | תֹּאכַל |
| Imparfait | 2 | f. sg. | תֹּאכְלִי |
| Imparfait | 1 | c. sg. | אֹכַל |
| Imparfait | 3 | m. pl. | יֹאכְלוּ |
| Jussif | 3 | m. sg. | יֶּאֱכֹל |
| Impératif | 2 | m. sg. | אֱכֹל |
| Impératif | 2 | f. sg. | אִכְלִי |
| Impératif | 2 | m. pl. | אִכְלוּ |
| Infinitif construit | — | — | אֱכֹל |
| Infinitif absolu | — | — | אָכֹל |
| Participe actif | — | m. sg. | אֹכֵל |

## Les 21 verbes pe-alef (פ״א) attestés au moins 10 fois (BHSA)

Sens français : lexique du projet (`bhsa_grammar/lex_fr.json`). Glose anglaise : feature BHSA `gloss`. Formes hébraïques générées par `bhsa_grammar/binyan_gen.py` à partir des gabarits attestés de la catégorie `pe_alef` (`bhsa_grammar/binyan_templates.json`). Tri alphabétique BHSA.

| # | Lexème | Sens (FR) | Glose (EN) | Occ. | Parfait 3 m. sg. | Imparfait 3 m. sg. | Impératif 2 m. sg. | Inf. construit | Participe m. sg. |
|---||---||---||---||---||---||---||---||---||---||
| 1 | אבד | périr | perish | 195 | אָבַד | יֹאבַד | אֱבֹד | אֱבֹד | אֹבֵד |
| 2 | אבל | mener deuil | mourn | 37 | אָבַל | יֹאבַל | אֱבֹל | אֱבֹל | אֹבֵל |
| 3 | אשׁם | culpabilité (offrande) | do wrong | 38 | אָשַׁם | יֹאשַׁם | אֱשֹׁם | אֱשֹׁם | אֹשֵׁם |
| 4 | אשׁר | qui | be happy | 10 | אָשַׁר | יֹאשַׁר | אֱשֹׁר | אֱשֹׁר | אֹשֵׁר |
| 5 | אדם | homme | be ruddy | 11 | אָדַם | יֹאדַם | אֱדֹם | אֱדֹם | אֹדֵם |
| 6 | אכל | manger | eat | 819 | אָכַל | יֹאכַל | אֱכֹל | אֱכֹל | אֹכֵל |
| 7 | אלם | être muet | bind | 10 | אָלַם | יֹאלַם | אֱלֹם | אֱלֹם | אֹלֵם |
| 8 | אמל | languissants | wither | 16 | אָמַל | יֹאמַל | אֱמֹל | אֱמֹל | אֹמֵל |
| 9 | אמן | être fidèle | be firm | 110 | אָמַן | יֹאמַן | אֱמֹן | אֱמֹן | אֹמֵן |
| 10 | אמר | dire | say | 5380 | אָמַר | יֹאמַר | אֱמֹר | אֱמֹר | אֹמֵר |
| 11 | אמץ | fortifier | be strong | 42 | אָמַץ | יֹאמַץ | אֱמֹץ | אֱמֹץ | אֹמֵץ |
| 12 | אנף | être en colère | be angry | 15 | אָנַף | יֹאנַף | אֱנֹף | אֱנֹף | אֹנֵף |
| 13 | ארב | dresser une embuscade | lie in ambush | 42 | אָרַב | יֹארַב | אֱרֹב | אֱרֹב | אֹרֵב |
| 14 | ארשׂ | fiancer | betroth | 12 | אָרַשׂ | יֹארַשׂ | אֱרֹשׂ | אֱרֹשׂ | אֹרֵשׂ |
| 15 | ארג | tisser | weave | 15 | אָרַג | יֹארַג | אֱרֹג | אֱרֹג | אֹרֵג |
| 16 | ארך | longueur | be long | 35 | אָרַך | יֹארַך | אֱרֹך | אֱרֹך | אֹרֵך |
| 17 | אסף | rassembler | gather | 205 | אָסַף | יֹאסַף | אֱסֹף | אֱסֹף | אֹסֵף |
| 18 | אסר | lier | bind | 71 | אָסַר | יֹאסַר | אֱסֹר | אֱסֹר | אֹסֵר |
| 19 | אזל | aller | go | 13 | אָזַל | יֹאזַל | אֱזֹל | אֱזֹל | אֹזֵל |
| 20 | אזן | oreille | listen | 42 | אָזַן | יֹאזַן | אֱזֹן | אֱזֹן | אֹזֵן |
| 21 | אזר | ceindre | put on | 17 | אָזַר | יֹאזַר | אֱזֹר | אֱזֹר | אֹזֵר |

## Remarques

- Le seuil de 10 occurrences écarte les lexèmes rares ; le comptage complet peut être refait depuis les features `lex`/`sp` de la BHSA avec `sp = verb` (classification `classify_root` du projet, catégorie `pe_alef`).
- Les formes générées sont celles du gabarit dominant attesté ; le mode « Binyanim » de l'application affiche le paradigme complet de chaque verbe.
