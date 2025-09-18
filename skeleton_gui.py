"""
Einfaches GUI-Smoketest-Fenster (tkinter)
version 0.5
- Keine externen Abhängigkeiten (nur Standardbibliothek)
- Optional: CSV-Header mit csv.Sniffer erkennen und in Comboboxen laden
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from typing import List


class GUITestApp(tk.Tk):
    """Kleines Testfenster für GUI-Elemente des Projekts."""

    def __init__(self) -> None:
        super().__init__()
        self.title("GUI-Smoketest – CSV Daten Plotter")
        self.geometry("900x560")
        self.minsize(780, 480)

        # Interner Zustand
        self.loaded_file: str | None = None
        self.columns: List[str] = []
        self.chart_type = tk.StringVar(value="line")
        self.legend_var = tk.BooleanVar(value=True)
        self.title_var = tk.StringVar(value="Mein Testdiagramm")

        self._build_menu()
        self._build_body()
        self._build_statusbar()
        self._log("App gestartet. Bereit für Tests.")

    # --- Aufbau UI ---------------------------------------------------------
    def _build_menu(self) -> None:
        """Einfache Menüleiste (Datei → Öffnen/Beenden)."""
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="CSV öffnen…", command=self.on_load_file)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.destroy)
        menubar.add_cascade(label="Datei", menu=file_menu)
        self.config(menu=menubar)

    def _build_body(self) -> None:
        """Hauptbereich: Felder, Buttons, Log."""
        root = ttk.Frame(self, padding=16)
        root.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Layout-Spalten streckbar machen
        for c in range(6):
            root.columnconfigure(c, weight=1)
        root.rowconfigure(4, weight=1)

        # Datei-Box
        file_lbl = ttk.Label(root, text="Datei:")
        self.file_val = ttk.Label(root, text="— keine Datei —", foreground="#555")
        open_btn = ttk.Button(root, text="CSV öffnen…", command=self.on_load_file)
        file_lbl.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.file_val.grid(row=0, column=1, columnspan=4, sticky="we")
        open_btn.grid(row=0, column=5, sticky="e")

        # Achsen-Auswahl
        ttk.Label(root, text="X-Achse:").grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.cmb_x = ttk.Combobox(root, state="readonly", values=self.columns)
        self.cmb_x.grid(row=1, column=1, columnspan=2, sticky="we", pady=(12, 0))

        ttk.Label(root, text="Y-Achse:").grid(row=1, column=3, sticky="w", pady=(12, 0))
        self.cmb_y = ttk.Combobox(root, state="readonly", values=self.columns)
        self.cmb_y.grid(row=1, column=4, columnspan=2, sticky="we", pady=(12, 0))

        # Diagrammtyp (RadioButtons)
        typ_frame = ttk.LabelFrame(root, text="Diagrammtyp", padding=10)
        typ_frame.grid(row=2, column=0, columnspan=3, sticky="we", pady=(12, 0))
        ttk.Radiobutton(typ_frame, text="Linie", value="line", variable=self.chart_type).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(typ_frame, text="Balken", value="bar", variable=self.chart_type).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(typ_frame, text="Punkte", value="scatter", variable=self.chart_type).grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(typ_frame, text="Fläche", value="area", variable=self.chart_type).grid(row=0, column=3, sticky="w")

        # Optionen
        opt_frame = ttk.LabelFrame(root, text="Optionen", padding=10)
        opt_frame.grid(row=2, column=3, columnspan=3, sticky="we", pady=(12, 0))
        ttk.Checkbutton(opt_frame, text="Legende anzeigen", variable=self.legend_var).grid(row=0, column=0, sticky="w")
        ttk.Label(opt_frame, text="Titel:").grid(row=0, column=1, sticky="e", padx=(12, 6))
        ttk.Entry(opt_frame, textvariable=self.title_var).grid(row=0, column=2, sticky="we")
        opt_frame.columnconfigure(2, weight=1)

        # Bedien-Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=6, sticky="we", pady=(12, 0))
        ttk.Button(btn_frame, text="Plot (Demo)", command=self.on_plot).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Reset", command=self.on_reset).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Schließen", command=self.destroy).pack(side=tk.RIGHT)

        # Log-Feld (ersetzt echte Ausgabe)
        log_lbl = ttk.Label(root, text="Ereignis-Log:")
        log_lbl.grid(row=4, column=0, sticky="sw", pady=(12, 0))
        self.txt_log = tk.Text(root, height=10, wrap="word")
        self.txt_log.grid(row=5, column=0, columnspan=6, sticky="nsew")
        yscroll = ttk.Scrollbar(root, orient="vertical", command=self.txt_log.yview)
        yscroll.grid(row=5, column=6, sticky="ns")
        self.txt_log.configure(yscrollcommand=yscroll.set)

    def _build_statusbar(self) -> None:
        """Einfache Statusleiste unten."""
        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=1, column=0, sticky="we")
        self.status = ttk.Label(self, text="Bereit.", anchor="w", padding=(8, 4))
        self.status.grid(row=2, column=0, sticky="we")

    # --- Aktionen -----------------------------------------------------------
    def on_load_file(self) -> None:
        """CSV-Datei wählen, Header erkennen und Comboboxen füllen."""
        path = filedialog.askopenfilename(
            title="CSV wählen",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
        )
        if not path:
            self._log("Öffnen abgebrochen.")
            return

        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    # Fallback: Komma als Standard-Trenner
                    dialect = csv.excel
                reader = csv.reader(f, dialect)
                header = next(reader, [])
        except Exception as ex:  # bewusst allgemein für Demo-Zwecke
            messagebox.showerror("Fehler beim Lesen", str(ex))
            self._log(f"Fehler beim Lesen: {ex}")
            return

        # Minimaler Schutz: leere/zu lange Spaltennamen filtern
        header = [h.strip()[:50] for h in header if h and h.strip()]
        if not header:
            header = ["Spalte_1", "Spalte_2", "Spalte_3"]  # Fallback

        self.loaded_file = path
        self.columns = header
        self.cmb_x.configure(values=self.columns)
        self.cmb_y.configure(values=self.columns)
        if self.columns:
            self.cmb_x.set(self.columns[0])
            if len(self.columns) > 1:
                self.cmb_y.set(self.columns[1])
        self.file_val.configure(text=path)
        self._set_status(f"Geladen: {path}")
        self._log(f"CSV geladen. Spalten: {', '.join(self.columns)}")

    def on_plot(self) -> None:
        """Nur Demo: zeigt die gewählten Optionen im Log an."""
        x = self.cmb_x.get() or "(leer)"
        y = self.cmb_y.get() or "(leer)"
        msg = (
            f"Plot (Demo) → Typ: {self.chart_type.get()}, X: {x}, Y: {y}, "
            f"Titel: '{self.title_var.get()}', Legende: {self.legend_var.get()}"
        )
        self._log(msg)
        self._set_status("Plot (Demo) ausgeführt – kein echtes Diagramm.")

    def on_reset(self) -> None:
        """Eingaben zurücksetzen (einfach und nachvollziehbar)."""
        self.cmb_x.set("")
        self.cmb_y.set("")
        self.chart_type.set("line")
        self.legend_var.set(True)
        self.title_var.set("Mein Testdiagramm")
        self._log("Eingaben zurückgesetzt.")
        self._set_status("Zurückgesetzt.")

    # --- Hilfsfunktionen ----------------------------------------------------
    def _log(self, text: str) -> None:
        """Text in das Log-Feld schreiben und automatisch scrollen."""
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")

    def _set_status(self, text: str) -> None:
        """Statusleiste aktualisieren."""
        self.status.configure(text=text)


if __name__ == "__main__":
    # Startpunkt für den schnellen Test
    app = GUITestApp()
    app.mainloop()
