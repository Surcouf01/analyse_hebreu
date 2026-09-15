"""Diagnostics heuristiques pour reconnaître le binyan d'une forme verbale.

Pour un mot conjugué, renvoie la liste des règles morphologiques qui
permettent d'identifier son binyan (vs) plutôt qu'un autre. Les heuristiques
s'appuient sur les features BHSA :

  - vbs (verbal stem marker) : la signature consonantique du binyan
    (H = hifil/hofal, HT = hitpael, N = nifal, absent = qal/piel/pual,
    C = shafel, >T = ethpaal araméen, etc.).
  - le schéma vocalique : disambiguïse les binyanim partageant le même vbs
    (hifil vs hofal : hireq/segol après le ה vs shureq/qamats ; piel vs pual
    vs qal : hireq vs shureq vs qamats).
  - la présence du préfixe ת (hitpael, nithpaal), du préfixe נ (nifal, nit),
    du préfixe מ (participe), etc.

Ces heuristiques sont pédagogiques : elles expliquent le raisonnement, elles
ne re-décident pas le binyan (la base BHSA l'a déjà codé dans `vs`).
"""

# Marqueur de stem (vbs) -> binyan. Quand vbs est unique, il est suffisant.
_VBS_SIGNATURE = {
    "absent": ("qal/piel/pual", "vbs=absent (pas de marqueur de stem consonantique) ; les binyanim sans préformative (qal, piel, pual) n'ont pas de marqueur consonantique — il faut le schéma vocalique pour les distinguer."),
    "H": ("hifil/hofal", "vbs=H : préformative ה (hē) — commun à l'hifil (actif causatif) et au hofal (passif causatif) ; le schéma vocalique les sépare."),
    "HT": ("hitpael", "vbs=HT : préformative הִתְ (hit) — signature du hitpael (réfléchi)."),
    "HCT": ("hsht/hithpalpel", "vbs=HCT : préformative הִשְׁתְּ (hšt) — hithpalpel, forme réfléchie sur racine redoublée."),
    "NT": ("nit/nithpaal", "vbs=NT : préformative נִתְ (nit) — nithpaal, rare, réfléchi-passif."),
    "N": ("nifal", "vbs=N : préformative נ (nūn) — signature du nifal (réfléchi-passif)."),
    "C": ("shafel", "vbs=C : préformative שׁ (šin) — shafel, rare, causatif (emprunt araméen)."),
    ">": ("afel/haf/hifil(aram.)", "vbs=> : préformative א (alef) — afel araméen (causatif)."),
    ">T": ("ethpaal/ethpeal", "vbs=>T : préformative אֶתְ (et) — ethpaal/ethpeal araméen (réfléchi-passif)."),
    "T": ("tif/ithpaal", "vbs=T : préformative תְ (taw) — ithpaal araméen (réfléchi)."),
}

# Voyelles (points de nikkud) pertinentes pour le disambiguïsation.
_HIREQ = "\u05b4"        # ִ
_SEGOL = "\u05b6"        # ֶ
_HATAF_SEGOL = "\u05b2"  # ֲ
_SHUREQ_VAV = "\u05d5"   # ו (vav shureq, après consonne = /u/)
_QUBUTS = "\u05bb"       # ֻ
_QAMATS = "\u05b8"       # ָ
_HOLAM = "\u05b9"        # ֹ
_PATAH = "\u05b7"        # ַ


def _first_vowel(s, start=1):
    """Renvoie le premier signe de voyelle (nikkud) dans s à partir de `start`,
    en ignorant daguesh (U+05BC), shin/sin-dot (U+05C1/C2) et meteg."""
    if not s:
        return None
    skip = {0x05BC, 0x05C1, 0x05C2, 0x05AD}  # daguesh, shin/sin-dot, meteg
    for c in s[start:]:
        o = ord(c)
        if 0x05B0 <= o <= 0x05BB or o == 0x05C7:  # voyelles
            return c
        if o not in skip and not (0x05D0 <= o <= 0x05F4):
            continue
        if o in skip:
            continue
        # consonne : on s'arrête (la voyelle cherchée est juste après)
        return None
    return None


def _vowel_after_ha(form):
    """Voyelle qui suit la préformative ה (hifil/hofal perf sans pfm).

    Distingue : vav shureq (הוּ, hofal) des voyelles hireq/segol (hifil).
    Renvoie le vav U+05D5 comme marqueur shureq, sinon le premier nikkud."""
    if not form or form[0] != "\u05d4" or len(form) < 2:
        return None
    if form[1] == "\u05d5":  # vav shureq → hofal
        return "\u05d5"
    return _first_vowel(form, start=1)


def _first_root_vowel(form):
    """Voyelle après la 1re consonne radicale (piel/pual/qal perf sans pfm)."""
    if not form or len(form) < 2:
        return None
    return _first_vowel(form, start=1)


