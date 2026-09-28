# Traduction anglaise King James Version 1611 (`data/kjv_1611.txt`)

Ce document décrit la traduction anglaise de l'application : son
histoire, sa source numérique, le rendu du nom divin, et les
particularités de maintenance du fichier.

La KJV suit la versification anglaise (KJV) : Joël et Malachie ont
3 chapitres, les titres des psaumes sont fusionnés au verset 1, etc.
Le fichier `data/kjv_1611.txt` a donc été renuméroté vers la
versification BHSA par `scripts/renumber_translations.py` (voir
`renumerotation_traductions.md`).

## 1. Contexte

La **King James Version** (KJV, « Authorised Version », 1611, public
domain) est la traduction anglaise historique, commandée par Jacques Ier
et produite par environ 50 érudits en trois comités. Elle a été
traduite depuis l'hébreu massorétique pour l'AT et le grec (Texte reçu)
pour le NT. Le texte utilisé ici est celui de l'édition courante
(l'édition de 1611 elle-même comportait des variantes d'orthographe
qui ont été normalisées au fil des réimpressions du XVIIe siècle).

## 2. Source numérique

1. **JSON source** — dépôt
   [joe-dakroub/data_bible-json](https://github.com/joe-dakroub/data_bible-json)
   (public domain, format API.bible), distribution numérique
   courante de la KJV.
2. **Fichier du projet** — `data/kjv_1611.txt`, conversion vers le
   format texte plat du projet :
   `nom_BHSA\tchapitre\tverset\ttexte_anglais` (une ligne par verset,
   en-têtes `#`, UTF-8), avec nettoyage HTML (numéros de verset
   retirés).

## 3. Contenu

- **39 livres** : les livres protocanoniques de l'AT uniquement (noms
  BHSA latins : Genesis, Reges_I, Psalmi…). Le NT n'est pas inclus.
- **23 145 versets** (même couverture que la Riveduta).

## 4. Rendu du nom divin

La KJV suit la convention héritée de la Septante et de la Vulgate :

- **tétragramme YHWH** → **« the LORD »** en petites majuscules dans
  les éditions imprimées ; dans la source numérique utilisée, le
  marquage typographique est perdu et le mot apparaît en capitales
  (`LORD`, 6 565 occurrences du mot dans le fichier, YHWH Sabaoth
  compris : *the LORD of hosts*) ;
- **Adonaï** → « the Lord » ; **Adonaï + YHWH** → « the Lord GOD »
  (Gn 15:2 : *"And Abram said, Lord GOD, what wilt thou give me…"*) ;
- **Élohim** → « God » ; **Élohim + YHWH** → « the LORD God » ;
- le tétragramme apparaît en clair quatre fois : **JEHOVAH** en Ex 6:3,
  Ps 83:18, És 12:2, És 26:4 (Ex 6:3 : *"by my name JEHOVAH was I not
  known to them"*).

Exemples de versets de contrôle :

| Référence | KJV | Segond 1910 | Riveduta 1927 |
|---|---|---|---|
| Gn 15:2 | Lord GOD | Seigneur Éternel | Signore, Eterno |
| Ps 110:1 | The LORD … my Lord | l'Éternel … mon Seigneur | L'Eterno … il mio Signore |
| Ex 3:14 | I AM THAT I AM | Je suis celui qui suis | Io sono quegli che sono |

## 5. Particularités de la source

- La perte du marquage « petites majuscules » de l'édition imprimée
  fait que **YHWH (LORD) et Adonaï (Lord) ne sont plus distinguables
  à la seule vue du fichier** — sauf dans les quatre occurrences
  JEHOVAH et les cas combinés « Lord GOD » (Adonaï YHWH). Pour une
  comparaison fine du nom divin, préférer la Riveduta (l'Eterno /
  Signore) ou la Segond (l'Éternel / Seigneur).
- Le pilcrow `¶` (marque de paragraphe de l'édition imprimée) est
  conservé dans certaines lignes (p. ex. Chronica_I 1:5) ; c'est le
  texte de la source.
- Typographie ancienne : virgules et points-virgules sans espace
  consécutif, majuscules de la source conservées.

## 6. Maintenance

- Fichier régénérable depuis le JSON source (format API.bible) par
  tout script de conversion au format plat ; l'en-tête du fichier
  documente la source exacte.
- Pour remplacer le fichier : variable d'environnement
  `TRANSLATION_EN_DATA` (chemin vers un `.txt` plat), sinon
  `data/kjv_1611.txt`.
- Le format attendu est documenté dans la docstring de
  `bhsa_grammar/translation.py`.
