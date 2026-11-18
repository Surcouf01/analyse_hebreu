#!/usr/bin/env python3
"""Déplace les titres (superscriptions) des psaumes au verset 1 BHSA.

Après `scripts/renumber_translations.py`, les éditions KJV/Segond/Riveduta
ont leurs titres de psaumes fusionnés au début du premier verset du texte
(p. ex. `Psalmi 48:2` commence par « Cantique. Psaume des fils de Koré. »,
texte du verset 1 massorétique, tandis que le verset 1 est absent « en creux »).
Dans la versification BHSA affichée par l’application, le titre est le
verset 1 : ce script le détache et le place en `Psalmi <chapitre> 1`
(et en verset 2 pour les quatre psaumes à double titre 51/52/54/60),
comme le font déjà les traductions Rabbinat 1899 et Torres Amat 1823.

Résultat : ouvrir « Psaume 48:2 » affiche la traduction du verset 2
(« L’Éternel est grand… ») sans le titre du verset 1 en préfixe.

La table `_TITLES` contient, pour chaque fichier et chaque psaume titré,
le texte exact du titre (v1, et v2 pour les doubles titres). Chaque entrée
est vérifiée à l’exécution : le verset fusionné doit commencer par le
titre, sinon le script refuse sans écrire. Une seconde exécution est
sans effet (verset 1 déjà présent -> ignoré).

Usage :
    python scripts/split_psalm_titles.py            # les trois fichiers data/
    python scripts/split_psalm_titles.py --check    # vérification seule
    python scripts/split_psalm_titles.py data/kjv_1611.txt
"""

import argparse
import os
import re
import sys

