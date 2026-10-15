# Traduction française Bible du Rabbinat 1899 (`data/rabbinat_1899.txt`)

Ce document décrit la seconde traduction française de l'application :
son histoire, pourquoi elle a été ajoutée à côté de la Louis Segond 1910,
sa source numérique, le rendu du nom divin, et les particularités de
maintenance du fichier.

Sa numérotation est déjà massorétique (BHS), identique à la base BHSA :
aucun renumérotage n'a été nécessaire, contrairement à Segond/KJV/Riveduta
(versification chrétienne) et Torres Amat (Vulgate).

## 1. Contexte

La **Bible du Rabbinat** (« La Bible, traduite du texte original par les
membres du rabbinat français », direction Zadoc Kahn, Grand-Rabbin,
éditions A. Durlacher, Paris, 1899-1906) est la traduction de référence
du judaïsme francophone. Œuvre collective du rabbinat français
(avec notamment Lazare Wogue pour le Pentateuque et les livres
historiques), elle a été révisée plusieurs fois (1966, 1973, 1986…) mais
seule l'édition originale de 1899-1906 est dans le domaine public.

## 2. Pourquoi le Rabbinat en plus de la Segond

L'application analyse le texte massorétique : une traduction juive
calquée sur l'hébreu est un contrepoids utile à la Segond 1910,
traduction protestante synchronique de la même source mais de tradition
chrétienne.

| | YHWH (tétragramme) | Adonaï / Adoni | distingués ? |
|---|---|---|---|
| Segond 1910 | l'Éternel | Seigneur | oui |
| **Rabbinat 1899** | **l'Éternel** | **Seigneur / le Seigneur** | **oui** |

Vérifié sur le texte du fichier :

- **Gn 1:1** : *Au commencement, Dieu créa le ciel et la terre.*
  (le Rabbinat traduit *éch* par « ciel », singulier collectif, là où
  la Segond met « les cieux ») ;
- **Gn 15:2** (première occurrence d'Adonaï YHWH) : *Abram répondit:
  "Dieu-Éternel, que me donnerais-tu…"* ;
- **Ps 110:1** (YHWH + Adoni) : le titre au verset 1 précède
  *L'Éternel a dit à mon maître: "Assieds-toi à ma droite…"* ;
- **Ps 110:5** (Adonaï) : *Le Seigneur est à ta droite…*, distinct du
  « l'Éternel » du verset 1 ;
- **Ex 3:14** : *Je suis l'Être invariable!* (rendu propre au
  Rabbinat, là où Segond met « Je suis celui qui suis »).

La particularité la plus visible pour l'analyse : les **titres des
psaumes** sont comptés comme verset 1 par la massore (BHSA) — le fichier
les contient, alignés avec la base.

## 3. Source numérique

1. **Sefaria** — version « Bible du Rabbinat 1899 [fr] », texte issu de
   [fr.wikisource.org](https://fr.wikisource.org/wiki/Bible_du_Rabbinat)
   (domaine public), format JSON via l'API v3
   (`https://www.sefaria.org/api/v3/texts/`).
2. Le script `scripts/extract_rabbinat.py` télécharge les 39 livres
   protocanoniques de l'AT (une requête HTTP par livre) et écrit
   `data/rabbinat_1899.txt` au format plat du projet :

   ```
   <nom BHSA>\t<chapitre>\t<verset>\t<texte français>
   ```

   Les segments non-chaînés (notes de bas de page) sont ignorés, comme
   dans `bhsa_grammar.sefaria_client`.

C'est la même version Sefaria que celle déjà utilisée par
`bhsa_grammar.sefaria_client.py` pour l'enrichissement des sens par
binyan : le fichier `data/rabbinat_1899.txt` rend la traduction
disponible hors-ligne.

## 4. Versification

La source Sefaria suit la numérotation massorétique (BHS) :

- **Joël et Malachie : 4 chapitres** (contre 3 dans les Bibles
  chrétiennes) ;
- **titres des psaumes** : verset 1 (les versets suivants sont décalés
  de +1 par rapport à la KJV/Segond) ;
- **Deut 28:69** = 29:1 chrétien ; pas de fusion Psaumes 9/10, 113-114…

Aucun renumérotage n'a donc été appliqué : `scripts/renumber_translations.py`
ne doit **pas** être lancé sur ce fichier. Les 67 titres de psaumes
absents des traductions chrétiennes (en creux dans Segond/KJV/Riveduta)
sont ici présents.

## 5. Maintenance

- **Extraction** : `python scripts/extract_rabbinat.py` (39 requêtes,
  ~30 secondes ; réessais avec backoff, pauses de 0,3 s entre livres
  pour respecter l'API).
- **Aucun remappage** : le fichier est utilisé tel quel par
  `bhsa_grammar.translation.load_translation(language="rab")`.
- **Variable d'environnement** : `TRANSLATION_RAB_DATA` permet de
  pointer vers un fichier alternatif.
- **Comptes attendus** : 39 livres, 23 204 versets.
