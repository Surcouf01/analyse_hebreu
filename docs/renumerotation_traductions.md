# Renumérotation des traductions Segond, KJV et Riveduta (KJV → massorétique)

Ce document décrit la conversion de versification appliquée à
`data/louis_segond_1910.txt`, `data/kjv_1611.txt` et
`data/riveduta_1927.txt` par `scripts/renumber_translations.py`.
Il complète `renumerotation_torres_amat.md` (précédent équivalent pour
la traduction espagnole) et se veut la référence pour toute
maintenance future.

## 1. Contexte

Les traductions Segond 1910 (fr), King James Version 1611 (en) et
Riveduta Luzzi 1927 (it) sont des traductions chrétiennes de l'Ancien
Testament : elles suivent la **versification anglaise (KJV)** des
versets, qui diffère de la numérotation massorétique (BHS, celle de la
base BHSA) sur environ 120 chapitres :

- **regroupements de chapitres** : Joël (KJV 3 chapitres = BHSA 4) et
  Malachie (KJV 4 = BHSA 3:19-24) ;
- **versets en tête du chapitre suivant** : Genèse 31:55 = BHSA 32:1,
  Exode 7:26-29 = BHSA 8:1-4 (donc Exode KJV 8:5-32 = BHSA 8:1-28),
  Lévitique 5:20-26 = BHSA 6:1-7, Nombres 16:36-50 = BHSA 17:1-15,
  Nombres 25:19 + 26:1, Deut 12:32 = BHSA 13:1, Deut 22:30 = BHSA 23:1,
  Deut 28:69 = BHSA 29:1 (le fameux « 29:1 »), 1-2 Samuel, 1 Rois 4-5 et
  22, 2 Rois 11-12, 1 Chroniques 6 et 12, 2 Chroniques 2 et 14, Néhémie
  3-4, 7 et 9-10, Ésaïe 9 et 64, Jérémie 9, Ézéchiel 20-21, Daniel 3-6,
  Osée, Jonas 1:17-2, Michée 5, Nahum 1-2, Zacharie 1-2, Cantique 6-7,
  Ecclésiaste 4:17-5, Job 40-41, Esther (nombres) ;
- **titres des psaumes** : dans la BHSA le titre est compté comme verset
  1 ; les éditions KJV/Segond/Riveduta le fusionnent au verset 1 du
  texte. Environ 115 psaumes sont donc décalés de +1 (voire +2 pour les
  psaumes à double titre : Ps 51/52/54/60/108).

L'objectif : que le verset affiché par l'application pour `Joël 4:8`
(BHSA) soit le bon verset dans chaque traduction (KJV `Joel 3:8`,
Segond `Joël 3:8`, Riveduta `Gioele 3:8` renumérotés en `Joel 4:8`).

## 2. Source de la table de correspondance

La table est dérivée des tables **TVTMS** (*Translators Versification
Traditions with Methodology for Standardisation*, colonnes « English
KJV » et « Hebrew ») publiées par STEPBible :

- fichier `Versification/TVTMS - ... CC BY.txt` du dépôt
  [STEPBible/STEPBible-Data](https://github.com/STEPBible/STEPBible-Data)
  (© STEPBible.org, **CC BY 4.0**) ;
- les segments divergents ont été extraits automatiquement (une
  centaine de sections KJV↔hébreu), puis calibrés contre la base BHSA
  locale (`bhsa_repo/tf`) : structure de 23 213 versets de référence
  et contrôle des bornes de chaque chapitre.

En cas de divergence entre la table et la BHSA, la référence STEPBible
fait foi ; le script a été généré une fois et la table est figée dans
`_SEGMENTS`.

## 3. Méthode

Le script `scripts/renumber_translations.py` applique à chaque ligne
du fichier plat (`nom_BHSA\tchapitre\tverset\ttexte`) :

1. **segments** (`_SEGMENTS`) : la référence KJV `(livre, ch_kjv, v_kjv)`
   devient `(livre, ch_bhsa, v_bhsa)` lorsque les versifications
   divergent (1 966 versets renumérotés par fichier) ;
2. **versets KJV sans équivalent massorétique** (`_ENGLISH_ABSENT`) :
   trois versets KJV (Ésaïe 64:1, Néhémie 7:68, Psaume 13:6) sont
   fusionnés dans le verset hébreu précédent par les éditions
   chrétiennes ; leurs lignes sont supprimées (aucune perte de texte au
   sens BHSA) ;
3. **identité** : tous les autres versets sont inchangés (~85 % des
   versets) ;
4. **normalisation Segond** : trois livres de la Segond portaient des
   noms français introuvables dans la BHSA — `Osée` → `Hosea`,
   `Cantique Des Cantiques` → `Canticum`, `Lamentations De Jérémie` →
   `Threni` (468 versets renommés) ; le Nouveau Testament de la Segond
   (27 livres, sans équivalent BHSA) est recopié tel quel.

Deux catégories de versets restent « **en creux** » (pas de ligne,
l'application affiche « verset absent de la traduction »), comme pour
la Torres Amat :

- les **67 titres de psaumes** (BHSA v1 sans équivalent KJV : la ligne
  n'existe pas, le titre est dans le texte du verset suivant côté KJV) ;
- les **seconds versets des scissions** (4 cas : Nombres 26:1,
  1 Samuel 21:1, 1 Rois 22:44, 1 Chroniques 12:5) : le verset KJV
  fusionné est porté par la première référence BHSA de la paire.

## 4. Vérifications

Le script intègre ses propres contrôles et échoue en cas d'anomalie :

- **bornes** : zéro référence finale hors des bornes BHSA (les 23 213
  versets de référence définissent chapitre/verset valides) ;
- **unicité** : aucun doublon ni collision (deux versets source mappés
  vers la même référence BHSA) ;
- **comptes rendus** : nombre de versets, renumérotés, supprimés et
  renommés imprimés à chaque exécution.

Chiffres après conversion (Ancien Testament, 23 213 versets BHSA) :

| Fichier | Versets écrits | Renumérotés | Supprimés | En creux |
|---|---|---|---|---|
| `louis_segond_1910.txt` | 23 142 (AT) + 7 957 (NT) | 1 966 | 3 | 71 |
| `kjv_1611.txt` | 23 142 | 1 966 | 3 | 71 |
| `riveduta_1927.txt` | 23 142 | 1 966 | 3 | 71 |

(71 = 67 titres de psaumes + 4 seconds versets de scission.)

## 5. Maintenance

- Pour convertir un fichier : `python scripts/renumber_translations.py
  [fichier ...]` (sans argument, les trois fichiers par défaut). À
  n'appliquer **qu'une fois** : le script n'est pas idempotent, mais une
  seconde application est détectée (collisions de références) et
  refusée sans écriture.
- Pour recalibrer la table (mise à jour BHSA) : reprendre les sections
  KJV↔hébreu du fichier TVTMS de STEPBible (CC BY 4.0), extraire les
  paires divergentes et recalculer `_SEGMENTS` ; créditer STEPBible.
- Cas délicats connus : Esther (nombres décalés de un verset par
  chapitre pour les additions grecques — géré), Daniel 3 (KJV 3:24-30
  = BHSA 3:31-33 et KJV 4 = BHSA 4:1-37, additions deutéronomiques
  exclues des fichiers sources), Job 40-41 (chapitres décalés).

## 6. Crédits

Tables TVTMS © STEPBible.org, publiées sous licence
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) dans le
dépôt [STEPBible/STEPBible-Data](https://github.com/STEPBible/STEPBible-Data).
Merci de référencer ce dépôt comme source de la donnée de versification.