# {nom_fichier: {chapitre: (titre_v1,) ou (titre_v1, titre_v2)}}
# (titre_v1, None, reste) force un reste explicite (KJV Ps 18 : artéfacte
# « Saul: And he said,I will love » dans la source, nettoyé ici).
_TITLES = {
    "louis_segond_1910.txt": {
        3: ("Psaume de David. A l'occasion de sa fuite devant Absalom, son fils.",),
        4: ("Au chef des chantres. Avec instruments à cordes. Psaume de David.",),
        5: ("Au chef des chantres. Avec les flûtes. Psaume de David.",),
        6: ("Au chef des chantres. Avec instruments à cordes. Sur la harpe à huit cordes. Psaume de David.",),
        7: ("Complainte de David. Chantée à l'Éternel, au sujet de Cusch, Benjamite.",),
        8: ("Au chef des chantres. Sur la guitthith. Psaume de David.",),
        9: ("Au chef des chantres. Sur «Meurs pour le fils». Psaume de David.",),
        12: ("Au chef des chantres. Sur la harpe à huit cordes. Psaume de David.",),
        13: ("Au chef des chantres. Psaume de David.",),
        18: ("Au chef des chantres. Du serviteur de l'Éternel, de David, qui adressa à l'Éternel les paroles de ce cantique, lorsque l'Éternel l'eut délivré de la main de tous ses ennemis et de la main de Saül.",),
        19: ("Au chef des chantres. Psaume de David.",),
        20: ("Au chef des chantres. Psaume de David.",),
        21: ("Au chef des chantres. Psaume de David.",),
        22: ("Au chef des chantres. Sur «Biche de l'aurore». Psaume de David.",),
        30: ("Psaume. Cantique pour la dédicace de la maison. De David.",),
        31: ("Au chef des chantres. Psaume de David.",),
        34: ("De David. Lorsqu'il contrefit l'insensé en présence d'Abimélec, et qu'il s'en alla chassé par lui.",),
        36: ("Au chef des chantres. Du serviteur de l'Éternel, de David.",),
        38: ("Psaume de David. Pour souvenir.",),
        39: ("Au chef des chantres. A Jeduthun, Psaume de David.",),
        40: ("Au chef des chantres. De David. Psaume.",),
        41: ("Au chef des chantres. Psaume de David.",),
        42: ("Au chef des chantres. Cantique des fils de Koré.",),
        44: ("Au chef des chantres. Des fils de Koré. Cantique.",),
        45: ("Au chef des chantres. Sur les lis. Des fils de Koré. Cantique. Chant d'amour.",),
        46: ("Au chef des chantres. Des fils de Koré. Sur alamoth. Cantique.",),
        47: ("Au chef des chantres. Des fils de Koré. Psaume.",),
        48: ("Cantique. Psaume des fils de Koré.",),
        49: ("Au chef des chantres. Des fils de Koré. Psaume.",),
        51: ("Au chef des chantres. Psaume de David.", "Lorsque Nathan, le prophète, vint à lui, après que David fut allé vers Bath-Schéba.",),
        52: ("Au chef des chantres. Cantique de David.", "A l'occasion du rapport que Doëg, l'Édomite, vint faire à Saül, en lui disant: David s'est rendu dans la maison d'Achimélec.",),
        53: ("Au chef des chantres. Sur la flûte. Cantique de David.",),
        54: ("Au chef des chantres. Avec instruments à cordes. Cantique de David.", "Lorsque les Ziphiens vinrent dire à Saül: David n'est-il pas caché parmi nous?",),
        55: ("Au chef des chantres. Avec instruments à cordes. Cantique de David.",),
        56: ("Au chef des chantres. Sur «Colombe des térébinthes lointains». Hymne de David. Lorsque les Philistins le saisirent à Gath.",),
        57: ("Au chef des chantres. «Ne détruis pas». Hymne de David. Lorsqu'il se réfugia dans la caverne, poursuivi par Saül.",),
        58: ("Au chef des chantres. «Ne détruis pas». Hymne de David.",),
        59: ("Au chef des chantres. «Ne détruis pas». Hymne de David. Lorsque Saül envoya cerner la maison, pour le faire mourir.",),
        60: ("Au chef des chantres. Sur le lis lyrique. Hymne de David, pour enseigner.", "Lorsqu'il fit la guerre aux Syriens de Mésopotamie et aux Syriens de Tsoba, et que Joab revint et battit dans la vallée du sel douze mille Édomites.",),
        61: ("Au chef des chantres. Sur instruments à cordes. De David.",),
        62: ("Au chef des chantres. D'après Jeduthun. Psaume de David.",),
        63: ("Psaume de David. Lorsqu'il était dans le désert de Juda.",),
        64: ("Au chef des chantres. Psaume de David.",),
        65: ("Au chef des chantres. Psaume de David. Cantique.",),
        67: ("Au chef des chantres. Avec instruments à cordes. Psaume. Cantique.",),
        68: ("Au chef des chantres. De David. Psaume. Cantique.",),
        69: ("Au chef des chantres. Sur les lis. De David.",),
        70: ("Au chef des chantres. De David. Pour souvenir.",),
        75: ("Au chef des chantres. «Ne détruis pas». Psaume d'Asaph. Cantique.",),
        76: ("Au chef des chantres. Avec instruments à cordes. Psaume d'Asaph. Cantique.",),
        77: ("Au chef des chantres. D'après Jeduthun. Psaume d'Asaph.",),
        80: ("Au chef des chantres. Sur les lis lyriques. D'Asaph. Psaume.",),
        81: ("Au chef des chantres. Sur la guitthith. D'Asaph.",),
        83: ("Cantique. Psaume d'Asaph.",),
        84: ("Au chef des chantres. Sur la guitthith. Des fils de Koré. Psaume.",),
        85: ("Au chef des chantres. Des fils de Koré. Psaume.",),
        88: ("Cantique. Psaume des fils de Koré. Au chef des chantres. Pour chanter sur la flûte. Cantique d'Héman, l'Ézrachite.",),
        89: ("Cantique d'Éthan, l'Ézrachite.",),
        92: ("Psaume. Cantique pour le jour du sabbat.",),
        102: ("Prière d'un malheureux, lorsqu'il est abattu et qu'il répand sa plainte devant l'Éternel.",),
        108: ("Cantique. Psaume de David.",),
        140: ("Au chef des chantres. Psaume de David.",),
        142: ("Cantique de David. Lorsqu'il était dans la caverne. Prière.",),
    },
    "kjv_1611.txt": {
        3: ("A Psalm of David, when he fled from Absalom his son.",),
        4: ("To the chief Musician on Neginoth, A Psalm of David.",),
        5: ("To the chief Musician upon Nehiloth, A Psalm of David.",),
        6: ("To the chief Musician on Neginoth upon Sheminith, A Psalm of David.",),
        7: ("Shiggaion of David, which he sang unto the LORD, concerning the words of Cush the Benjamite.",),
        8: ("To the chief Musician upon Gittith, A Psalm of David.",),
        9: ("To the chief Musician upon Muthlabben, A Psalm of David.",),
        12: ("To the chief Musician upon Sheminith, A Psalm of David.",),
        13: ("To the chief Musician, A Psalm of David.",),
        18: ("To the chief Musician, A Psalm of David, the servant of the LORD, who spake unto the LORD the words of this song in the day that the LORD delivered him from the hand of all his enemies, and from the hand of Saul.", None, "And he said, I will love thee, O LORD, my strength.",),
        19: ("To the chief Musician, A Psalm of David.",),
        20: ("To the chief Musician, A Psalm of David.",),
        21: ("To the chief Musician, A Psalm of David.",),
        22: ("To the chief Musician upon Aijeleth Shahar, A Psalm of David.",),
        30: ("A Psalm and Song at the dedication of the house of David.",),
        31: ("To the chief Musician, A Psalm of David.",),
        34: ("A Psalm of David, when he changed his behaviour before Abimelech; who drove him away, and he departed.",),
        36: ("To the chief Musician, A Psalm of David the servant of the LORD.",),
        38: ("A Psalm of David, to bring to remembrance.",),
        39: ("To the chief Musician, even to Jeduthun, A Psalm of David.",),
        40: ("To the chief Musician, A Psalm of David.",),
        41: ("To the chief Musician, A Psalm of David.",),
        42: ("To the chief Musician, Maschil, for the sons of Korah.",),
        44: ("To the chief Musician for the sons of Korah, Maschil.",),
        45: ("To the chief Musician upon Shoshannim, for the sons of Korah, Maschil, A Song of loves.",),
        46: ("To the chief Musician for the sons of Korah, A Song upon Alamoth.",),
        47: ("To the chief Musician, A Psalm for the sons of Korah.",),
        48: ("A Song and Psalm for the sons of Korah.",),
        49: ("To the chief Musician, A Psalm for the sons of Korah.",),
        51: ("To the chief Musician, A Psalm of David,", "when Nathan the prophet came unto him, after he had gone in to Bath-sheba.",),
        52: ("To the chief Musician, Maschil, A Psalm of David,", "when Doeg the Edomite came and told Saul, and said unto him, David is come to the house of Ahimelech.",),
        53: ("To the chief Musician upon Mahalath, Maschil, A Psalm of David.",),
        54: ("To the chief Musician on Neginoth, Maschil, A Psalm of David,", "when the Ziphims came and said to Saul, Doth not David hide himself with us?",),
        55: ("To the chief Musician on Neginoth, Maschil, A Psalm of David.",),
        56: ("To the chief Musician upon Jonath-elem-rechokim, Michtam of David, when the Philistines took him in Gath.",),
        57: ("To the chief Musician, Al-taschith, Michtam of David, when he fled from Saul in the cave.",),
        58: ("To the chief Musician, Al-taschith, Michtam of David.",),
        59: ("To the chief Musician, Al-taschith, Michtam of David; when Saul sent, and they watched the house to kill him.",),
        60: ("To the chief Musician upon Shushan-eduth, Michtam of David, to teach;", "when he strove with Aram-naharaim and with Aram-zobah, when Joab returned, and smote of Edom in the valley of salt twelve thousand.",),
        61: ("To the chief Musician upon Neginah, A Psalm of David.",),
        62: ("To the chief Musician, to Jeduthun, A Psalm of David.",),
        63: ("A Psalm of David, when he was in the wilderness of Judah.",),
        64: ("To the chief Musician, A Psalm of David.",),
        65: ("To the chief Musician, A Psalm and Song of David.",),
        67: ("To the chief Musician on Neginoth, A Psalm or Song.",),
        68: ("To the chief Musician, A Psalm or Song of David.",),
        69: ("To the chief Musician upon Shoshannim, A Psalm of David.",),
        70: ("To the chief Musician, A Psalm of David, to bring to remembrance.",),
        75: ("To the chief Musician, Al-taschith, A Psalm or Song of Asaph.",),
        76: ("To the chief Musician on Neginoth, A Psalm or Song of Asaph.",),
        77: ("To the chief Musician, to Jeduthun, A Psalm of Asaph.",),
        80: ("To the chief Musician upon Shoshannim-eduth, A Psalm of Asaph.",),
        81: ("To the chief Musician upon Gittith, A Psalm of Asaph.",),
        83: ("A Song or Psalm of Asaph.",),
        84: ("To the chief Musician upon Gittith, A Psalm for the sons of Korah.",),
        85: ("To the chief Musician, A Psalm for the sons of Korah.",),
        88: ("A Song or Psalm for the sons of Korah, to the chief Musician upon Mahalath Leannoth, Maschil of Heman the Ezrahite.",),
        89: ("Maschil of Ethan the Ezrahite.",),
        92: ("A Psalm or Song for the sabbath day.",),
        102: ("A Prayer of the afflicted, when he is overwhelmed, and poureth out his complaint before the LORD.",),
        108: ("A Song or Psalm of David.",),
        140: ("To the chief Musician, A Psalm of David.",),
        142: ("Maschil of David; A Prayer when he was in the cave.",),
    },
    "riveduta_1927.txt": {
        3: ("Salmo di Davide composto quand'egli fuggì dinanzi ad Absalom suo figliuolo.",),
        4: ("Al Capo de' musici. Per strumenti a corda. Salmo di Davide.",),
        5: ("Al Capo de' musici. Per strumenti a fiato. Salmo di Davide.",),
        6: ("Al Capo de' musici. Per strumenti a corda. Su Sheminith. Salmo di Davide.",),
        7: ("Shiggaion di Davide ch'egli cantò all'Eterno, a proposito delle parole di Cush, beniaminita.",),
        8: ("Al Capo de' musici. Sulla Ghittea. Salmo di Davide.",),
        9: ("Al Capo dei musici. Su \"Muori pel figlio\". Salmo di Davide.",),
        12: ("Al Capo de' musici. Sopra l'ottava. Salmo di Davide.",),
        13: ("Al Capo de' musici. Salmo di Davide.",),
        18: ("Al Capo de' musici. Di Davide, servo dell'Eterno, il quale rivolse all'Eterno le parole di questo cantico quando l'Eterno l'ebbe riscosso dalla mano di tutti i suoi nemici e dalla mano di Saul.",),
        19: ("Al Capo dei musici. Salmo di Davide.",),
        20: ("Al Capo de' musici. Salmo di Davide.",),
        21: ("Per il Capo de' musici. Salmo di Davide.",),
        22: ("Per il Capo de' musici. Su \"Cerva dell'aurora\". Salmo di Davide.",),
        30: ("Salmo. Cantico per la dedicazione della Casa. Di Davide.",),
        31: ("Per il Capo de' musici. Salmo di Davide.",),
        34: ("Di Davide, quando si finse insensato davanti ad Abimelec e, cacciato da lui, se ne andò.",),
        36: ("Per il Capo de' musici. Di Davide, servo dell'Eterno.",),
        38: ("Salmo di Davide. Per far ricordare.",),
        39: ("Per il Capo de' musici. Per Jeduthun. Salmo di Davide.",),
        40: ("Per il Capo de' musici. Di Davide. Salmo.",),
        41: ("Per il Capo de' musici. Salmo di Davide.",),
        42: ("Per il Capo de' musici. Cantico de' figliuoli di Core.",),
        44: ("Al capo de' musici. Dei figliuoli di Core. Cantico.",),
        45: ("Per il Capo de' musici. Sopra \"i gigli\". De' figliuoli di Core. Cantico. Inno nuziale.",),
        46: ("Per il Capo de' musici. Dei figliuoli di Core. Per voci di fanciulle. Canto.",),
        47: ("Per il Capo de' musici. Dei figliuoli di Core. Salmo.",),
        48: ("Canto. Salmo de' figliuoli di Core.",),
        49: ("Per il Capo de' musici. De' figliuoli di Core. Salmo.",),
        51: ("Per il Capo de' musici. Salmo di Davide,", "quando il profeta Natan venne a lui, dopo che Davide era stato da Batseba.",),
        52: ("Per il Capo de' musici. Cantico di Davide,", "quando Doeg l'Edomita venne a riferire a Saul che Davide era entrato in casa di Ahimelec.",),
        53: ("Al Capo de' musici. Mestamente. Cantico di Davide.",),
        54: ("Per il Capo de' musici. Per strumenti a corda. Cantico di Davide", "quando gli Zifei vennero a dire a Saul: Davide non si tiene egli nascosto fra noi?",),
        55: ("Per il Capo de' musici. Per strumenti a corda. Cantico di Davide.",),
        56: ("Per il Capo de' musici. Su: \"Colomba de' terebinti lontani\". Inno di Davide quando i Filistei lo presero in Gat.",),
        57: ("Per il Capo de' musici. \"Non distruggere\". Inno di Davide, quando, perseguitato da Saul, fuggì nella spelonca.",),
        58: ("Per il Capo de' musici. \"Non distruggere\". Inno di Davide.",),
        59: ("Per il Capo de' musici. \"Non distruggere\". Inno di Davide, quando Saul mandò a guardargli la casa per ucciderlo.",),
        60: ("Per il Capo de' musici. Su \"il giglio della testimonianza\". Inno di Davide da insegnare;", "quand'egli mosse guerra ai Siri di Mesopotamia e ai Siri di Soba e Joab tornò, e sconfisse 12.000 Idumei nella valle del Sale.",),
        61: ("Per il Capo de' musici. Per strumenti a corda. Di Davide.",),
        62: ("Per il Capo de' musici. Per Jeduthun. Salmo di Davide.",),
        63: ("Salmo di Davide: quand'era nel deserto di Giuda.",),
        64: ("Per il Capo de' musici. Salmo di Davide.",),
        65: ("Per il Capo de' musici. Salmo di Davide. Canto.",),
        67: ("Per il Capo de' musici. Per strumenti a corda. Salmo. Canto.",),
        68: ("Al Capo de' musici. Di Davide. Salmo. Canto.",),
        69: ("Al Capo de' musici. Sopra \"i gigli\". Di Davide.",),
        70: ("Per il Capo de' musici. Di Davide; per far ricordare.",),
        75: ("Per il Capo de' musici. \"Non distruggere\". Salmo di Asaf. Canto.",),
        76: ("Per il Capo de' Musici. Per strumenti a corda. Salmo di Asaf. Canto.",),
        77: ("Per il Capo de' Musici. Secondo Jeduthun. Salmo di Asaf.",),
        80: ("Per il Capo de' musici. Sopra \"i gigli della testimonianza\". Salmo di Asaf.",),
        81: ("Per il Capo de' musici. Sulla Ghittea. Salmo di Asaf.",),
        83: ("Canto. Salmo di Asaf.",),
        84: ("Per il Capo de' musici. Sulla Ghittea. Salmo de' figliuoli di Kore.",),
        85: ("Per il Capo de' musici. Salmo de' figliuoli di Kore.",),
        88: ("Canto. Salmo dei figliuoli di Kore. Per il Capo de' musici. Da cantarsi mestamente. Cantico di Heman, l'Ezrahita.",),
        89: ("Cantico di Etan l'Ezrahita.",),
        92: ("Salmo. Canto per il giorno del sabato.",),
        102: ("Preghiera dell'afflitto quand'è abbattuto e spande il suo lamento dinanzi all'Eterno.",),
        108: ("Canto. Salmo di Davide.",),
        140: ("Per il Capo de' musici. Salmo di Davide.",),
        142: ("Cantico di Davide, quand'era nella spelonca. Preghiera.",),
    },
}


