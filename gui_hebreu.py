#!/usr/bin/env python3
"""Interface graphique de l'analyseur grammatical de l'hébreu biblique.

Fenêtre Tkinter à onglets qui reprend chacune des fonctions du programme en
ligne de commande (``analyse_hebreu.py``) :

  - Onglet « Verset »  : analyse d'un verset par sélection successive du
    livre (dans l'ordre canonique de la Bible hébraïque, Torah en premier),
    du chapitre puis du verset, au moyen de listes déroulantes bornées aux
    limites réelles de la base BHSA.
  - Onglet « Mot »     : analyse d'un mot hébreu isolé, saisie via un clavier
    hébreu virtuel (points-voyelles inclus) en UTF-8.
  - Onglet « Phrase »  : analyse d'une phrase hébreu libre, saisie via le
    même clavier hébreu virtuel.

Lancement :

    python gui_hebreu.py

La base BHSA est chargée en arrière-plan au démarrage (cf. ``bhsa_grammar``).
"""

import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from bhsa_grammar import (
    load_corpus,
    analyze_verse_by_reference,
    analyze_word,
    analyze_phrase,
    format_text,
    format_json,
    format_summary,
    format_word,
    format_word_json,
    format_phrase,
    format_phrase_json,
    book_french,
    DataNotFoundError,
)


# Police affichant l'hébreu (points-voyelles + daguesh) sur la plupart des
# systèmes. Tkinter retombe sur une police équivalente si elle est absente.
HEBREW_FONT = ("DejaVu Sans", 14)
HEBREW_FONT_MONO = ("DejaVu Sans Mono", 12)


# --- Clavier hébreu virtuel ------------------------------------------------
# Points-voyelles (nikkud) et daguesh — marques combinantes UTF-8.
_NIKKUD = {
    "qamats": "\u05B8",      # ָ
    "patach": "\u05B7",      # ַ
    "segol": "\u05B6",       # ֶ
    "tsere": "\u05B5",       # ֵ
    "hireq": "\u05B4",       # ִ
    "holem": "\u05B9",       # ֹ
    "qubuts": "\u05BB",     # ֻ
    "sheva": "\u05B0",       # ְ
    "dagesh": "\u05BC",     # ּ
    "qamats_qatan": "\u05C7",  # ַ (qamats qatan / qamats hatuf)
}

NIKKUD_LABELS = {
    "qamats": "\u05B8 qamats",
    "patach": "\u05B7 patach",
    "segol": "\u05B6 segol",
    "tsere": "\u05B5 tsere",
    "hireq": "\u05B4 hireq",
    "holem": "\u05B9 holem",
    "qubuts": "\u05BB qubuts",
    "sheva": "\u05B0 sheva",
    "dagesh": "\u05BC dagesh",
    "qamats_qatan": "\u05C7 q.qatan",
}


