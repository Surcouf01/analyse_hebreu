#!/usr/bin/env python3
"""Impression d'un paradigme de binyan (onglet Binyanim) avec aperçu.

Construit un document imprimable A4 pour UN binyan d'un résultat
d'analyse --binyanim (structure produite par parse_binyanim_text),
le met en pages via Pillow, l'affiche en aperçu (Tkinter) puis
l'imprime ou l'exporte en PDF.

Le rendu de l'hébreu est fait en ordre visuel (bidi_display.to_visual) :
sans libraqm, Pillow dessine les glyphes de gauche à droite ; la
conversion préalable garantit un ordre d'affichage correct, comme
dans les zones de résultat du GUI (cf. ResultText).
"""

import os
import re
import subprocess
import sys
import tempfile

import bidi_display

# Marques de directionnalité : utiles au widget Tkinter (ordre visuel
# stable), sans effet au dessin Pillow — retirées avant rendu.
_BIDI_MARKS_RE = re.compile("[\u200e\u200f\u202a-\u202e\u2066-\u2069]")

# Ligne de paradigme du texte marqué : «    <libellé>  <forme> »
_ROW_RE = re.compile(r"^ {4}(\S.*?)\s{2,}(\S.*)$")

# Ordre pédagogique des temps (cf. binyanim_to_text).
_TENSE_ORDER = ("perf", "impf", "impv", "juss", "coh")

_NON_FINITE_TITLE = "Formes non finies"


def _visual(text):
    """Texte en ordre visuel, sans marques de directionnalité (dessin)."""
    if not text:
        return ""
    return _BIDI_MARKS_RE.sub("", bidi_display.to_visual(str(text)))


def _binyan_entry(parsed, binyan_code):
    for b in parsed.get("binyanim", []):
        if b.get("code") == binyan_code:
            return b
    return None


def build_binyan_document(parsed, binyan_code):
    """Document imprimable d'un binyan à partir du texte parsé du CLI.

    ``parsed`` est la structure renvoyée par parse_binyanim_text ;
    ``binyan_code`` le code du binyan à imprimer (qal, nif, piel...).
    Renvoie :
        {"title", "subtitle", "meta": [...], "notes": [...],
         "sections": [{"title", "rows": [(libellé, forme), ...]}]}
    Lève ValueError si le binyan n'est pas dans le résultat.
    """
    entry = _binyan_entry(parsed, binyan_code)
    if entry is None:
        raise ValueError(f"Binyan inconnu dans le résultat : {binyan_code!r}")

    verb = parsed.get("verb", {})
    weak = parsed.get("weak", {})
    doc = {
        "title": f"Paradigme — {entry['name_fr']} ({entry['name_he']})",
        "subtitle": "",
        "meta": [],
        "notes": [],
        "sections": [],
    }

    # Sous-titre : racine, lemme BHSA, traduction française du verbe.
    parts = []
    if verb.get("root"):
        parts.append(f"Racine {verb['root']}")
    if verb.get("lex"):
        parts.append(f"lemme BHSA : {verb['lex']}")
    doc["subtitle"] = "  ·  ".join(parts)
    if verb.get("gloss_fr"):
        doc["subtitle"] += f"  « {verb['gloss_fr']} »"

    # Catégorie du verbe (fort ou faible).
    code = weak.get("code")
    if code in (None, "strong"):
        doc["meta"].append("Verbe fort (shalem) : conjugaison régulière.")
    elif weak.get("label"):
        doc["meta"].append(f"Verbe faible : {weak['label']}")

    # Attestation du binyan pour cette racine.
    if entry.get("exists") is False:
        if entry.get("mishnah_forms"):
            doc["meta"].append(
                "Binyan non attesté dans la Bible hébraïque pour cette "
                "racine, mais attesté dans la Mishna (paradigme "
                "théorique, construit par analogie).")
        else:
            doc["meta"].append(
                "Binyan non attesté dans la Bible hébraïque pour cette "
                "racine (paradigme théorique, construit par analogie).")
    elif entry.get("attested"):
        doc["meta"].append("Binyan attesté dans la BHSA pour cette forme.")

    # Traductions du verbe dans ce binyan.
    trads = []
    if entry.get("translation_fr"):
        trads.append(f"fr : {entry['translation_fr']}")
    if entry.get("translation_en"):
        trads.append(f"en : {entry['translation_en']}")
    if trads:
        doc["notes"].append("Traduction : " + "  |  ".join(trads))
    if entry.get("mishnah_forms"):
        doc["notes"].append(
            "Formes attestées dans la Mishna : "
            + ", ".join(entry["mishnah_forms"]))

    # Sections de paradigme : parsées depuis le texte du binyan. Les
    # en-têtes de temps («  Parfait (qatal) : ») ouvrent une section,
    # les lignes indentées «    libellé  forme » deviennent des rangées.
    current = None
    for line in entry.get("text", "").split("\n"):
        if not line.strip():
            continue
        if (line.startswith("--") or line.startswith("Traduction")
                or line.startswith("⚠") or line.startswith("✸")):
            continue
        row = _ROW_RE.match(line)
        if row and current is not None:
            current["rows"].append((row.group(1), row.group(2)))
            continue
        head = re.match(r"^ {2}(\S.*?)\s*:\s*$", line)
        if head:
            title = head.group(1).strip()
            current = {"title": title, "rows": []}
            doc["sections"].append(current)
    return doc


