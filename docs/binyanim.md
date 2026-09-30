# Les binyanim — le système verbal de l'hébreu biblique

## Définition

Un **binyan** (בִּנְיָן, « construction », pluriel *binyanim*) est une « voix » ou « conjugaison » du verbe hébreu : un schème de formation qui combine préfixes, voyelles et affixes pour dériver, à partir d'une même racine consonantique, des verbes de sens actif, passif, causatif, réciproque ou réfléchi. Là où le français utilise des auxiliaires (« faire écrire », « être écrit »), l'hébreu encode ces nuances directement dans la morphologie du verbe.

Exemple : la racine **כ-ת-ב** « écrire » donne, selon le binyan :

| Binyan | Parfait 3 m. sg. | Sens |
|---|---|---|
| qal | כָּתַב | il a écrit |
| nifal | נִכְתַּב | il a été écrit / il s'est écrit |
| piel | כִּתַּב | il a écrit (intensif) |
| pual | כֻּתַּב | il a été écrit (passif du piel) |
| hifil | הִכְתִּיב | il a fait écrire |
| hofal | הָכְתַב | il a été fait écrire |
| hithpael | הִתְכַּתֵּב | il s'est écrit / il s'est fait correspondre |

Le système du projet reconnaît et génère les **7 binyanim hébreux principaux** (qal, nifal, piel, pual, hifil, hofal, hithpael) via `bhsa_grammar/binyan_gen.py`. Le document [verbe_ktb_binyanim.md](verbe_ktb_binyanim.md) détaille la conjugaison complète de כתב dans chacun d'eux, et l'index [verbes_faibles.md](verbes_faibles.md) recense la conjugaison des verbes faibles par catégorie.

## Perspective historique

