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
                        lines.append(f"            ‣ {word['text'].strip()}{lex}")
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
