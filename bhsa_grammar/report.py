"""Formatage du rapport d'analyse grammaticale (texte et JSON)."""

import json


def _indent_block(text, n):
    pad = "  " * n
    return "\n".join(pad + line for line in text.splitlines())


def to_text(analysis, verbose_words=True):
    """Formate le résultat de ``analyze_verse`` en texte lisible."""
    lines = []
    ref = analysis["reference"]
    book, ch, vs = ref
    lines.append(f"=== {book} {ch}:{vs} ===")
    lines.append(analysis["text"].strip())
    lines.append("")

    for si, sent in enumerate(analysis["sentences"], 1):
        lines.append(f"-- Phrase {si} --")
        lines.append(sent["text"].strip())
        lines.append("")
        for ci, clause in enumerate(sent["clauses"], 1):
            lines.append(f"  · Clause {ci} : {clause['text'].strip()}")
            for r in clause["rules"]:
                lines.append(f"      ↳ {r}")
            for pi, phrase in enumerate(clause["phrases"], 1):
                lines.append(f"      • Syntagme {pi} : {phrase['text'].strip()}")
                for r in phrase["rules"]:
                    lines.append(f"          ↳ {r}")
                if verbose_words:
                    for word in phrase["words"]:
                        lex = f"  ({word['lex']})" if word["lex"] else ""
                        gloss_fr = word.get("gloss_fr") or ""
                        gloss_en = word.get("gloss") or ""
                        gloss = f"  « {gloss_fr} »" if gloss_fr else (f"  « {gloss_en} »" if gloss_en else "")
                        lines.append(f"            ‣ {word['text'].strip()}{lex}{gloss}")
                        for r in word["rules"]:
                            lines.append(f"              ↳ {r}")
            lines.append("")
    return "\n".join(lines)


def to_json(analysis, indent=2, ensure_ascii=False):
    return json.dumps(analysis, indent=indent, ensure_ascii=ensure_ascii)


def to_summary(analysis):
    """Version condensée : liste plate des règles détectées par niveau."""
    rules = {"clause": [], "phrase": [], "word": []}
    for sent in analysis["sentences"]:
        for clause in sent["clauses"]:
            rules["clause"].extend(clause["rules"])
            for phrase in clause["phrases"]:
                rules["phrase"].extend(phrase["rules"])
                for word in phrase["words"]:
                    rules["word"].extend(word["rules"])
    # dédoublonnage en préservant l'ordre
    for k in rules:
        rules[k] = list(dict.fromkeys(rules[k]))
    return rules


def word_to_text(word_analysis):
    """Formate le résultat de ``analyze_word`` en texte lisible."""
    lines = []
    lines.append(f"=== Mot analysé : {word_analysis['input']} ===")
    if not word_analysis["found"]:
        lines.append("Aucune occurrence trouvée dans la base BHSA.")
        lines.append("")
        lines.append("Astuces :")
        lines.append("  - Saisir le mot avec le nikkud mais sans les teamim.")
        lines.append("  - Les préfixes (ב/כ/ל/מ/ו/ה/ש) peuvent rester attachés ;")
        lines.append("    ils seront détachés automatiquement.")
        lines.append("  - Essayer aussi la forme sans nikkud (consonnes seules).")
        return "\n".join(lines)

    lines.append(f"{len(word_analysis['matches'])} analyse(s) morphologique(s) trouvée(s) :")
    lines.append("")
    for i, m in enumerate(word_analysis["matches"], 1):
        lines.append(f"-- Analyse {i} ({m['count']} occurrence(s)) --")
        if m["method"] == "prefix":
            lines.append(f"  Méthode : préfixe « {m['prefix']} » détaché, reste recherché.")
        else:
            lines.append(f"  Méthode : forme {'complète' if m['method']=='word' else 'consonantique'}.")
        ref = m.get("reference_example")
        if ref and ref[0]:
            book, ch, vs = ref
            lines.append(f"  Forme en base : {m['text'].strip()}  (lemme : {m['lex']})")
            gfr = m.get("gloss_fr") or ""
            gen = m.get("gloss") or ""
            if gfr:
                lines.append(f"  Traduction (fr) : {gfr}")
                if gen and gen != gfr:
                    lines.append(f"  Traduction (en) : {gen}")
            elif gen:
                lines.append(f"  Traduction (gloss) : {gen}")
            lines.append(f"  Exemple : {book} {ch}:{vs}")
        else:
            lines.append(f"  Forme en base : {m['text'].strip()}  (lemme : {m['lex']})")
            gfr = m.get("gloss_fr") or ""
            gen = m.get("gloss") or ""
            if gfr:
                lines.append(f"  Traduction (fr) : {gfr}")
                if gen and gen != gfr:
                    lines.append(f"  Traduction (en) : {gen}")
            elif gen:
                lines.append(f"  Traduction (gloss) : {gen}")
        # Features clés
        f_ = m["features"]
        bits = []
        for k, label in [
            ("sp", "POS"), ("gn", "genre"), ("nu", "nombre"), ("ps", "personne"),
            ("st", "état"), ("vt", "temps"), ("vs", "binyan"), ("prs", "suffixe"),
        ]:
            v = f_.get(k)
            if v and v not in ("NA", "unknown", "absent", "none", ""):
                bits.append(f"{label}={v}")
        if bits:
            lines.append(f"  Morphologie : {', '.join(bits)}")
        lines.append("  Règles :")
        for r in m["rules"]:
            lines.append(f"    ↳ {r}")
        lines.append("")
    return "\n".join(lines)


def word_to_json(word_analysis, indent=2, ensure_ascii=False):
    return json.dumps(word_analysis, indent=indent, ensure_ascii=ensure_ascii)


def phrase_to_text(phrase_analysis):
    """Formate le résultat de ``analyze_phrase`` en texte lisible."""
    lines = []
    lines.append(f"=== Phrase analysée : {phrase_analysis['input']} ===")
    lines.append("")
    lines.append("-- Règles contextuelles --")
    if not phrase_analysis["context_rules"]:
        lines.append("  (aucune règle contextuelle détectée)")
    for r in phrase_analysis["context_rules"]:
        lines.append(f"  • {r}")
    lines.append("")
    lines.append("-- Analyse token par token --")
    for i, tok in enumerate(phrase_analysis["tokens"], 1):
        lines.append(f"")
        lines.append(f"  [{i}] {tok['text']}")
        for r in tok["rules"]:
            lines.append(f"      ↳ {r}")
        # Détail des lectures possibles si ambigu et trouvé
        wa = tok["word_analysis"]
        if wa["found"] and len(wa["matches"]) > 1:
            lines.append(f"      Lectures possibles :")
            for m in wa["matches"][:3]:
                lex = m.get("lex") or ""
                gfr = m.get("gloss_fr") or ""
                gen = m.get("gloss") or ""
                gloss_str = f" « {gfr} »" if gfr else (f" « {gen} »" if gen else "")
                lines.append(
                    f"        - {m['text'].strip()} (lemme {lex}, {m['count']} occ.){gloss_str} : "
                    f"{m['rules'][0] if m['rules'] else ''}"
                )
    return "\n".join(lines)


def phrase_to_json(phrase_analysis, indent=2, ensure_ascii=False):
    return json.dumps(phrase_analysis, indent=indent, ensure_ascii=ensure_ascii)