- Le mot בִּנְיָן vient de בנה « construire » : les grammairiens juifs médiévaux comparaient déjà les schèmes verbaux à des « constructions » édifiées sur la racine.
- La théorie des racines trilitères est l'œuvre de **Judah Ḥayyūj** (xᵉ s., Cordoue), systématisée par **Jonah ibn Janāḥ** ; **David Qimḥi** (Radak) l'a popularisée en Europe. Les binyanim y sont décrits comme des schèmes dérivationnels réguliers.
- Les grammaires de référence modernes — **Gesenius-Kautzsch**, **Joüon-Muraoka** (§ 49 : le qal exprime l'état ou l'action simple ; les autres thèmes expriment des nuances de l'action), **Waltke-O'Connor** — décrivent 7 thèmes principaux pour l'hébreu, auxquels s'ajoutent quelques schèmes rares (poel, palal, etc.).

## Les 7 binyanim hébreux

Statistiques d'attestation dans la BHSA (extraction des features `vs`/`sp`/`languageISO`, branche `data2021`) : le corpus hébreu compte **73 710 mots verbaux** (toutes formes verbales, participes inclus), répartis ainsi (occurrences ; lexèmes distincts) :

| Binyan | Occurrences | Lexèmes distincts | Part des verbes |
|---|---:|---:|---:|
| qal | 50 205 | 1 133 | 68,1 % |
| hifil | 9 407 | 498 | 12,8 % |
| piel | 6 811 | 490 | 9,2 % |
| nifal | 4 145 | 432 | 5,6 % |
| hithpael | 960 | 225 | 1,3 % |
| pual | 492 | 199 | 0,7 % |
| hofal | 415 | 105 | 0,6 % |

Les schèmes restants (hsht, hotp, pasq, poel, tif, nit, poal, htpo — environ 200 occurrences au total) sont des formes rares ou secondaires ; ils ne sont pas modélisés par le moteur du projet.

### 1. Qal (קַל) — le thème léger

Le qal (« léger », par opposition aux thèmes « lourds » pourvus de préfixe) est le binyan fondamental, non dérivé : action simple ou état, à la voix active ou moyenne. C'est la forme « du dictionnaire ».

- **Marquage** : aucun préfixe ; le vocalisme distingue parfait (qatal : כָּתַב), imparfait (yiqtol : יִכְתֹּב), impératif, infinitif, participes.
- **Exemples** : שָׁמַע « il a entendu », מָלַךְ « il a régné », קָטֹן « être petit » (statif).
- **Participe passif qal** : le qal possède un participe passif à part entière (כָּתוּב « écrit », בָּנוּי « bâti »), surtout pour les verbes d'action transitifs.

### 2. Nifal (נִפְעַל) — passif / moyen du qal

- **Marquage** : préfixe נִ- au parfait (נִכְתַּב), préfixe יִ- + alef prothétique à l'imparfait (יִכָּתֵב).
- **Valeurs** : (1) passif du qal (שָׁמַע → נִשְׁמַע « être entendu ») ; (2) moyen ou réfléchi (נִשְׁמַר « se garder ») ; (3) inchoatif / potentiel (נִפְתַּח « s'ouvrir », נִקְרָא « être appelé »).
- **Exemples** : ראה nifal « apparaître, se laisser voir » (Ex 3,2), ידע nifal « être connu ».

### 3. Piel (פִּעֵל) — l'intensif actif

- **Marquage** : voyelle i sous la première radicale (כִּתַּב), dagesh fort dans la 2ᵉ radicale (דִּבֶּר).
- **Valeurs** : (1) intensif (שָׁלַח → שִׁלַּח « renvoyer ») ; (2) déclaratif ou factitif (דָּבַר → דִּבֵּר « parler ») ; (3) itératif / distributif (פָּקַד → פִּקֵּד « inspecter »). Selon les verbes, le piel n'a pas toujours un sens nettement intensif.
- **Exemples** : בֵּרַךְ « bénir », קִדַּשׁ « sanctifier », שִׁבֵּר « briser en morceaux ».

### 4. Pual (פֻּעַל) — le passif du piel

- **Marquage** : voyelle u sous la première radicale (כֻּתַּב), dagesh fort sur la 2ᵉ radicale.
- **Valeur** : passif du piel ; en pratique le plus souvent passif simple en contexte.
- **Exemples** : מְלֻאָה « être rempli », מְבֹרָךְ / בָּרוּךְ « béni » (participe). Beaucoup de participes « passifs » courants sont des pual, tandis que le participe passif qal (כָּתוּב) est plus restreint.

### 5. Hofal (הֻפְעַל) — le passif du hifil

- **Marquage** : préfixe הָ- au parfait (הָכְתַב, variante הֻפְעַל selon les verbes faibles).
- **Valeur** : passif du hifil (הִכְתִּיב « faire écrire » → הָכְתַב « être fait écrire ») ; le plus souvent passif simple en contexte. C'est le binyan le plus rare des sept (415 occurrences).
- **Exemples** : הוֹדַע « être fait savoir » (Dan 2), הֻבָּא « être apporté », הֻגַּל « être déporté » (racine גלה).

### 6. Hithpael (הִתְפַּעֵל) — réfléchi / réciproque

- **Marquage** : préfixe הִתְ- + dagesh fort sur la 2ᵉ radicale (הִתְכַּתֵּב).
- **Valeurs** : réfléchi (הִתְפַּלֵּל « prier »), réciproque (הִתְרַאֵה « se voir mutuellement »), moyen (הִתְהַלֵּךְ « se promener »), parfois passif. L'infixe -ת- continue un élément sémitique commun (cf. l'accadien -ta-).
- **Exemples** : הִתְפַּלֵּל « prier », הִתְיַצֵּב « se tenir debout », הִשְׁתַּחֲוָה « se prosterner » (racine חוה, avec « conversion des sibilantes » שׁ → שׂ).

### 7. Hifil (הִפְעִיל) — le causatif actif

- **Marquage** : préfixe הִ- + voyelle i sous la première radicale (הִכְתִּיב).
- **Valeurs** : (1) causatif (מָלַךְ → הִמְלִיךְ « faire régner ») ; (2) déclaratif (רָאָה → הֶרְאָה « montrer ») ; (3) parfois simple, sans nuance causative nette ; (4) « laisser faire » (הִקְטִין « laisser être petit »).
- **Exemples** : הִשְׁמִיעַ « faire entendre », הִגִּיד « faire connaître, raconter », הוֹצִיא « faire sortir » (racine יצא).

## Les binyanim rares

Au-delà des 7 thèmes principaux, la BHSA atteste quelques schèmes marginaux, souvent chez des racines à 2ᵉ radicale faible :

- **poel / poal** : variante du piel/pual avec voyelle o, typique de certaines racines ע״ו / ע״י ou « geminées étendues » (5 et 3 occurrences).
- **hsht / hotp** : formes de hithpael/hofal de verbes faibles en variation libre avec les formes standard (170 et 8 occurrences).
- **pasq** (6), **tif** (5), **nit** (3), **htpo** (3), **etpa** (2) : hapax ou quasi-hapax du corpus massorétique ; la BHSA les étiquette séparément mais les grammaires les rattachent à un thème principal (p. ex. tif = nifal d'un verbe ע״י).

Le moteur du projet ne modélise pas ces schèmes rares : seuls les 7 binyanim principaux disposent de gabarits dans `binyan_templates.json`.

## Les binyanim araméens

Les passages araméens de la Bible (Esdre, Daniel — environ 6 100 mots, 188 lexèmes verbaux) utilisent un système apparenté mais distinct, que la BHSA étiquette séparément (environ 1 070 occurrences verbales) :

| Binyan araméen | Occurrences | Équivalent hébreu |
|---|---:|---|
| peal | 654 | qal |
| hafel | 163 | hifil |
| pael | 88 | piel |
| hithpeel | 53 | hithpael |
| peil | 40 | pual |
| hithpaal | 30 | hithpael |
| shafel | 15 | causatif à ש (cf. accadien S-stem) |
| hofal | 12 | hofal |
| etpa / etpe | 9 | nifal |
| afel | 4 | hifil |
| hsht | 2 | hithpael |

Le **peal** est la forme ordinaire de l'araméen biblique (כְּתַב « il écrivit » ; participe כָּתָב « scribe », le mot כְּתָבָא). Le moteur du projet ne génère pas les paradigmes araméens ; l'application les identifie via la langue (`languageISO = arc`).

## Comment le projet reconnaît un binyan

L'onglet « Binyanim » de l'application génère les paradigmes à partir de la racine et de sa catégorie (`classify_root` : verbe fort, pe-nun, ayin-waw, etc. — voir [verbes_faibles.md](verbes_faibles.md)), puis, pour chaque binyan, applique les gabarits de `binyan_templates.json` : préfixe, vocalisme, affixes de personne/genre/nombre. Les données de la BHSA (features `vs` = stem, `vt` = tense) servent de référence pour déterminer si un binyan est attesté pour une racine donnée (fichier `binyan_senses_fr_en.json` : sens français/anglais par binyan).

## Remarques

- **Le qal écrase tout** : plus de deux tiers des occurrences verbales (50 205 sur 73 710, 68,1 %) sont au qal. Les prophètes et la poésie recourent proportionnellement davantage aux thèmes dérivés.
- **Pual et hofal sont les parents pauvres** : environ 900 occurrences à eux deux, presque exclusivement sous forme de participes ou de parfaits 3ᵉ personne, et souvent au passif du qal plutôt que du piel/hifil étymologique.
- **Le nifal cumule les fonctions** : passif du qal, moyen, inchoatif — c'est le thème le plus polysémique, difficile à paraphraser en français par une seule formule.
- **Sens par binyan dans le projet** (source `binyan_senses_fr_en.json`) : ראה qal « voir » / hifil « montrer » / nifal « apparaître » / hithpael « se montrer » ; כתב qal « écrire » / nifal « être écrit » / piel « écrire (intensif) » ; שלם qal « être complet » / piel « rembourser » / hifil « achever » ; ילד qal « enfanter » / nifal « naître » / hifil « engendrer » ; גלה piel/hifil « emmener en exil » / hofal « être déporté ».
- **Une même racine peut vivre dans plusieurs binyanim** : les records de la BHSA sont des racines comme ילד, פקד ou בקש, attestées dans 7 à 8 thèmes différents.

## Pour aller plus loin

- [verbe_ktb_binyanim.md](verbe_ktb_binyanim.md) — conjugaison complète de כתב dans les 7 binyanim
- [verbes_faibles.md](verbes_faibles.md) — index des verbes faibles (10 catégories) avec introduction historique
- [verbes_lamed_he.md](verbes_lamed_he.md), [verbes_pe_guttural.md](verbes_pe_guttural.md), [verbes_ayin_vav_yod.md](verbes_ayin_vav_yod.md) et les autres documents de la série