_DEFAULT_FILES = ("data/louis_segond_1910.txt", "data/kjv_1611.txt", "data/riveduta_1927.txt")


def _check_prefix(merged, prefix):
    if merged.startswith(prefix):
        return len(prefix)
    # tolérance : la source peut avoir une ponctuation différente en fin
    # de titre (KJV Ps 18 : « … from the hand of Saul: » au lieu de « Saul. »)
    stem = prefix.rstrip(".?!,;:")
    if stem and merged.startswith(stem):
        return len(stem)
    return -1


def split_file(path, table, check_only=False):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    first_verse = {}
    has_v1 = set()
    for line in lines:
        p = line.split("\t")
        if len(p) >= 4 and p[0] == "Psalmi" and p[1].isdigit() and p[2].isdigit():
            ch, v = int(p[1]), int(p[2])
            if v == 1:
                has_v1.add(ch)
            if ch not in first_verse or v < first_verse[ch]:
                first_verse[ch] = v
    out = []
    report = []
    done = set()
    for line in lines:
        p = line.split("\t")
        ch = int(p[1]) if len(p) >= 4 and p[0] == "Psalmi" and p[1].isdigit() else None
        v = int(p[2]) if ch is not None and p[2].isdigit() else None
        if (ch in table and ch not in has_v1 and ch not in done
                and v == first_verse.get(ch)):
            entry = table[ch]
            title_v1 = entry[0]
            title_v2 = entry[1] if len(entry) > 1 else None
            forced_rest = entry[2] if len(entry) > 2 else None
            merged = p[3]
            prefix = title_v1 if title_v2 is None else title_v1 + " " + title_v2
            n = _check_prefix(merged, prefix)
            if n < 0:
                raise RuntimeError(
                    f"{path}: Ps {ch}:{v} ne commence pas par le titre attendu:\n{merged[:120]}")
            if forced_rest is not None:
                remainder = forced_rest
            else:
                # nettoie un éventuel artefact de la source en tête de reste
                # (Riveduta OSIS : « .} » entre le titre et le verset)
                remainder = re.sub(r"^[\s.?!,;:}]+", "", merged[n:])
            if not remainder:
                raise RuntimeError(f"{path}: Ps {ch}: verset restant vide")
            out.append(f"Psalmi\t{ch}\t1\t{title_v1}")
            if title_v2 is not None:
                out.append(f"Psalmi\t{ch}\t2\t{title_v2}")
            out.append(f"Psalmi\t{ch}\t{v}\t{remainder}")
            tag = "v1+v2" if title_v2 is not None else "v1"
            report.append(f"Ps {ch}: titre -> {tag}, v{v} nettoyé")
            done.add(ch)
        else:
            out.append(line)
    for ch in sorted(set(table) - done - has_v1):
        report.append(f"Ps {ch}: verset 1 déjà présent, ignoré")
    if not check_only:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", help="fichiers plats à corriger (défaut: les trois data/)")
    ap.add_argument("--check", action="store_true", help="vérifie sans écrire")
    args = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = args.files or [os.path.join(here, f) for f in _DEFAULT_FILES]
    status = 0
    for path in files:
        name = os.path.basename(path)
        table = _TITLES.get(name)
        if table is None:
            print(f"{name}: pas dans la table, ignoré")
            continue
        if not os.path.isfile(path):
            print(f"{name}: fichier introuvable ({path})")
            status = 1
            continue
        try:
            report = split_file(path, table, check_only=args.check)
        except RuntimeError as exc:
            print(f"ERREUR {exc}")
            status = 1
            continue
        print(f"== {name} ({len(report)} psaumes)")
        for line in report:
            print("   " + line)
    return status


if __name__ == "__main__":
    sys.exit(main())