class HebrewKeyboard(ttk.Frame):
    """Clavier hébreu virtuel qui insère des caractères UTF-8 dans le widget
    texte ciblé (Entry ou Text)."""

    def __init__(self, master, target_getter):
        super().__init__(master)
        # target_getter() renvoie le widget Entry/Text actuellement ciblé.
        self._get_target = target_getter

        consonants = [
            "\u05D0", "\u05D1", "\u05D2", "\u05D3", "\u05D4", "\u05D5",
            "\u05D6", "\u05D7", "\u05D8", "\u05D9", "\u05DB", "\u05DA",
            "\u05DC", "\u05DE", "\u05DD", "\u05E0", "\u05DF", "\u05E1",
            "\u05E2", "\u05E4", "\u05E3", "\u05E6", "\u05E5", "\u05E7",
            "\u05E8", "\u05E9", "\u05EA",
        ]
        # Row of consonants
        cons_frame = ttk.Frame(self)
        cons_frame.pack(fill="x", pady=(0, 4))
        for ch in consonants:
            self._make_key(cons_frame, ch, ch)

        # Row of vowel points (nikkud) + dagesh
        nik_frame = ttk.Frame(self)
        nik_frame.pack(fill="x")
        for key, label in NIKKUD_LABELS.items():
            self._make_key(nik_frame, _NIKKUD[key], label)

        # Control row
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", pady=(4, 0))
        self._make_key(ctrl, " ", "Espace", width=14)
        self._make_key(ctrl, "\u05C3", "sof pasuq \u05C3", width=10)
        self._make_key(ctrl, None, "\u232B Retour", width=12, action="backspace")

    def _make_key(self, parent, char, label, width=4, action=None):
        btn = ttk.Button(parent, text=label, width=width,
                         command=lambda c=char, a=action: self._press(c, a))
        btn.pack(side="left", padx=1, pady=1)
        return btn

    def _press(self, char, action):
        target = self._get_target()
        if target is None:
            return
        try:
            if action == "backspace":
                if isinstance(target, tk.Text):
                    target.delete("insert-1c", "insert")
                else:
                    pos = target.index(tk.INSERT)
                    if pos > 0:
                        target.delete(pos - 1)
            else:
                target.insert(tk.INSERT, char)
                if isinstance(target, tk.Text):
                    target.see(tk.INSERT)
            target.focus_set()
        except tk.TclError:
            pass


