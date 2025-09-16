# ui_main.py
# Einfache Tkinter-Oberfläche für CSV Daten Plotter
# - Ordner wählen und CSV-Dateien listen
# - Spaltenauswahl (X / Y-Mehrfachauswahl)
# - Plot-Typ wählen und zeichnen
# - PNG speichern
# - Statistik-Panel unter dem Plot anzeigen

import os
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Hinweis: Keine zusätzlichen Pakete nötig. pandas wird in der UI nicht verwendet.


class MainUI:
    def __init__(self, root,
                 on_select_folder=None,
                 on_select_file=None,
                 on_plot=None,
                 on_save_png=None):
        # Callbacks aus app.py
        self.on_select_folder = on_select_folder
        self.on_select_file = on_select_file
        self.on_plot = on_plot
        self.on_save_png = on_save_png

        # Zustand
        self.current_folder = None
        self.current_file = None
        self.plot_type_var = tk.StringVar(value="Line")

        # Hauptlayout: links Steuerung, rechts Plot+Statistik
        self.container = ttk.Frame(root)
        self.container.pack(fill="both", expand=True)

        self.left = ttk.Frame(self.container, padding=8)
        self.left.pack(side="left", fill="y")

        self.right = ttk.Frame(self.container, padding=8)
        self.right.pack(side="right", fill="both", expand=True)

        # ---------------------------
        # Linke Seite: Ordner/Dateien
        # ---------------------------
        self._build_folder_file_block()

        # ---------------------------
        # Linke Seite: Auswahl/Plot
        # ---------------------------
        self._build_controls_block()

        # ---------------------------
        # Rechte Seite: Plot + Statistik
        # ---------------------------
        self._build_plot_block()
        self._build_stats_block()

    # =========================================
    # Aufbau linke Seite: Ordner und Datei-Liste
    # =========================================
    def _build_folder_file_block(self):
        grp = ttk.LabelFrame(self.left, text="Ordner und CSV", padding=8)
        grp.pack(fill="x")

        # Ordner wählen
        btn_folder = ttk.Button(grp, text="Ordner wählen", command=self._choose_folder)
        btn_folder.pack(fill="x")

        # Dateiliste
        self.file_list = tk.Listbox(grp, height=12, exportselection=False)
        self.file_list.pack(fill="both", expand=True, pady=(8, 0))

        # Scrollbar für Dateiliste
        scrollbar = ttk.Scrollbar(grp, orient="vertical", command=self.file_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        # Event: Datei anklicken
        self.file_list.bind("<<ListboxSelect>>", self._on_file_click)

    # =========================================
    # Aufbau linke Seite: Spalten/Plot-Steuerung
    # =========================================
    def _build_controls_block(self):
        grp = ttk.LabelFrame(self.left, text="Auswahl und Plot", padding=8)
        grp.pack(fill="both", expand=True, pady=(8, 0))

        # Plot-Typ
        ttk.Label(grp, text="Plot-Typ:").pack(anchor="w")
        self.plot_type_cb = ttk.Combobox(
            grp,
            state="readonly",
            values=["Line", "Pie", "Histogram", "Stacked Area", "Polar"],
            textvariable=self.plot_type_var
        )
        self.plot_type_cb.pack(fill="x", pady=(0, 8))

        # X-Spalte (einfach)
        ttk.Label(grp, text="X-Spalte (Kategorie/Datum):").pack(anchor="w")
        self.x_cb = ttk.Combobox(grp, state="readonly", values=[])
        self.x_cb.pack(fill="x", pady=(0, 8))

        # Y-Spalten (Mehrfachauswahl)
        ttk.Label(grp, text="Y-Spalten (numerisch):").pack(anchor="w")
        self.y_list = tk.Listbox(grp, height=8, selectmode="extended", exportselection=False)
        self.y_list.pack(fill="both", expand=True)

        y_scroll = ttk.Scrollbar(grp, orient="vertical", command=self.y_list.yview)
        y_scroll.pack(side="right", fill="y")
        self.y_list.configure(yscrollcommand=y_scroll.set)

        # Buttons: Plot + PNG speichern
        btn_plot = ttk.Button(grp, text="Plot zeichnen", command=self._on_plot_click)
        btn_plot.pack(fill="x", pady=(8, 4))

        btn_save = ttk.Button(grp, text="PNG speichern", command=self._on_save_png_click)
        btn_save.pack(fill="x")

    # =========================================
    # Aufbau rechte Seite: Plot und Statistik
    # =========================================
    def _build_plot_block(self):
        grp = ttk.LabelFrame(self.right, text="Diagramm", padding=8)
        grp.pack(fill="both", expand=True)

        # Matplotlib Figure + Canvas
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=grp)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

    def _build_stats_block(self):
        grp = ttk.LabelFrame(self.right, text="Statistik", padding=8)
        grp.pack(fill="x", expand=False, pady=(8, 0))

        # Textfeld (read-only) für Statistik
        self.stats_text = tk.Text(grp, height=10, wrap="word")
        self.stats_text.pack(fill="both", expand=True)

        # read-only simulieren: wir erlauben nur programmatische Änderungen
        self.stats_text.bind("<Key>", lambda e: "break")

    # =========================================
    # Öffentliche Methoden (wird von app.py genutzt)
    # =========================================
    def list_csv_files(self, folder_path):
        """Zeigt CSV-Dateien aus dem gewählten Ordner."""
        self.current_folder = folder_path
        self.file_list.delete(0, tk.END)

        if not folder_path or not os.path.isdir(folder_path):
            return

        csvs = sorted(glob.glob(os.path.join(folder_path, "*.csv")))
        for p in csvs:
            name = os.path.basename(p)
            self.file_list.insert(tk.END, name)

    def set_columns(self, columns):
        """Setzt Spalten in X-Combobox und Y-Liste."""
        if columns is None:
            columns = []

        # X
        self.x_cb["values"] = columns
        if columns:
            self.x_cb.set(columns[0])
        else:
            self.x_cb.set("")

        # Y
        self.y_list.delete(0, tk.END)
        for c in columns:
            self.y_list.insert(tk.END, c)

    def get_plot_axes(self):
        """Gibt die aktuelle Achse zurück (wird von app.py genutzt)."""
        return self.ax

    def draw_canvas(self):
        """Zeichnet den Canvas neu."""
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def update_stats_panel(self, text):
        """Aktualisiert den Statistik-Text."""
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)
        if text:
            self.stats_text.insert(tk.END, text)
        self.stats_text.config(state="disabled")

    def save_current_plot(self, source_csv_path):
        """
        Speichert das aktuelle Diagramm als PNG.
        Vorgeschlagener Dateiname basiert auf Quell-CSV und Plot-Typ.
        """
        # Vorschlag für Dateinamen
        base = "plot"
        if source_csv_path:
            base = os.path.splitext(os.path.basename(source_csv_path))[0]

        plot_type = self.plot_type_var.get() or "Plot"
        suggested = f"{base}_{plot_type}.png"

        file_path = filedialog.asksaveasfilename(
            title="PNG speichern",
            defaultextension=".png",
            initialfile=suggested,
            filetypes=[("PNG-Bild", "*.png")]
        )
        if not file_path:
            return

        try:
            self.figure.savefig(file_path, format="png")
            messagebox.showinfo("Gespeichert", f"PNG wurde gespeichert:\n{file_path}")
        except Exception as ex:
            messagebox.showerror("Fehler beim Speichern", str(ex))

    # =========================================
    # Interne Event-Handler
    # =========================================
    def _choose_folder(self):
        """Ordnerdialog öffnen und Liste aktualisieren."""
        path = filedialog.askdirectory(title="Ordner auswählen")
        if not path:
            return
        self.current_folder = path

        # Callback nach app.py
        if self.on_select_folder:
            self.on_select_folder(path)

    def _on_file_click(self, event):
        """Wird ausgelöst, wenn der Nutzer eine Datei in der Liste anklickt."""
        if self.current_folder is None:
            return
        sel = self.file_list.curselection()
        if not sel:
            return

        name = self.file_list.get(sel[0])
        full_path = os.path.join(self.current_folder, name)
        self.current_file = full_path

        # Callback nach app.py
        if self.on_select_file:
            self.on_select_file(full_path)

    def _on_plot_click(self):
        """Sammelt die Auswahl und ruft den Plot-Callback auf."""
        plot_type = self.plot_type_var.get()

        # X
        x_col = self.x_cb.get().strip()
        if x_col == "":
            x_col = None

        # Y (Mehrfachauswahl)
        y_cols = []
        for idx in self.y_list.curselection():
            y_cols.append(self.y_list.get(idx))

        # Callback nach app.py
        if self.on_plot:
            self.on_plot(plot_type, x_col, y_cols)

    def _on_save_png_click(self):
        """Speicher-Button -> Callback in app.py."""
        if self.on_save_png:
            self.on_save_png()
