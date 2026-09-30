# Documentation grammaticale — index

Ce fichier est le point d'entrée de la documentation grammaticale hébreu du projet. Toutes les formes et tous les paradigmes cités dans cette série sont **générés par le moteur de conjugaison du projet** (`bhsa_grammar/binyan_gen.py` et `binyan_templates.json`), et les effectifs sont extraits de la **BHSA** (branche `data2021`, features `lex`, `sp`, `vs`, `vt`, `gloss`), garantissant la cohérence avec l'onglet « Binyanim » de l'application.

## Vue d'ensemble

| Domaine | Document | Contenu |
|---|---|---|
| Le système verbal | [binyanim.md](binyanim.md) | Les 7 binyanim hébreux (qal, nifal, piel, pual, hifil, hofal, hithpael) : sens, morphologie, statistiques BHSA, schèmes rares, binyanim araméens |
| Étude d'une racine | [verbe_ktb_binyanim.md](verbe_ktb_binyanim.md) | כתב « écrire » (verbe fort) : conjugaison complète dans les 7 binyanim, attestés et théoriques |
| Verbes faibles — index | [verbes_faibles.md](verbes_faibles.md) | Introduction générale et historique, ordre de priorité de `classify_root`, tableau des 10 catégories |

## Les 10 catégories de verbes faibles

Chaque document donne la définition de la catégorie, les règles de conjugaison au qal, un paradigme complet et le tableau des verbes attestés (seuil : ≥ 10 occurrences dans la BHSA), avec sens français (`lex_fr.json`) et glose anglaise.

| # | Catégorie | Document | Verbes | Exemple |
|---|---|---|---:|---|
| 1 | ל״ה (lamed-he) | [verbes_lamed_he.md](verbes_lamed_he.md) | 93 | בנה « bâtir » |
| 2 | פ״ג (pe-guttural) | [verbes_pe_guttural.md](verbes_pe_guttural.md) | 77 | עבד « servir » |
| 3 | ע״ו / ע״י (ayin-waw / ayin-yod) | [verbes_ayin_vav_yod.md](verbes_ayin_vav_yod.md) | 65 | קום « se lever » |
| 4 | פ״נ (pe-nun) | [verbes_pe_nun.md](verbes_pe_nun.md) | 35 | נפל « tomber » |
| 5 | פ״י (pe-yod) | [verbes_pe_yod.md](verbes_pe_yod.md) | 24 | ישב « habiter » |
| 6 | פ״א (pe-alef) | [verbes_pe_alef.md](verbes_pe_alef.md) | 21 | אכל « manger » |
| 7 | ע״ג (ayin-guttural) | [verbes_ayin_guttural.md](verbes_ayin_guttural.md) | 78 | שׁמע « entendre » |
| 8 | ל״א (lamed-alef) | [verbes_lamed_alef.md](verbes_lamed_alef.md) | 23 | מצא « trouver » |
| 9 | ל״ג (lamed-guttural) | [verbes_lamed_guttural.md](verbes_lamed_guttural.md) | 69 | שׁלח « envoyer » |
| 10 | verbes doubles (geminations) | [verbes_doubles.md](verbes_doubles.md) | 46 | סבב « entourer » |

Soit **531 verbes faibles documentés** (chiffres et listes vérifiés sur l'extraction BHSA, classification `classify_root` du projet).

## Remarques transversales

- **Gutturales** : la tradition considère comme gutturales (et « assimilées ») א ע ה ח ר ; le moteur du projet retient `GUTTURALS = (א, ה, ח, ע)` — le ר, consonne sonante, y est traité comme forte (`strong`). Les documents des catégories gutturales signalent cette différence.
- **Priorité des catégories** : quand plusieurs faiblesses se combinent dans une même racine (p. ex. נוח, פ-נ + ל-ח), `classify_root` applique un ordre de priorité : `double > lamed_he > lamed_alef > lamed_guttural > ayin_vav > ayin_guttural > pe_nun > pe_alef > pe_yod > pe_guttural > strong`. Chaque racine n'apparaît donc que dans un seul document.
- **Frontières documentées** : בוא, יצא, נשׂא → `lamed_alef` ; שׁמע, ידע, לקח, שׁלח → `lamed_guttural` ; אהב → `ayin_guttural` ; רדף → `strong`.

## Autres documents du dossier `docs/`

- [renumerotation_traductions.md](renumerotation_traductions.md) — renumérotation des traductions
- [renumerotation_torres_amat.md](renumerotation_torres_amat.md) — renumérotation Torres Amat
- [traduction_kjv_1611.md](traduction_kjv_1611.md), [traduction_louis_segond_1910.md](traduction_louis_segond_1910.md), [traduction_riveduta_1927.md](traduction_riveduta_1927.md) — documents sur les traductions