class AnalyseurGUI:
    """Fenêtre principale de l'analyseur grammatical."""

    def __init__(self, root):
        self.root = root
        self.api = None
        self._work_queue = queue.Queue()
        self._target_widget = None  # widget actuellement ciblé par le clavier

        root.title("Analyseur grammatical de l'hébreu biblique")
        root.geometry("980x720")
        root.minsize(820, 600)

        self._build_widgets()
        self._start_loading()

        # Polling des résultats des travaux en arrière-plan.
        root.after(120, self._poll_queue)

    # --- Construction de l'interface -------------------------------------
    def _build_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_verse = ttk.Frame(self.notebook)
        self.tab_word = ttk.Frame(self.notebook)
        self.tab_phrase = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_verse, text="Verset")
        self.notebook.add(self.tab_word, text="Mot")
        self.notebook.add(self.tab_phrase, text="Phrase")

        self._build_verse_tab()
        self._build_word_tab()
        self._build_phrase_tab()

        # Barre d'état (chargement de la base / analyse en cours).
        self.status = ttk.Label(self.root, text="Chargement de la base BHSA…",
                                relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom")

    def _build_verse_tab(self):
        tab = self.tab_verse

        form = ttk.LabelFrame(tab, text="Référence du verset")
        form.pack(fill="x", padx=8, pady=8)

        # Livre (ordre canonique : Torah en premier), Chapitre, Verset.
        ttk.Label(form, text="Livre :").grid(row=0, column=0, sticky="w", padx=4, pady=6)
        self.book_var = tk.StringVar()
        self.book_combo = ttk.Combobox(form, textvariable=self.book_var,
                                       state="readonly", width=30)
        self.book_combo.grid(row=0, column=1, sticky="w", padx=4, pady=6)
        self.book_combo.bind("<<ComboboxSelected>>", self._on_book_change)

        ttk.Label(form, text="Chapitre :").grid(row=0, column=2, sticky="w", padx=(16, 4), pady=6)
        self.chapter_var = tk.StringVar()
        self.chapter_combo = ttk.Combobox(form, textvariable=self.chapter_var,
                                          state="readonly", width=8)
        self.chapter_combo.grid(row=0, column=3, sticky="w", padx=4, pady=6)
        self.chapter_combo.bind("<<ComboboxSelected>>", self._on_chapter_change)

        ttk.Label(form, text="Verset :").grid(row=0, column=4, sticky="w", padx=(16, 4), pady=6)
        self.verse_var = tk.StringVar()
        self.verse_combo = ttk.Combobox(form, textvariable=self.verse_var,
                                        state="readonly", width=8)
        self.verse_combo.grid(row=0, column=5, sticky="w", padx=4, pady=6)

        # Options de format
        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.verse_format = tk.StringVar(value="text")
        ttk.Radiobutton(opts, text="Texte", variable=self.verse_format,
                        value="text").pack(side="left")
        ttk.Radiobutton(opts, text="Synthèse", variable=self.verse_format,
                        value="summary").pack(side="left")
        ttk.Radiobutton(opts, text="JSON", variable=self.verse_format,
                        value="json").pack(side="left")
        self.verse_no_words = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Masquer le détail mot à mot",
                        variable=self.verse_no_words).pack(side="left", padx=(16, 0))

        self.btn_verse = ttk.Button(tab, text="Analyser le verset",
                                   command=self._run_verse)
        self.btn_verse.pack(anchor="w", padx=8, pady=8)
        self.btn_verse.state(["disabled"])

        self._build_output(tab)

    def _build_word_tab(self):
        tab = self.tab_word
        form = ttk.LabelFrame(tab, text="Mot hébreu à analyser")
        form.pack(fill="x", padx=8, pady=8)

        self.word_entry = tk.Entry(form, font=HEBREW_FONT, justify="right")
        self.word_entry.pack(fill="x", padx=4, pady=4)
        self.word_entry.bind("<FocusIn>", self._remember_target)

        hint = ttk.Label(form,
                         text="Saisissez le mot avec le nikkud mais sans les teamim. "
                              "Les préfixes (ב/כ/ל/מ/ו/ה/ש) restent attachés.",
                         wraplength=760, justify="left")
        hint.pack(anchor="w", padx=4, pady=(2, 6))

        self._build_keyboard(form)

        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.word_format = tk.StringVar(value="text")
        ttk.Radiobutton(opts, text="Texte", variable=self.word_format,
                        value="text").pack(side="left")
        ttk.Radiobutton(opts, text="JSON", variable=self.word_format,
                        value="json").pack(side="left")

        self.btn_word = ttk.Button(tab, text="Analyser le mot",
                                   command=self._run_word)
        self.btn_word.pack(anchor="w", padx=8, pady=8)
        self.btn_word.state(["disabled"])

        self._build_output(tab)

    def _build_phrase_tab(self):
        tab = self.tab_phrase
        form = ttk.LabelFrame(tab, text="Phrase hébreu à analyser")
        form.pack(fill="both", expand=False, padx=8, pady=8)

        self.phrase_text = tk.Text(form, font=HEBREW_FONT, height=3,
                                   wrap="word", padx=4, pady=4)
        self.phrase_text.pack(fill="x", padx=4, pady=4)
        self.phrase_text.bind("<FocusIn>", self._remember_target)

        hint = ttk.Label(form,
                         text="Séparez les mots par des espaces. L'analyse est indicative "
                              "(pas de parsing syntaxique complet).",
                         wraplength=760, justify="left")
        hint.pack(anchor="w", padx=4, pady=(2, 6))

        self._build_keyboard(form)

        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.phrase_format = tk.StringVar(value="text")
        ttk.Radiobutton(opts, text="Texte", variable=self.phrase_format,
                        value="text").pack(side="left")
        ttk.Radiobutton(opts, text="JSON", variable=self.phrase_format,
                        value="json").pack(side="left")

        self.btn_phrase = ttk.Button(tab, text="Analyser la phrase",
                                     command=self._run_phrase)
        self.btn_phrase.pack(anchor="w", padx=8, pady=8)
        self.btn_phrase.state(["disabled"])

        self._build_output(tab)

    def _build_keyboard(self, parent):
        kb_frame = ttk.LabelFrame(parent, text="Clavier hébreu (UTF-8)")
        kb_frame.pack(fill="x", padx=4, pady=(2, 6))
        self.keyboard = HebrewKeyboard(kb_frame, self._get_target)
        self.keyboard.pack(fill="x", padx=4, pady=4)

    def _build_output(self, parent):
        frame = ttk.LabelFrame(parent, text="Résultat")
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.output_text = tk.Text(frame, font=HEBREW_FONT_MONO, wrap="word")
        self.output_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, command=self.output_text.yview)
        scroll.pack(side="right", fill="y")
        self.output_text.configure(yscrollcommand=scroll.set)
        self.output_text.configure(state="disabled")
        # Associer la zone de résultat partagée (une par onglet).
        parent._output = self.output_text

    # --- Cible du clavier virtuel ----------------------------------------
    def _remember_target(self, event):
        self._target_widget = event.widget

    def _get_target(self):
        # Priorité au widget ayant le focus ; sinon l'entrée du clavier.
        w = self._target_widget
        if w is not None and w.winfo_exists():
            return w
        # Fallback : selon l'onglet actif.
        idx = self.notebook.select()
        if not idx:
            return None
        if self.notebook.tab(idx, "text") == "Mot":
            return self.word_entry
        if self.notebook.tab(idx, "text") == "Phrase":
            return self.phrase_text
        return None

    # --- Chargement de la base BHSA --------------------------------------
    def _start_loading(self):
        def worker():
            try:
                api = load_corpus()
                self._work_queue.put(("loaded", api))
            except DataNotFoundError as exc:
                self._work_queue.put(("error", str(exc)))
            except Exception as exc:  # noqa: BLE001
                self._work_queue.put(("error", repr(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_corpus_loaded(self, api):
        self.api = api
        self.status.configure(text="Base BHSA chargée. Prêt.")
        for btn in (self.btn_verse, self.btn_word, self.btn_phrase):
            btn.state(["!disabled"])
        self._populate_books()

    def _on_corpus_error(self, msg):
        self.status.configure(text="Erreur de chargement de la base BHSA.")
        messagebox.showerror(
            "Base BHSA introuvable",
            f"Impossible de charger la base BHSA.\n\n{msg}\n\n"
            "Placez un clone de ETCBC/bhsa (branche data2021) à bhsa_repo/tf/c, "
            "ou définissez la variable BHSA_DATA.",
        )

    # --- Peuplement des listes déroulantes ------------------------------
    def _populate_books(self):
        F = self.api.F
        # Ordre canonique de la Bible hébraïque (Torah en tête) = ordre
        # naturel des nœuds « book » dans Text-Fabric.
        self._book_order = []
        display = []
        for b in F.otype.s("book"):
            bhsa = F.book.v(b)
            fr = book_french(bhsa)
            self._book_order.append((bhsa, fr, b))
            display.append(fr)
        self.book_combo["values"] = display
        # Index internes pour retrouver les bornes (chapitres/versets).
        self._book_index = {fr: (bhsa, b) for bhsa, fr, b in self._book_order}
        if display:
            self.book_combo.current(0)
            self._on_book_change()

    def _on_book_change(self, event=None):
        if self.api is None:
            return
        F, L = self.api.F, self.api.L
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            return
        _bhsa, book_node = entry
        chapters = sorted({F.chapter.v(c) for c in L.i(book_node, "chapter")})
        self._chapters_for_book = chapters
        self.chapter_combo["values"] = [str(c) for c in chapters]
        if chapters:
            self.chapter_combo.current(0)
            self._on_chapter_change()

    def _on_chapter_change(self, event=None):
        if self.api is None:
            return
        F, L = self.api.F, self.api.L
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            return
        _bhsa, book_node = entry
        try:
            chap = int(self.chapter_var.get())
        except ValueError:
            return
        chap_node = next((c for c in L.i(book_node, "chapter")
                         if F.chapter.v(c) == chap), None)
        if chap_node is None:
            self.verse_combo["values"] = []
            return
        verses = sorted({F.verse.v(v) for v in L.i(chap_node, "verse")})
        self.verse_combo["values"] = [str(v) for v in verses]
        if verses:
            self.verse_combo.current(0)

    # --- Lancement des analyses (en arrière-plan) -----------------------
    def _set_output(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _disable_buttons(self):
        for btn in (self.btn_verse, self.btn_word, self.btn_phrase):
            btn.state(["disabled"])

    def _enable_buttons(self):
        if self.api is not None:
            for btn in (self.btn_verse, self.btn_word, self.btn_phrase):
                btn.state(["!disabled"])

    def _run_verse(self):
        if self.api is None:
            return
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            messagebox.showwarning("Référence", "Sélectionnez un livre.")
            return
        bhsa, _b = entry
        chap = self.chapter_var.get()
        verse = self.verse_var.get()
        if not chap or not verse:
            messagebox.showwarning("Référence", "Sélectionnez chapitre et verset.")
            return
        reference = f"{fr} {chap}:{verse}"
        fmt = self.verse_format.get()
        no_words = self.verse_no_words.get()
        out = self.tab_verse._output
        self._disable_buttons()
        self.status.configure(text=f"Analyse : {reference}…")

        def worker():
            try:
                analysis = analyze_verse_by_reference(self.api, reference)
                if fmt == "json":
                    result = format_json(analysis)
                elif fmt == "summary":
                    summary = format_summary(analysis)
                    lines = ["=== Règles détectées (synthèse) ==="]
                    for level in ("clause", "phrase", "word"):
                        lines.append(f"\n[{level}]")
                        for r in summary[level]:
                            lines.append(f"  - {r}")
                    result = "\n".join(lines)
                else:
                    result = format_text(analysis, verbose_words=not no_words)
                self._work_queue.put(("verse_done", result))
            except ValueError as exc:
                self._work_queue.put(("verse_done", f"Erreur : {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _run_word(self):
        if self.api is None:
            return
        form = self.word_entry.get().strip()
        if not form:
            messagebox.showwarning("Mot", "Saisissez un mot hébreu.")
            return
        fmt = self.word_format.get()
        F, L = self.api.F, self.api.L
        out = self.tab_word._output
        self._disable_buttons()
        self.status.configure(text=f"Analyse du mot « {form} »…")

        def worker():
            analysis = analyze_word(F, L, form)
            if fmt == "json":
                result = format_word_json(analysis)
            else:
                result = format_word(analysis)
            self._work_queue.put(("word_done", result))

        threading.Thread(target=worker, daemon=True).start()

    def _run_phrase(self):
        if self.api is None:
            return
        phrase = self.phrase_text.get("1.0", "end").strip()
        if not phrase:
            messagebox.showwarning("Phrase", "Saisissez une phrase hébreu.")
            return
        fmt = self.phrase_format.get()
        F, L = self.api.F, self.api.L
        out = self.tab_phrase._output
        self._disable_buttons()
        self.status.configure(text="Analyse de la phrase…")

        def worker():
            analysis = analyze_phrase(F, L, phrase)
            if fmt == "json":
                result = format_phrase_json(analysis)
            else:
                result = format_phrase(analysis)
            self._work_queue.put(("phrase_done", result))

        threading.Thread(target=worker, daemon=True).start()

    # --- Polling ----------------------------------------------------------
    def _poll_queue(self):
        try:
            while True:
                kind, payload = self._work_queue.get_nowait()
                if kind == "loaded":
                    self._on_corpus_loaded(payload)
                elif kind == "error":
                    self._on_corpus_error(payload)
                elif kind == "verse_done":
                    self._set_output(self.tab_verse._output, payload)
                    self.status.configure(text="Prêt.")
                    self._enable_buttons()
                elif kind == "word_done":
                    self._set_output(self.tab_word._output, payload)
                    self.status.configure(text="Prêt.")
                    self._enable_buttons()
                elif kind == "phrase_done":
                    self._set_output(self.tab_phrase._output, payload)
                    self.status.configure(text="Prêt.")
                    self._enable_buttons()
        except queue.Empty:
            pass
        self.root.after(120, self._poll_queue)


def main():
    root = tk.Tk()
    AnalyseurGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
