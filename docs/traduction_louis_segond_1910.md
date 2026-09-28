# Traduction française Louis Segond 1910 (`data/louis_segond_1910.txt`)

Ce document décrit la traduction française de l'application : son
histoire, sa source numérique, le rendu du nom divin, et les
particularités de maintenance du fichier.

L'application n'analyse que l'hébreu (BHSA) ; pour les livres de
l'Ancien Testament, le fichier suit la versification chrétienne
(KJV) : Joël et Malachie 3 chapitres, titres des psaumes fusionnés,
Exode 7-8, Deut 28:69, etc. Le fichier `data/louis_segond_1910.txt` a
donc été renuméroté vers la versification BHSA par
`scripts/renumber_translations.py`, qui normalise aussi trois noms de
livres français vers les noms BHSA (Osée → Hosea, Cantique Des
Cantiques → Canticum, Lamentations De Jérémie → Threni) — voir
`renumerotation_traductions.md`.

## 1. Contexte

La **Bible Louis Segond** (Louis Segond, 1810-1885, domaine public) est
la traduction protestante francophone la plus diffusée. Ancien
Testament paru en 1874 (commande de la Compagnie des pasteurs de
Genève), Nouveau Testament et Bible complète en 1880, révisée
notamment en 1910 (aussi « Segond révisée » ou LSG 1910). Segond a
traduit depuis l'hébreu (texte massorétique) pour l'AT et le grec
(Texte reçu) pour le NT.

## 2. Source numérique

1. **JSON source** — dépôt [juliend2/data-bible](https://github.com/juliend2/data-bible),
   fichier `db/seed_data/louis-segond-formatted.json` (CC0 / domaine
   public), structure `Testaments → Books → Chapters → Verses`.
   C'est le même fichier que celui accepté directement par
   `bhsa_grammar/translation.py` au format JSON (chemin d'env
   `TRANSLATION_DATA` avec extension `.json`).
2. **Fichier du projet** — `data/louis_segond_1910.txt`, conversion du
   JSON vers le format texte plat du projet :
   `nom_BHSA\tchapitre\tverset\ttexte_français` (une ligne par verset,
   en-têtes `#`, UTF-8).

La conversion des noms de livre se fait via
`bhsa_grammar.reference.normalize_book` (le JSON source porte des noms
français : « Genèse », « 1 Corinthiens », etc. ; le format plat porte
des noms BHSA latins : Genesis, Reges_I, etc.).

## 3. Contenu

- **66 livres** : les 39 livres protocanoniques de l'AT (noms BHSA
  latins) **et les 27 livres du Nouveau Testament** (noms français :
  « Matthieu », « 1 Corinthiens », « Apocalypse »…). C'est la seule
  traduction fournie qui couvre le NT.
- **31 102 versets** au total.
- L'application n'utilise que les 39 livres de l'AT ; les livres du NT
  sont sans effet pour l'analyse (ils sont simplement ignorés lors des
  recherches par référence BHSA, qui n'indexent que l'AT).

## 4. Rendu du nom divin

Segond 1910 suit la convention protestante classique :

- **tétragramme YHWH** → « l'Éternel » (6 968 occurrences du mot
  « Éternel » dans le fichier) ;
- **Adonaï** → « Seigneur » ; **Adonaï + YHWH** → « Seigneur Éternel »
  (Gn 15:2 : *« Abram répondit: Seigneur Éternel, que me donneras-tu? »*) ;
- **Élohim** → « Dieu » ; **Élohim + YHWH** → « Éternel Dieu »
  (Gn 2:4 : *« l'Éternel Dieu fit une terre et des ciels »*) ;
- **YHWH Sabaoth** → « l'Éternel des armées » (És 6:3 : *« Saint, saint,
  saint est l'Éternel des armées ! »*).

Exemples de versets de contrôle (comparaison utile avec les autres
traductions du projet) :

| Référence | Segond 1910 | Riveduta 1927 |
|---|---|---|
| Gn 15:2 (Adonaï YHWH) | Seigneur Éternel | Signore, Eterno |
| Ps 110:1 (YHWH + Adoni) | l'Éternel … mon Seigneur | L'Eterno … il mio Signore |
| Ex 3:14 | Je suis celui qui suis | Io sono quegli che sono |

## 5. Particularités de la source

- Typographie ancienne : ponctuation collée (`sans enfants; et`),
  absence d'espaces insécables ; le texte n'a pas été modernisé.
- Certains versets sont précédés de leur titre (`De David. Psaume.` en
  Ps 110:1, conservé dans le fichier) — c'est le texte de la source.
- La numérotation de Segond diffère parfois de celle de la BHSA (par
  exemple *1 Rois 22* s'arrête à 22:53 en Segond contre 22:54 dans la
  BHSA) ; dans ce cas l'application affiche que le verset est absent
  de la traduction. Ces écarts sont inhérents à l'édition Segond 1910
  et ne sont pas corrigeables par table.

## 6. Maintenance

- Fichier régénérable depuis le JSON source via la fonction
  `_parse_json` de `bhsa_grammar/translation.py` (référence de
  structure) ou tout script de conversion au format plat.
- Pour remplacer le fichier : variable d'environnement
  `TRANSLATION_DATA` (chemin vers un `.txt` plat ou un `.json` du
  format juliend2/data-bible), sinon `data/louis_segond_1910.txt`.
- Le format attendu est documenté dans l'en-tête du fichier et la
  docstring de `bhsa_grammar/translation.py`.
