"""Onglet README : rendu enrichi du markdown et navigation.

Extrait de gui_hebreu.py (refactorisation en paquet gui/) : le mixin
ReadmeTabMixin regroupe la construction de l'onglet README — lecture
du README.md, conversion markdown -> HTML -> texte taggé, sommaire
cliquable (liens hypertextes vers les titres), barre de recherche
Ctrl-F (cf. FindMixin/ReadmeText) et historique de navigation
arrière/avant (boutons Précédent/Suivant, Alt+Gauche/Droite).
"""

import os
import re
import sys
import tkinter as tk
import webbrowser
from tkinter import ttk

from gui.config import _github_slug, _resource_dir, _app_dir
from gui.widgets import ReadmeText


class ReadmeTabMixin:
    def _build_readme_tab(self, parent=None):
        """Onglet README : rendu enrichi du fichier README.md.

        Le markdown est converti en HTML par le module ``markdown``
        (structure de référence), puis le HTML est restitué dans un
        tk.Text avec tags : titres, gras, italique, blocs de code,
        listes à puces. Ce rendu maison (pas de moteur HTML externe,
        notamment pas tkinterweb qui provoque un segmentation fault
        sous Windows) ne peut pas planter la fenêtre. Sans module
        markdown, repli sur le markdown brut.
        """
        tab = self.tab_readme
        # Lecture du README : à côté du script, puis ressources
        # embarquées (PyInstaller), puis dossier de l'exécutable.
        readme = None
        for base in (os.path.dirname(os.path.abspath(__file__)),
                     _resource_dir(), _app_dir()):
            for name in ("README.md", "readme.md"):
                p = os.path.join(base, name)
                if os.path.isfile(p):
                    readme = p
                    break
            if readme:
                break
        if readme is None:
            ttk.Label(tab, text="README.md introuvable.").pack(padx=8,
                                                              pady=8)
            return
        with open(readme, encoding="utf-8") as fh:
            md_text = fh.read()

        # Barre d'outils : navigation dans l'historique des liens
        # du sommaire (arrière/avant, cf. _readme_nav_*). Les widgets
        # boutons portent un nom distinct des méthodes de navigation
        # (_readme_nav_back/_readme_nav_forward).
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=4, pady=(4, 0))
        self._readme_nav_back_btn = ttk.Button(
            toolbar, text="\u2190 Précédent", width=12,
            state="disabled", command=self._readme_nav_back)
        self._readme_nav_back_btn.pack(side="left", padx=(0, 4))
        self._readme_nav_fwd_btn = ttk.Button(
            toolbar, text="Suivant \u2192", width=12,
            state="disabled", command=self._readme_nav_forward)
        self._readme_nav_fwd_btn.pack(side="left")
        # Historique de navigation : pile des positions visitées par
        # clic sur un lien interne (index de début du titre ciblé) et
        # position courante dans cette pile.
        self._readme_nav_history = []
        self._readme_nav_pos = -1
        # Raccourcis clavier Alt+Gauche / Alt+Droite : actifs quel que
        # soit le focus (bind_all), le handler vérifie que l'onglet
        # README est affiché et ignore sinon.
        self.root.bind_all("<Alt-Left>", self._on_readme_nav_key)
        self.root.bind_all("<Alt-Right>", self._on_readme_nav_key)

        # Zone de texte défilable avec rendu enrichi, avec recherche
        # Ctrl-F (cf. FindMixin).
        wrap = tk.Frame(tab)
        wrap.pack(fill="both", expand=True, padx=4, pady=4)
        text = ReadmeText(wrap, wrap="word", padx=12, pady=8,
                       font=("Segoe UI", 10) if sys.platform == "win32"
                       else ("TkDefaultFont", 10),
                       bg="white", relief="flat")
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=text.yview)
        yscroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.configure(yscrollcommand=yscroll.set)

        # Tags du rendu. cget("font") renvoie une CHAÎNE : résoudre
        # la police via tkinter.font pour obtenir famille et taille
        # numériques.
        from tkinter import font as tkfont
        base = tkfont.Font(font=text.cget("font"))
        fam = base.actual("family")
        size = base.actual("size")
        mono = tkfont.Font(family="Consolas", size=10) \
            if sys.platform == "win32" else tkfont.nametofont("TkFixedFont")
        mono_small = mono.copy()
        mono_small.configure(size=mono.actual("size") - 1)
        # Hiérarchie h1..h6 : chaque niveau se distingue par la taille,
        # la couleur et l'espacement — h1 titre principal, h2 section
        # (souligné par un filet), h3 sous-section, h4-h6 niveaux fins.
        text.tag_configure("h1", font=(fam, size + 9, "bold"),
                           foreground="#1a1a2e", spacing3=12, spacing1=14)
        text.tag_configure("h2", font=(fam, size + 5, "bold"),
                           foreground="#16213e", spacing3=8, spacing1=16,
                           underline=True)
        text.tag_configure("h3", font=(fam, size + 2, "bold"),
                           foreground="#0f3460", spacing1=10, spacing3=4)
        text.tag_configure("h4", font=(fam, size, "bold italic"),
                           foreground="#0f3460", spacing1=8)
        text.tag_configure("h5", font=(fam, size - 1, "bold"),
                           foreground="#51557e", spacing1=6)
        text.tag_configure("h6", font=(fam, size - 1, "italic"),
                           foreground="#51557e", spacing1=6)
        text.tag_configure("bold", font=(fam, size, "bold"))
        text.tag_configure("italic", font=(fam, size, "italic"))
        text.tag_configure("code", font=mono, background="#f0f0f0")
        text.tag_configure("pre", font=mono_small, background="#f5f5f5",
                           lmargin1=12, lmargin2=12,
                           spacing1=4, spacing3=4)
        text.tag_configure("li", lmargin1=16, lmargin2=24)
        text.tag_configure("hr", justify="center", foreground="gray60")
        # Liens hypertextes (sommaire, liens du markdown) : bleu,
        # soulignés, curseur main, clic -> défilement vers l'ancre.
        text.tag_configure("link", foreground="#0000EE", underline=True)
        text.tag_bind("link", "<Enter>",
                      lambda e: text.configure(cursor="hand2"))
        text.tag_bind("link", "<Leave>",
                      lambda e: text.configure(cursor=""))
        text.tag_bind("link", "<Button-1>", self._on_readme_link)
        text.tag_lower("sel", "link")

        # Les commentaires HTML (marqueurs <!-- TOC --> du sommaire
        # généré) ne doivent pas apparaître dans le rendu.
        md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)

        try:
            import markdown
            html = markdown.markdown(
                md_text, extensions=["tables", "fenced_code",
                                     "sane_lists"])
            self._render_html_to_text(text, html)
        except ImportError:
            text.insert("1.0", md_text)

        text.configure(state="disabled")
        self._readme_text = text

    def _render_html_to_text(self, text_widget, html):
        """Restitue un sous-ensemble HTML dans un tk.Text avec tags.

        Pris en charge : h1-h6, p, br, hr, ul/ol/li (imbrication
        approximée par l'indentation), strong/b, em/i, code, pre,
        blockquote, a (liens hypertextes). Le texte brut du HTML est
        inséré, les tags s'appliquent par plages.
        """
        import html as _html
        import re

        # Découpage du HTML en événements (ouvrant/fermant/texte).
        tag_re = re.compile(r"<(/?)(\w+)([^>]*)>")
        pos = 0
        events = []  # (type, nom, attrs) / ("text", contenu)
        for m in tag_re.finditer(html):
            if m.start() > pos:
                events.append(("text", html[pos:m.start()], ""))
            events.append(("close" if m.group(1) else "open",
                           m.group(2).lower(), m.group(3) or ""))
            pos = m.end()
        if pos < len(html):
            events.append(("text", html[pos:], ""))

        headings = {"h1", "h2", "h3", "h4", "h5", "h6"}
        # --- Traitement séquentiel des événements ---
        text_widget.delete("1.0", "end")
        markup = []  # pile de tags actifs ("bold", "italic", "code")
        list_stack = []
        counters = []
        # Titre en cours de construction : texte accumulé + index de
        # départ, pour calculer l'ancre (slug GitHub) à la fermeture
        # et enregistrer la position cible des liens du sommaire.
        heading_text = []
        heading_start = None
        heading_seq = 0
        anchors = {}  # slug -> nom de marque Tk du début du titre
        # Liens <a href> : plage de texte -> cible (ancre locale ou URL).
        link_spans = []  # (début, fin, href) ; fin fixée à la fermeture
        def current_tags():
            return [t for t in markup if isinstance(t, str)]

        def in_heading():
            return (markup and isinstance(markup[-1], str)
                    and markup[-1].startswith("h"))

        for kind, a, b in events:
            if kind == "text":
                content = _html.unescape(a)
                if not content:
                    continue
                # Sauter les contenus vides (inter-tags).
                if not content.strip() and not content.startswith("\n"):
                    continue
                if in_heading():
                    heading_text.append(content)
                tags = current_tags() + (["li"] if list_stack else [])
                # Dans un lien : appliquer le tag « link ».
                if any(isinstance(t, tuple) and t[0] == "a"
                       for t in markup):
                    tags = tags + ["link"]
                text_widget.insert("end", content, tuple(tags) or ())
            elif kind == "open":
                if a in headings:
                    text_widget.insert("end", "\n")
                    # Position de départ du titre : une marque Tk (elle
                    # suit les insertions/suppressions ultérieures, en
                    # particulier le nettoyage des lignes vides en fin
                    # de rendu qui décale les indices figés).
                    heading_start = f"readme_h_{heading_seq}"
                    text_widget.mark_set(heading_start, "end")
                    text_widget.mark_gravity(heading_start, "left")
                    heading_seq += 1
                    heading_text = []
                    markup.append("h" + a[1])
                    # Les titres ferment implicitement les paragraphes.
                elif a == "a":
                    m = re.search(r"href\s*=\s*[\"']([^\"']*)[\"']", b)
                    markup.append(("a", m.group(1) if m else ""))
                    link_spans.append([text_widget.index("end - 1c"),
                                       None,
                                       m.group(1) if m else ""])
                elif a in ("strong", "b"):
                    markup.append("bold")
                elif a in ("em", "i"):
                    markup.append("italic")
                elif a == "code":
                    markup.append("code")
                elif a == "pre":
                    text_widget.insert("end", "\n")
                    markup.append("pre")
                elif a in ("ul", "ol"):
                    list_stack.append(a)
                    counters.append(0)
                    text_widget.insert("end", "\n")
                elif a == "li":
                    # Nouvelle ligne seulement si le dernier caractère
                    # inséré n'est pas déjà un retour à la ligne.
                    end = text_widget.index("end - 1c")
                    last = text_widget.get(f"{end}", "end")
                    sep = "" if last == "\n" else "\n"
                    if list_stack and list_stack[-1] == "ol":
                        counters[-1] += 1
                        text_widget.insert("end", sep + "  " * (len(list_stack) - 1)
                                          + f"{counters[-1]}. ", ("li",))
                    else:
                        text_widget.insert("end", sep + "  " * max(0, len(list_stack) - 1)
                                          + "\u2022 ", ("li",))
                elif a == "br":
                    text_widget.insert("end", "\n")
                elif a == "hr":
                    text_widget.insert("end", "\n\u2500" * 30 + "\n", ("hr",))
                elif a == "blockquote":
                    markup.append("li")
                    text_widget.insert("end", "\n")
            elif kind == "close":
                if a in headings:
                    if markup and isinstance(markup[-1], str) \
                            and markup[-1].startswith("h"):
                        markup.pop()
                    # Ancre GitHub du titre (cf. scripts/generate_toc.py)
                    # : le sommaire inséré dans le README pointe vers elle.
                    slug = _github_slug("".join(heading_text))
                    if slug and heading_start is not None:
                        anchors.setdefault(slug, heading_start)
                    text_widget.insert("end", "\n\n", ())
                elif a == "a":
                    for i in range(len(markup) - 1, -1, -1):
                        if isinstance(markup[i], tuple) and markup[i][0] == "a":
                            del markup[i]
                            break
                    for span in reversed(link_spans):
                        if span[1] is None:
                            span[1] = text_widget.index("end - 1c")
                            break
                elif a in ("strong", "b", "em", "i", "code", "li",
                           "blockquote"):
                    if markup and markup[-1] in ("bold", "italic",
                                                 "code", "li"):
                        markup.pop()
                elif a == "pre":
                    if markup and markup[-1] == "pre":
                        markup.pop()
                    text_widget.insert("end", "\n\n", ())
                elif a in ("ul", "ol"):
                    if list_stack:
                        list_stack.pop()
                    if counters:
                        counters.pop()
                    text_widget.insert("end", "\n")
        # Enregistrer les cibles des liens internes : le handler de
        # clic (cf. _on_readme_link) défile vers le titre dont le slug
        # GitHub correspond à l'ancre ; les liens externes ouvrent le
        # navigateur.
        text_widget._readme_anchors = anchors
        text_widget._readme_links = {}
        for start, end, href in link_spans:
            if not href:
                continue
            if href.startswith("#"):
                text_widget.tag_add(f"link:{href[1:]}", start, end)
            elif href.startswith(("http://", "https://")):
                # Seuls les vrais liens web sont cliquables : un chemin
                # relatif (ex. .github/workflows/…) n'a pas de cible
                # ouvrable depuis le widget.
                tag = f"linkext:{len(text_widget._readme_links)}"
                text_widget.tag_configure(
                    tag, foreground="#0000EE", underline=True)
                text_widget.tag_add(tag, start, end)
                text_widget._readme_links[tag] = href
        # Nettoyage : lignes vides multiples -> une seule. La
        # suppression doit être CIBLÉE (search/delete sur la plage
        # excédentaire) : relire tout le texte avec get() puis le
        # réinsérer perdrait tous les tags de formatage.
        while True:
            idx = text_widget.search("\n\n\n", "1.0", "end")
            if not idx:
                break
            # Supprimer UN newline de la séquence (boucle jusqu'à
            # normalisation complète).
            text_widget.delete(f"{idx} lineend", f"{idx} lineend +1c")

    def _on_readme_link(self, event=None):
        """Clic sur un lien du sommaire : défile vers le titre ciblé.

        Les liens internes (#ancre) utilisent le slug GitHub calculé
        à l'insertion des titres (cf. _render_html_to_text) ; les
        liens externes (http…) s'ouvrent dans le navigateur. Chaque
        saut interne est inscrit dans l'historique de navigation
        (cf. _readme_nav_*).
        """
        w = self._readme_text
        if w is None:
            return
        try:
            idx = w.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        anchors = getattr(w, "_readme_anchors", {})
        links = getattr(w, "_readme_links", {})
        for tag in w.tag_names(idx):
            if tag.startswith("link:") and tag != "link":
                target = tag[len("link:"):]
                if target in anchors:
                    self._readme_nav_jump(anchors[target])
                    return
            elif tag in links:
                webbrowser.open(links[tag])
                return

    # --- Historique de navigation des liens du README -------------------
    def _readme_nav_jump(self, target):
        """Défile vers la cible et inscrit le saut dans l'historique.

        La position de départ (haut du document, là où se trouve le
        sommaire) est enregistrée comme premier élément : le retour
        arrière y ramène après un premier saut, comme dans un
        navigateur.
        """
        w = self._readme_text
        if w is None:
            return
        w.see(target)
        # Position de départ mémorisée au premier saut.
        if not self._readme_nav_history:
            self._readme_nav_history.append("1.0")
            self._readme_nav_pos = 0
        # Coupe l'éventuel futur (retour en arrière puis nouveau saut,
        # comme dans un navigateur) et empile la nouvelle position.
        self._readme_nav_history = self._readme_nav_history[
            :self._readme_nav_pos + 1]
        self._readme_nav_history.append(target)
        self._readme_nav_pos = len(self._readme_nav_history) - 1
        self._readme_nav_update_buttons()

    def _readme_nav_back(self):
        """Retourne à la position précédente de l'historique."""
        if self._readme_nav_pos > 0:
            self._readme_nav_pos -= 1
            target = self._readme_nav_history[self._readme_nav_pos]
            if self._readme_text is not None:
                self._readme_text.see(target)
            self._readme_nav_update_buttons()

    def _readme_nav_forward(self):
        """Avance à la position suivante de l'historique."""
        if self._readme_nav_pos < len(self._readme_nav_history) - 1:
            self._readme_nav_pos += 1
            target = self._readme_nav_history[self._readme_nav_pos]
            if self._readme_text is not None:
                self._readme_text.see(target)
            self._readme_nav_update_buttons()

    def _readme_nav_update_buttons(self):
        """Active/désactive les boutons selon la position courante."""
        can_back = self._readme_nav_pos > 0
        can_fwd = (self._readme_nav_pos
                   < len(self._readme_nav_history) - 1)
        for btn, on in ((self._readme_nav_back_btn, can_back),
                        (self._readme_nav_fwd_btn, can_fwd)):
            if btn is not None:
                try:
                    btn.configure(state="normal" if on else "disabled")
                except tk.TclError:
                    pass

    def _on_readme_nav_key(self, event=None):
        """Alt+Gauche / Alt+Droite : navigation arrière/avant —
        uniquement quand l'onglet README est actif."""
        try:
            idx = self.notebook.select()
            if not idx or self.notebook.tab(idx, "text") != "README":
                return None
        except tk.TclError:
            return None
        if event.keysym == "Left":
            self._readme_nav_back()
        elif event.keysym == "Right":
            self._readme_nav_forward()
        return "break"