def binyan_diagnostics(F, w):
    """Renvoie une liste de règles heuristiques expliquant le binyan du mot w.

    F = API Text-Fabric features, w = nœud word.
    """
    sp = _g(F, "sp", w)
    if sp != "verb":
        return []

    vs = _g(F, "vs", w) or ""
    vt = _g(F, "vt", w) or ""
    pfm = _g(F, "pfm", w) or ""
    vbs = _g(F, "vbs", w) or ""
    vbe = _g(F, "vbe", w) or ""
    form = _g(F, "g_word_utf8", w) or ""
    cons = _g(F, "g_cons_utf8", w) or ""

    rules = []

    def add(r):
        rules.append(r)

    # --- 1. Signature du marqueur de stem (vbs) ------------------------------ #
    sig = _VBS_SIGNATURE.get(vbs)
    if sig:
        add(f"[binyan] Marqueur de stem (vbs={vbs!r}) : {sig[1]}")
    else:
        add(f"[binyan] Marqueur de stem (vbs={vbs!r}) : marqueur non standard.")

    # --- 2. Préformative consonantique visible ------------------------------- #
    # hitpael / hithpalpel : préfixe ת après ה
    if cons.startswith("\u05d4\u05ea") or "HT" in (vbs or ""):
        add("[binyan] Préformative הִתְ (hit) visible : le ת infixé après ה est "
            "la signature du hitpael (réfléchi).")
    # nifal : préfixe נ
    if vbs == "N" or (form and form.startswith("\u05e0") and vbs == "N"):
        add("[binyan] Préformative נ (nūn) visible : signature du nifal "
            "(réfléchi-passif ; le nūn s'assimile parfois dans les formes à préfixe).")
    # hifil/hofal : préformative ה
    if vbs == "H":
        add("[binyan] Préformative ה (hē) causative : commune à hifil et hofal ; "
            "le schéma vocalique décide.")

    # --- 3. Disambiguïsation hifil vs hofal (vbs=H) -------------------------- #
    if vbs == "H" and vt == "perf" and pfm in ("absent", "", None):
        v = _vowel_after_ha(form)
        if v in (_HIREQ, _SEGOL, _HATAF_SEGOL):
            add(f"[binyan] Voyelle {v!r} (hireq/segol) après le ה : schéma actif → "
                "hifil (causatif actif), et non hofal.")
        elif v in (_SHUREQ_VAV, _QUBUTS, _QAMATS):
            add(f"[binyan] Voyelle {v!r} (shureq/qamats) après le ה : schéma passif → "
                "hofal (causatif passif), et non hifil.")

    # --- 4. Disambiguïsation qal vs piel vs pual (vbs=absent) ----------------- #
    if vbs == "absent" and vt == "perf" and pfm in ("absent", "", None):
        v = _first_root_vowel(form)
        if vs == "qal":
            add(f"[binyan] Voyelle {v!r} (qamats/patah) sous la 1re radicale : "
                "schéma qal (actif neutre), sans l'hireq du piel ni le shureq du pual.")
        elif vs == "piel":
            add(f"[binyan] Voyelle {v!r} (hireq) sous la 1re radicale + daguesh "
                "fort sur la 2e radicale : schéma piel (intensif actif), "
                "distinct du qal (qamats) et du pual (shureq).")
        elif vs == "pual":
            add(f"[binyan] Voyelle {v!r} (shureq/qubuts) sous la 1re radicale : "
                "schéma pual (passif intensif du piel), distinct du piel (hireq) "
                "et du qal (qamats).")

    # --- 5. Hitpael et dérivés : redoublement / racine ----------------------- #
    if vs == "hit":
        add("[binyan] Hitpael : ת infixé entre préformative ה et racine, "
            "souvent avec redoublement de la 2e radicale (daguesh fort) → "
            "sens réfléchi.")
    if vs in ("hsht",):
        add("[binyan] Hithpalpel (hsht) : comme hitpael mais sur racine "
            "redoublée (2e/3e radicale identiques) — la préformative השת "
            "remplace הת.")
    if vs in ("htpa", "htpe", "htpo", "hotp"):
        add(f"[binyan] {vs.upper()} : variante hitpael-like (réfléchi) sur "
            f"schéma vocalique atypique — binyan rare/dérivé.")

    # --- 6. Passifs ---------------------------------------------------------- #
    if vs == "pual":
        add("[binyan] Pual : passif intensif du piel (shureq sous la 1re radicale, "
            "daguesh fort), voix passive.")
    if vs == "hof":
        add("[binyan] Hofal : passif causatif du hifil (shureq/qamats après ה), "
            "voix passive.")
    if vs == "nif":
        add("[binyan] Nifal : voix réfléchie-passive (préformative נ), "
            "à mi-chemin entre actif et passif.")

    # --- 7. Binyanim araméens ------------------------------------------------ #
    if vs in ("peal", "pael", "peil", "afel", "haf", "etpa", "etpe", "tif", "pasq"):
        add(f"[binyan] {vs} : binyan araméen (langue='Aramaic') — équivalent "
            f"morphologique d'un binyan hébreu (ex. peal≈qal, pael≈piel, "
            f"afel/haf≈hifil, etpa/etpe≈hitpael).")
    if vs == "poel" or vs == "poal":
        add(f"[binyan] {vs} : binyan rare, variante intensive (poel actif / "
            f"poal passif) proche du piel/pual mais à schéma vocalique distinct.")

    # --- 8. Règle d'exclusion synthétique ------------------------------------ #
    if not rules:
        add(f"[binyan] Binyan codé {vs!r} dans la base BHSA ; aucune heuristique "
            f"morphologique simple ne le distingue (forme atypique ou rare).")

    return rules


def _g(F, name, w):
    feat = getattr(F, name, None)
    return feat.v(w) if feat is not None else None