# --- Polices ----------------------------------------------------------------

# Paires (régulière, grasse) par ordre de priorité, par plateforme.
# Les polices doivent couvrir l'hébreu avec nikkud (DejaVu Sans, Arial,
# Tahoma, Noto Sans Hebrew).
def _font_pairs():
    if sys.platform == "win32":
        fonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        return [
            (os.path.join(fonts, "dejavusans.ttf"),
             os.path.join(fonts, "dejavusans-bold.ttf")),
            (os.path.join(fonts, "arial.ttf"),
             os.path.join(fonts, "arialbd.ttf")),
            (os.path.join(fonts, "tahoma.ttf"),
             os.path.join(fonts, "tahomabd.ttf")),
            (os.path.join(fonts, "segoeui.ttf"),
             os.path.join(fonts, "segoeuib.ttf")),
        ]
    if sys.platform == "darwin":
        supp = "/System/Library/Fonts/Supplemental"
        return [
            (os.path.join(supp, "DejaVuSans.ttf"),
             os.path.join(supp, "DejaVuSans-Bold.ttf")),
            (os.path.join(supp, "Arial Unicode.ttf"),
             os.path.join(supp, "Arial Unicode.ttf")),
            (os.path.join(supp, "Arial.ttf"),
             os.path.join(supp, "Arial Bold.ttf")),
        ]
    return [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf",
         "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]


def _load_font(bold, pt, dpi):
    """Charge une police (grasse ou régulière) ; repli : police par défaut."""
    from PIL import ImageFont
    size = max(1, round(pt * dpi / 72))
    for regular, bold_path in _font_pairs():
        path = bold_path if bold else regular
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        if not bold and os.path.isfile(regular):
            try:
                return ImageFont.truetype(regular, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# --- Rendu ------------------------------------------------------------------

def render_binyan_pages(doc, dpi=150, font_scale=1.0):
    """Met le document en pages A4 ; renvoie une liste de PIL.Image.

    ``font_scale`` (0.6 à 2.0) agrandit/réduit toutes les polices du
    document — utile pour compenser la réduction du mode 2 pages/
    feuille ou pour un rendu plus aéré (les tailles de base sont en
    points : 17/11/9/12/9,5/12/8 pour titre/sous-titre/méta/section/
    libellé/forme/pied de page).
    """
    from PIL import Image, ImageDraw

    font_scale = min(2.0, max(0.6, float(font_scale)))
    scale = dpi / 72.0
    width = round(8.27 * dpi)   # 210 mm
    height = round(11.69 * dpi)  # 297 mm
    margin = round(0.85 * dpi)
    footer_zone = round(0.55 * dpi)

    f_title = _load_font(True, 17 * font_scale, dpi)
    f_subtitle = _load_font(False, 11 * font_scale, dpi)
    f_meta = _load_font(False, 9 * font_scale, dpi)
    f_section = _load_font(True, 12 * font_scale, dpi)
    f_label = _load_font(False, 9.5 * font_scale, dpi)
    f_form = _load_font(True, 12 * font_scale, dpi)
    f_footer = _load_font(False, 8, dpi)

    ink = "#1a1a1a"
    grey = "#555555"
    rule = "#999999"

    pages = []

    def new_page():
        img = Image.new("RGB", (width, height), "white")
        pages.append((img, ImageDraw.Draw(img)))
        return img, ImageDraw.Draw(img), margin

    img, draw, y = new_page()

    def text(x, yy, s, font, fill=ink):
        draw.text((x, yy), _visual(s), font=font, fill=fill)

    def text_right(x_right, yy, s, font, fill=ink):
        s = _visual(s)
        w = draw.textlength(s, font=font)
        draw.text((x_right - w, yy), s, font=font, fill=fill)

    def ensure_room(needed):
        nonlocal img, draw, y
        if y + needed > height - margin - footer_zone:
            img, draw, y = new_page()

    # En-tête (première page uniquement).
    text(margin, y, doc["title"], f_title)
    y += round(f_title.size * 1.45)
    if doc.get("subtitle"):
        text(margin, y, doc["subtitle"], f_subtitle, grey)
        y += round(f_subtitle.size * 1.5)
    for line in doc.get("meta", []):
        text(margin, y, line, f_meta, grey)
        y += round(f_meta.size * 1.45)
    if doc.get("notes"):
        y += round(f_meta.size * 0.5)
        for line in doc["notes"]:
            text(margin, y, line, f_meta)
            y += round(f_meta.size * 1.45)
    y += round(f_meta.size * 0.6)
    draw.line([(margin, y), (width - margin, y)], fill=rule, width=2)
    y += round(f_meta.size * 1.2)

    # Sections : titre souligné + rangées « libellé (gauche) forme (droite) ».
    for section in doc.get("sections", []):
        if not section.get("rows"):
            continue
        ensure_room(round(f_section.size * 3))
        text(margin, y, section["title"], f_section)
        y += round(f_section.size * 1.35)
        for label, form in section["rows"]:
            row_h = max(f_label.size, f_form.size)
            ensure_room(round(row_h * 1.7))
            text(margin, y, label, f_label, grey)
            text_right(width - margin, y, form, f_form)
            y += round(row_h * 1.55)
        y += round(f_section.size * 0.8)

    # Pied de page : « analyse_hebreu — page i/n ».
    total = len(pages)
    for i, (pimg, pdraw) in enumerate(pages, start=1):
        footer = f"analyse_hebreu — page {i}/{total}"
        fw = pdraw.textlength(footer, font=f_footer)
        pdraw.text(((width - fw) / 2, height - margin + round(6 * scale)),
                   footer, font=f_footer, fill=grey)

    return [pimg for pimg, _ in pages]


def compose_sheets(pages, per_sheet=2, dpi=150):
    """Regroupe les pages en feuilles A4 paysage, 2 pages par feuille.

    Chaque page portrait est réduite pour tenir dans sa demi-colonne
    (marge + gouttière centraux) et centrée verticalement. Une feuille
    incomplète garde sa colonne droite vide.
    """
    if not pages:
        raise ValueError("Aucune page à composer.")
    if per_sheet != 2:
        raise ValueError(f"Disposition non supportée : {per_sheet} "
                         "pages par feuille.")
    from PIL import Image

    sheet_w = round(11.69 * dpi)   # 297 mm (paysage)
    sheet_h = round(8.27 * dpi)    # 210 mm
    margin = round(0.4 * dpi)
    gutter = round(0.5 * dpi)
    cell_w = (sheet_w - 2 * margin - gutter) // 2

    sheets = []
    for i in range(0, len(pages), per_sheet):
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
        for col, page in enumerate(pages[i:i + per_sheet]):
            scale = min(cell_w / page.width,
                        (sheet_h - 2 * margin) / page.height, 1.0)
            size = (max(1, round(page.width * scale)),
                    max(1, round(page.height * scale)))
            reduced = page if size == page.size else page.resize(size)
            x = margin + col * (cell_w + gutter) + (cell_w - size[0]) // 2
            y = (sheet_h - size[1]) // 2
            sheet.paste(reduced, (x, y))
        sheets.append(sheet)
    return sheets


def save_pdf(pages, path, dpi=150):
    """Écrit les pages dans un PDF (une page A4 par image)."""
    if not pages:
        raise ValueError("Aucune page à exporter.")
    pages[0].save(path, format="PDF", save_all=True,
                  append_images=pages[1:], resolution=dpi)


# --- Impression -------------------------------------------------------------

def print_pdf_file(path):
    """Imprime un PDF via la commande d'impression de la plateforme.

    Renvoie True si une commande a été lancée, False si le fichier
    doit être ouvert manuellement pour impression.
    """
    try:
        if sys.platform == "win32":
            os.startfile(path, "print")  # noqa: S606 (association PDF)
            return True
        if sys.platform == "darwin":
            subprocess.run(["lpr", path], check=True,
                           capture_output=True, timeout=30)
            return True
        for cmd in (["lp", path], ["lpr", path]):
            try:
                subprocess.run(cmd, check=True, capture_output=True,
                               timeout=30)
                return True
            except (OSError, subprocess.SubprocessError):
                continue
        return False
    except (OSError, subprocess.SubprocessError):
        return False


def open_pdf_file(path):
    """Ouvre le PDF avec l'application par défaut (repli d'impression)."""
    try:
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", path])  # noqa: S603,S607
        return True
    except OSError:
        return False


# --- Aperçu (Tkinter) -------------------------------------------------------

class BinyanPrintPreview:
    """Fenêtre d'aperçu avant impression (composition, pas d'héritage Tk).

    Importée paresseusement : le module reste utilisable (rendu, PDF,
    tests) sans tkinter ni affichage.
    """

    _MIN_ZOOM = 0.25
    _MAX_ZOOM = 3.0

    def __init__(self, parent, pages, title="Binyan", doc=None, dpi=150,
                 two_up=False, font_scale=100, on_close=None):
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        from PIL import ImageTk

        self._tk = tk
        self._messagebox = messagebox
        self._ImageTk = ImageTk
        self.doc = doc
        self._dpi = dpi
        self._on_close = on_close
        self.pages = pages
        self._two_up = tk.BooleanVar(value=bool(two_up))
        self._sheets_cache = None
        self._page = 0
        self._zoom = 1.0
        self._photo = None
        self._fit_job = None
        self._font_job = None

        self.win = tk.Toplevel(parent)
        self.win.title(f"Aperçu avant impression — {title}")
        self.win.geometry("980x960")
        self.win.transient(parent)

        bar = ttk.Frame(self.win)
        bar.pack(fill="x", padx=6, pady=6)
        self.btn_prev = ttk.Button(bar, text="◀", width=3,
                                   command=self._prev_page)
        self.btn_prev.pack(side="left")
        self.label_page = ttk.Label(bar, text="", width=10, anchor="center")
        self.label_page.pack(side="left", padx=4)
        self.btn_next = ttk.Button(bar, text="▶", width=3,
                                   command=self._next_page)
        self.btn_next.pack(side="left")
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y",
                                                    padx=8)
        ttk.Button(bar, text="−", width=3,
                   command=lambda: self._zoom_by(1 / 1.25)).pack(side="left")
        self.label_zoom = ttk.Label(bar, text="", width=8, anchor="center")
        self.label_zoom.pack(side="left", padx=4)
        ttk.Button(bar, text="+", width=3,
                   command=lambda: self._zoom_by(1.25)).pack(side="left")
        ttk.Button(bar, text="Ajuster", command=self._fit_width).pack(
            side="left", padx=4)
        # Impression économe : deux pages du paradigme côte à côte sur
        # une même feuille A4 paysage (colonnes réduites).
        ttk.Checkbutton(bar, text="2 pages/feuille",
                        variable=self._two_up,
                        command=self._on_two_up).pack(side="left", padx=8)
        self._two_up.trace_add("write", self._invalidate_sheets)

        # Taille de police du document (pourcentage des tailles de base).
        # Re-rendu différé : chaque frappe dans le champ re-programme le
        # rendu 400 ms plus tard (le rendu complet d'un paradigme prend
        # quelques centaines de ms).
        ttk.Label(bar, text="Police :").pack(side="left", padx=(8, 2))
        self.font_scale_var = tk.StringVar(value=str(int(font_scale)))
        self._font_spin = ttk.Spinbox(bar, from_=60, to=200, increment=10,
                                      width=5, textvariable=self.font_scale_var,
                                      command=self._rerender)
        self._font_spin.pack(side="left")
        ttk.Label(bar, text="%").pack(side="left")
        # Flèches de la spinbox : rendu immédiat (command ci-dessus) ;
        # frappe clavier : rendu différé, le temps de taper la valeur.
        self._font_spin.bind("<KeyRelease>", lambda e: self._on_font_scale())
        self._font_spin.bind("<Return>", lambda e: self._rerender())
        self._font_spin.bind("<FocusOut>", lambda e: self._rerender())

        ttk.Button(bar, text="Enregistrer en PDF…",
                   command=self._save_pdf).pack(side="right", padx=4)
        self.btn_print = ttk.Button(bar, text="Imprimer…", command=self._print)
        self.btn_print.pack(side="right", padx=4)
        ttk.Button(bar, text="Fermer",
                   command=self._close).pack(side="right", padx=4)

        wrap = ttk.Frame(self.win)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, background="#404040",
                                highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        yscroll = ttk.Scrollbar(wrap, orient="vertical",
                                command=self.canvas.yview)
        yscroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=yscroll.set)
        self.canvas.bind("<Configure>",
                         lambda e: self.win.after_idle(self._fit_if_needed))
        self.win.bind("<Escape>", lambda e: self._close())
        self.win.bind("<Prior>", lambda e: self._prev_page())
        self.win.bind("<Next>", lambda e: self._next_page())
        # Fermeture (Échap, croix, bouton) : propager les réglages à
        # l'appelant (persistance gui.properties) avant de détruire.
        self.win.protocol("WM_DELETE_WINDOW", self._close)

        self._fit_width(first=True)

    # --- disposition 2 pages/feuille ----------------------------------------

    def _close(self):
        """Ferme l'aperçu en propageant les réglages courants."""
        if self._on_close is not None:
            try:
                self._on_close(self._two_up.get(),
                               int(self.font_scale_var.get()))
            except (ValueError, TypeError):
                pass
        self.win.destroy()

    def _invalidate_sheets(self, *_args):
        """La case « 2 pages/feuille » a changé : composition à refaire."""
        self._sheets_cache = None

    def _on_font_scale(self):
        """Nouvelle taille de police : re-rend le document.

        Rendu immédiat sur les flèches de la spinbox (retour tactile) ;
        différé de 400 ms sur la frappe clavier (le temps de finir de
        taper la valeur). Sans document source (aperçu ouvert sur des
        pages déjà rendues), le contrôle est sans effet.
        """
        if self.doc is None:
            return
        if self._font_job is not None:
            try:
                self.win.after_cancel(self._font_job)
            except self._tk.TclError:
                pass
            self._font_job = None
        self._font_job = self.win.after(400, self._rerender)

    def _rerender(self):
        self._font_job = None
        raw = self.font_scale_var.get().strip()
        if not raw:
            return
        try:
            scale = float(raw) / 100.0
        except ValueError:
            return
        if not (0.6 <= scale <= 2.0):
            return
        # Le rendu d'un paradigme multi-pages peut prendre plusieurs
        # secondes : montrer l'activité (curseur, libellé) et forcer le
        # rafraîchissement avant de bloquer la boucle d'événements.
        self.win.configure(cursor="watch")
        self.label_page.configure(text="re-rendu…")
        self.win.update_idletasks()
        try:
            self.pages = render_binyan_pages(self.doc, dpi=self._dpi,
                                             font_scale=scale)
        except Exception as exc:
            self.win.configure(cursor="")
            self._messagebox.showerror(
                "Impression", f"Échec du re-rendu : {exc}")
            return
        self.win.configure(cursor="")
        self._sheets_cache = None
        self._page = 0
        self._fit_width(first=True)

    def _on_two_up(self):
        """Bascule 1/2 pages par feuille : recompose et rafraîchit l'aperçu."""
        self._page = 0
        self._fit_width(first=True)

    def _current_pages(self):
        """Pages affichées/imprimées selon la case « 2 pages/feuille ».

        La composition est mise en cache : recomposer à chaque affichage
        serait coûteux (redimensionnement des deux pages complètes)."""
        if not self._two_up.get() or len(self.pages) <= 1:
            return self.pages
        if self._sheets_cache is None:
            self._sheets_cache = compose_sheets(self.pages, per_sheet=2)
        return self._sheets_cache

    # --- pages et zoom ------------------------------------------------------

    def _show_page(self):
        shown_pages = self._current_pages()
        img = shown_pages[self._page]
        size = (max(1, round(img.width * self._zoom)),
                max(1, round(img.height * self._zoom)))
        shown = img if size == img.size else img.resize(size)
        self._photo = self._ImageTk.PhotoImage(shown)
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, size[0], size[1]))
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        self.label_page.configure(
            text=f"page {self._page + 1}/{len(shown_pages)}")
        self.label_zoom.configure(text=f"{round(self._zoom * 100)} %")
        self.btn_prev.state(["!disabled"] if self._page > 0 else ["disabled"])
        self.btn_next.state(["!disabled"] if self._page < len(shown_pages) - 1
                            else ["disabled"])

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._show_page()

    def _next_page(self):
        if self._page < len(self._current_pages()) - 1:
            self._page += 1
            self._show_page()

    def _zoom_by(self, factor):
        self._zoom = min(self._MAX_ZOOM, max(self._MIN_ZOOM,
                                             self._zoom * factor))
        self._show_page()

    def _fit_width(self, first=False):
        canvas_w = max(1, self.canvas.winfo_width())
        if first and canvas_w <= 1:
            self._zoom = 0.65
        else:
            self._zoom = min(self._MAX_ZOOM, max(
                self._MIN_ZOOM,
                (canvas_w - 24) / self._current_pages()[0].width))
        self._show_page()

    def _fit_if_needed(self):
        if self._fit_job is not None:
            self.win.after_cancel(self._fit_job)
        self._fit_job = self.win.after(150, self._fit_width)

    # --- impression et export ----------------------------------------------

    def _print(self):
        pdf = os.path.join(tempfile.gettempdir(), "analyse_hebreu_binyan.pdf")
        try:
            save_pdf(self._current_pages(), pdf)
        except (OSError, ValueError) as exc:
            self._messagebox.showerror(
                "Impression", f"Échec de la génération du PDF : {exc}")
            return
        if print_pdf_file(pdf):
            self._messagebox.showinfo(
                "Impression", "Document envoyé à l'imprimante.")
        elif open_pdf_file(pdf):
            self._messagebox.showinfo(
                "Impression",
                "Aucune imprimante en ligne de commande n'est disponible.\n"
                "Le PDF a été ouvert : imprimez-le depuis sa visionneuse.")
        else:
            self._messagebox.showwarning(
                "Impression",
                f"Impossible de lancer l'impression.\nPDF : {pdf}")

    def _save_pdf(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self.win, defaultextension=".pdf",
            filetypes=[("Fichier PDF", "*.pdf")])
        if not path:
            return
        try:
            save_pdf(self._current_pages(), path)
        except (OSError, ValueError) as exc:
            self._messagebox.showerror(
                "Enregistrement", f"Échec de l'enregistrement : {exc}")
            return
        self._messagebox.showinfo(
            "Enregistrement", f"PDF enregistré :\n{path}")


def open_binyan_preview(parent, parsed, binyan_code,
                        two_up=False, font_scale=100, on_close=None):
    """Construit le document du binyan, le met en pages et ouvre l'aperçu.

    ``two_up`` et ``font_scale`` (pourcentage) sont les réglages
    initiaux de disposition ; ``on_close(two_up, font_scale)`` est
    appelé à la fermeture pour persister les réglages.

    Renvoie la fenêtre d'aperçu, ou None si le binyan est introuvable
    (l'erreur est signalée par l'appelant).
    """
    doc = build_binyan_document(parsed, binyan_code)
    pages = render_binyan_pages(doc, font_scale=font_scale / 100.0)
    return BinyanPrintPreview(parent, pages, title=doc["title"], doc=doc,
                              two_up=two_up, font_scale=font_scale,
                              on_close=on_close)
