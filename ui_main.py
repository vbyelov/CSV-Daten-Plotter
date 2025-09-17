import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional


class UIMain(ttk.Frame):
    """
    Haupt-UI für das Projekt.

    Änderungen in dieser Version:
    - Auswahl des Diagrammtyps jetzt über Radiobuttons (statt Combobox)
    - Klare Gruppierung nach Diagramm-Familien (Line/Area, Bar/Hist, Pie/Polar)
    - Ein einziges StringVar (chart_type_var) hält den Zustand und triggert den Callback

    Hinweis zur Integration:
    - Übergib beim Erzeugen passende Callback-Funktionen aus app.py
      (siehe __init__-Signatur). Nichts Komplexes – reine Weiterleitung.
    - Die Schlüsselwerte für Diagrammtypen sind:
        "line", "stacked_area", "bar", "hist", "pie", "polar"
      => Diese müssen mit den Keys im Dispatcher in plotter.py übereinstimmen.
    """

    # Konstanten: Keys müssen mit plotter.CHHART_HANDLERS übereinstimmen
    CHART_KEYS = ("line", "stacked_area", "bar", "hist", "pie", "polar")

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_open_csv: Optional[Callable[[], None]] = None,
        on_chart_type_changed: Optional[Callable[[str], None]] = None,
        on_x_changed: Optional[Callable[[str], None]] = None,
        on_y_changed: Optional[Callable[[str], None]] = None,
        on_plot_clicked: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master)
        self.on_open_csv = on_open_csv
        self.on_chart_type_changed = on_chart_type_changed
        self.on_x_changed = on_x_changed
        self.on_y_changed = on_y_changed
        self.on_plot_clicked = on_plot_clicked

        # ---- Layout-Grundstruktur -------------------------------------------------
        # Oberer Bereich: CSV-Auswahl
        self._build_file_frame()
        # Mittlerer Bereich: Diagrammtyp via Radiobuttons
        self._build_chart_type_frame()
        # Bereich für Spaltenauswahl (X/Y)
        self._build_axes_frame()
        # Button-Leiste
        self._build_actions_frame()

        # Optionale Größenanpassung
        self.columnconfigure(0, weight=1)

    # -------------------------------------------------------------------------
    # Öffentliche Properties / Getter
    # -------------------------------------------------------------------------
    @property
    def chart_type_var(self) -> tk.StringVar:
        return self._chart_type_var

    def get_chart_type(self) -> str:
        """Liefert den aktuell gewählten Diagrammtyp (Key)."""
        return self._chart_type_var.get()

    def set_columns(self, numeric: List[str], categorical: List[str]) -> None:
        """
        Setzt die verfügbaren Spalten für X/Y.
        - Für X: typischerweise numerisch/zeitlich
        - Für Y: numerisch (bei Pie: Kategorie + Wert)
        """
        self.cmb_x["values"] = numeric + categorical
        self.cmb_y["values"] = numeric

    # -------------------------------------------------------------------------
    # Interne UI-Bausteine
    # -------------------------------------------------------------------------
    def _build_file_frame(self) -> None:
        # Datei/CSV Auswahl – bewusst minimal gehalten
        frm = ttk.LabelFrame(self, text="CSV-Datei")
        frm.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Pfad:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.ent_path = ttk.Entry(frm)
        self.ent_path.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ttk.Button(frm, text="Öffnen…", command=self._on_open_csv_click).grid(
            row=0, column=2, padx=6, pady=6
        )

    def _build_chart_type_frame(self) -> None:
        # Radiobuttons zur Auswahl des Diagrammtyps (ersetzt Combobox)
        lbf = ttk.LabelFrame(self, text="Diagrammtyp")
        lbf.grid(row=1, column=0, sticky="ew", padx=8, pady=4)

        # Ein gemeinsames StringVar für alle Radiobuttons
        self._chart_type_var = tk.StringVar(value="line")  # Default

        # Drei kompakte Gruppen für bessere Übersicht
        grp1 = ttk.LabelFrame(lbf, text="Line & Area")
        grp2 = ttk.LabelFrame(lbf, text="Bar & Hist")
        grp3 = ttk.LabelFrame(lbf, text="Pie & Polar")
        grp1.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        grp2.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        grp3.grid(row=0, column=2, padx=6, pady=6, sticky="w")

        # Kurzlabels, Werte = Keys für plotter-Dispatcher
        self._add_radio(grp1, "Line", "line")
        self._add_radio(grp1, "Stacked Area", "stacked_area")
        self._add_radio(grp2, "Bar", "bar")
        self._add_radio(grp2, "Histogram", "hist")
        self._add_radio(grp3, "Pie", "pie")
        self._add_radio(grp3, "Polar", "polar")

    def _add_radio(self, parent: tk.Misc, text: str, value: str) -> None:
        """Hilfsfunktion: Radiobutton mit gemeinsamem StringVar anlegen."""
        rb = ttk.Radiobutton(
            parent,
            text=text,
            value=value,
            variable=self._chart_type_var,
            command=self._on_chart_type_changed,
        )
        # Kompakte Anordnung in zwei Spalten
        children = len(parent.grid_slaves())
        r, c = divmod(children, 2)
        rb.grid(row=r, column=c, padx=4, pady=2, sticky="w")

    def _build_axes_frame(self) -> None:
        lbf = ttk.LabelFrame(self, text="Achsen / Felder")
        lbf.grid(row=2, column=0, sticky="ew", padx=8, pady=4)
        for col in range(4):
            lbf.columnconfigure(col, weight=1)

        ttk.Label(lbf, text="X:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.cmb_x = ttk.Combobox(lbf, state="readonly")
        self.cmb_x.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.cmb_x.bind("<<ComboboxSelected>>", self._on_x_selected)

        ttk.Label(lbf, text="Y:").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.cmb_y = ttk.Combobox(lbf, state="readonly")
        self.cmb_y.grid(row=0, column=3, padx=6, pady=6, sticky="ew")
        self.cmb_y.bind("<<ComboboxSelected>>", self._on_y_selected)

    def _build_actions_frame(self) -> None:
        frm = ttk.Frame(self)
        frm.grid(row=3, column=0, sticky="ew", padx=8, pady=(4, 8))
        frm.columnconfigure(0, weight=1)

        self.btn_plot = ttk.Button(frm, text="Plot", command=self._on_plot_click)
        self.btn_plot.grid(row=0, column=1, padx=6, pady=6, sticky="e")

    # -------------------------------------------------------------------------
    # Interne Event-Handler – jeweils dünne Weiterleitungen zu app.py
    # -------------------------------------------------------------------------
    def _on_open_csv_click(self) -> None:
        # CSV-Öffnen an app.py delegieren
        if self.on_open_csv:
            self.on_open_csv()

    def _on_chart_type_changed(self) -> None:
        # Reagiert auf Radiobutton-Auswahl
        if self.on_chart_type_changed:
            self.on_chart_type_changed(self._chart_type_var.get())

    def _on_x_selected(self, _event: tk.Event) -> None:
        if self.on_x_changed:
            self.on_x_changed(self.cmb_x.get())

    def _on_y_selected(self, _event: tk.Event) -> None:
        if self.on_y_changed:
            self.on_y_changed(self.cmb_y.get())

    def _on_plot_click(self) -> None:
        if self.on_plot_clicked:
            self.on_plot_clicked()


# ----------------------------------------------------------------------------
# Manuelles Testen (optional): Nur wenn Datei direkt ausgeführt wird
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    def _log(msg: str):
        print(msg)

    root = tk.Tk()
    root.title("CSV-Daten-Plotter – UI-Test")

    ui = UIMain(
        root,
        on_open_csv=lambda: _log("CSV öffnen…"),
        on_chart_type_changed=lambda key: _log(f"Diagrammtyp: {key}"),
        on_x_changed=lambda x: _log(f"X geändert: {x}"),
        on_y_changed=lambda y: _log(f"Y geändert: {y}"),
        on_plot_clicked=lambda: _log("Plot klicken"),
    )
    ui.pack(fill="both", expand=True)

    # Demo: Spalten füllen
    ui.set_columns(numeric=["A", "B", "C"], categorical=["Stadt", "Land"])

    root.geometry("700x320")
    root.mainloop()
