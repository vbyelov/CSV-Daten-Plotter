# app.py
# ------------------------------------------------------
# Hauptsteuerung der Anwendung:
# - CSV laden
# - Spaltenlisten füllen (ohne Vorauswahl)
# - Validierung je Diagrammtyp
# - Plot ausführen (ruft plotter.*)
# - Statistik (nur als Text in "Details") anzeigen
# - PNG speichern (Menü + Button neben Plot)
# ------------------------------------------------------

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd

from ui_main import MainUI
from data_loader import load_csv, infer_columns
from plotter import (
    plot_line,
    plot_stacked_area,
    plot_pie,
    plot_hist,
    plot_polar,
)


class AppController:
    def __init__(self, root: tk.Tk):
        self.ui = MainUI(root)
        self.df: pd.DataFrame | None = None
        self.colinfo: dict | None = None
        self.current_csv_path: str | None = None
        self.plot_done: bool = False

        # Events verbinden
        self.ui.btn_open.configure(command=self.on_open_file)
        self.ui.btn_plot.configure(command=self.on_plot_clicked)
        self.ui.btn_save.configure(command=self.on_save_png)

        # Menüleiste (Speichern als PNG)
        menu = tk.Menu(root)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Speichern als PNG", command=self.on_save_png)
        menu.add_cascade(label="Datei", menu=file_menu)
        root.config(menu=menu)

        # Änderungen beobachten, um Plot-Button zu steuern
        self.ui.plot_type.trace_add("write", lambda *_: self.update_controls_state())
        self.ui.cmb_x.bind("<<ComboboxSelected>>", lambda _e: self.update_controls_state())
        self.ui.lst_y.bind("<<ListboxSelect>>", lambda _e: self.update_controls_state())

        # Anfangszustand
        self.update_controls_state()

    # -----------------------------
    # Datei laden
    # -----------------------------
    def on_open_file(self):
        path = filedialog.askopenfilename(
            title="CSV auswählen",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return

        try:
            df = load_csv(path)
        except Exception as ex:
            messagebox.showerror("Fehler beim Laden", str(ex))
            return

        self.df = df
        self.current_csv_path = path
        self.colinfo = infer_columns(df)
        self.plot_done = False

        # Spaltenlisten füllen – ohne Vorauswahl
        cols = df.columns.tolist()
        self.ui.cmb_x["values"] = cols
        self.ui.cmb_x.set("")  # leer lassen
        self.ui.lst_y.delete(0, tk.END)
        for c in cols:
            self.ui.lst_y.insert(tk.END, c)

        # Basisinfo in Details
        numeric_count = len(self.colinfo.get("numeric", []))
        categorical_count = len(self.colinfo.get("categorical", []))
        details = [
            "BASIS-STATISTIK",
            f"  rows: {len(df)}",
            f"  cols: {len(df.columns)}",
            f"  #numeric: {numeric_count}",
            f"  #categorical: {categorical_count}",
            "",
            "Wähle Diagrammtyp und Spalten, dann 'Plot erzeugen'.",
        ]
        self.ui.update_details("\n".join(details))
        self.ui.update_status(f"Geladen: {os.path.basename(path)} "
                              f"({len(df)} Zeilen, {len(df.columns)} Spalten)")

        # Plotbereich leeren
        self.ui.clear_plot()

        # Steuerelemente aktualisieren
        self.update_controls_state()

    # -----------------------------
    # Validierung & UI-Steuerung
    # -----------------------------
    def get_selected_x(self) -> str | None:
        val = self.ui.cmb_x.get().strip()
        return val if val else None

    def get_selected_ys(self) -> list[str]:
        sel = self.ui.lst_y.curselection()
        cols = [self.ui.lst_y.get(i) for i in sel]
        return cols

    def update_controls_state(self):
        """Aktiviert/Deaktiviert den Plot-Button je nach Auswahl."""
        ok, _msg = self.validate_selection(silent=True)
        self.ui.btn_plot.configure(state="normal" if ok else "disabled")

    def validate_selection(self, silent: bool = False) -> tuple[bool, str]:
        """Prüft die Auswahl gemäß vereinfachter Regeln."""
        if self.df is None:
            return False, "Bitte zuerst eine CSV-Datei laden."

        ptype = self.ui.plot_type.get()
        if not ptype:
            return False, "Bitte Diagrammtyp wählen."

        x = self.get_selected_x()
        ys = self.get_selected_ys()

        if ptype == "Line":
            if not x:
                return False, "Line: Bitte X-Spalte wählen."
            if len(ys) < 1:
                return False, "Line: Mindestens eine Y-Spalte wählen."
            if not self._all_numeric(ys):
                return False, "Line: Y-Spalten müssen numerisch sein."

        elif ptype == "Stacked Area":
            if not x:
                return False, "Stacked Area: Bitte X-Spalte wählen."
            if len(ys) < 1:
                return False, "Stacked Area: Mindestens eine (besser zwei) Y-Spalten wählen."
            if not self._all_numeric(ys):
                return False, "Stacked Area: Y-Spalten müssen numerisch sein."

        elif ptype == "Pie":
            if not x:
                return False, "Pie: Bitte X (Labels) wählen."
            if len(ys) != 1:
                return False, "Pie: Genau eine Y-Spalte wählen."
            if not self._all_numeric(ys):
                return False, "Pie: Y muss numerisch sein."

        elif ptype == "Histogram":
            if len(ys) != 1:
                return False, "Histogram: Genau eine Y-Spalte wählen."
            if not self._all_numeric(ys):
                return False, "Histogram: Y muss numerisch sein."

        elif ptype == "Polar":
            if len(ys) != 1:
                return False, "Polar: Genau eine Y-Spalte wählen."
            if not self._all_numeric(ys):
                return False, "Polar: Y muss numerisch sein."

        else:
            return False, "Unbekannter Diagrammtyp."

        return True, "OK"

    def _all_numeric(self, ys: list[str]) -> bool:
        if self.colinfo is None:
            return False
        numeric = set(self.colinfo.get("numeric", []))
        return all(y in numeric for y in ys)

    # -----------------------------
    # Plot-Handler
    # -----------------------------
    def on_plot_clicked(self):
        ok, msg = self.validate_selection()
        if not ok:
            messagebox.showwarning("Auswahl prüfen", msg)
            return

        # Zeichenbereich vorbereiten
        self.ui.fig.clf()
        ptype = self.ui.plot_type.get()

        try:
            if ptype == "Polar":
                ax = self.ui.fig.add_subplot(111, projection="polar")
            else:
                ax = self.ui.fig.add_subplot(111)
            self._draw_plot(ax)
            self.ui.canvas.draw()
            self.plot_done = True
        except Exception as ex:
            messagebox.showerror("Plot-Fehler", str(ex))
            self.plot_done = False
            return

        # Plot-bezogene Statistik (nur Text)
        try:
            details_text = self.compute_plot_stats()
            self.ui.update_details(details_text)
        except Exception as ex:
            self.ui.update_details(f"Statistik konnte nicht berechnet werden: {ex}")

    def _draw_plot(self, ax):
        """Ruft die passende plotter-Funktion auf."""
        df = self.df
        assert df is not None

        ptype = self.ui.plot_type.get()
        x = self.get_selected_x()
        ys = self.get_selected_ys()

        if ptype == "Line":
            plot_line(ax, df, x, ys)
            self.ui.update_status(f"Line: X={x}; Y={', '.join(ys)}")

        elif ptype == "Stacked Area":
            plot_stacked_area(ax, df, x, ys)
            self.ui.update_status(f"Stacked Area: X={x}; Y={', '.join(ys)}")

        elif ptype == "Pie":
            plot_pie(ax, df, label_col=x, value_col=ys[0], top_n=8)
            self.ui.update_status(f"Pie: Labels={x}; Wert={ys[0]}")

        elif ptype == "Histogram":
            s = pd.to_numeric(df[ys[0]], errors="coerce")
            plot_hist(ax, s)  # 'auto' bins im Plotter
            self.ui.update_status(f"Histogram: Y={ys[0]}")

        elif ptype == "Polar":
            s = pd.to_numeric(df[ys[0]], errors="coerce")
            plot_polar(ax, s)
            self.ui.update_status(f"Polar: Y={ys[0]}")

    # -----------------------------
    # Statistik (nur Text)
    # -----------------------------
    def compute_plot_stats(self) -> str:
        """Erstellt einen Textblock mit Statistik für den aktuellen Plot."""
        assert self.df is not None
        ptype = self.ui.plot_type.get()
        x = self.get_selected_x()
        ys = self.get_selected_ys()
        df = self.df

        lines: list[str] = []

        if ptype in ("Line", "Stacked Area", "Histogram"):
            lines.append("PLOT-STATISTIK")
            for col in ys:
                s = pd.to_numeric(df[col], errors="coerce")
                desc = s.describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
                lines.append(f"[{col}]")
                lines.append(f"  count={int(desc.get('count', 0))}")
                lines.append(f"  mean={desc.get('mean', float('nan')):.3f}, std={desc.get('std', float('nan')):.3f}")
                lines.append(f"  min={desc.get('min', float('nan'))}, 25%={desc.get('25%')}, 50%={desc.get('50%')}, 75%={desc.get('75%')}, max={desc.get('max', float('nan'))}")
                lines.append("")

            if ptype == "Histogram":
                s = pd.to_numeric(df[ys[0]], errors="coerce")
                n_total = len(s)
                n_nan = s.isna().sum()
                s_clean = s.dropna()
                if not s_clean.empty:
                    vmin, vmax = float(s_clean.min()), float(s_clean.max())
                    lines.append(f"Histogram-Extras: Wertebereich=[{vmin}, {vmax}], NaN-Anteil={n_nan}/{n_total}")
                else:
                    lines.append("Histogram-Extras: keine gültigen Werte nach Cleaning.")

        elif ptype == "Pie":
            vals = pd.to_numeric(df[ys[0]], errors="coerce")
            lab = df[x].astype(str)
            mask = vals.notna() & (vals > 0)
            agg = vals[mask].groupby(lab[mask]).sum().sort_values(ascending=False)
            k = min(8, len(agg))
            lines.append("PIE-STATISTIK")
            lines.append(f"  Kategorien: {len(agg)}")
            lines.append(f"  Top-N: {k}")
            lines.append(f"  Gesamtsumme: {float(agg.sum()) if len(agg) else 0.0}")
            lines.append("  Top-N Kategorien (nach Summe):")
            for name, val in agg.head(k).items():
                lines.append(f"    {name}: {val}")
            if len(agg) > k:
                rest = float(agg.iloc[k:].sum())
                lines.append(f"    Andere: {rest}")

        elif ptype == "Polar":
            s = pd.to_numeric(df[ys[0]], errors="coerce").dropna()
            lines.append("POLAR-STATISTIK")
            lines.append(f"  Werte (Anzahl): {len(s)}")
            if len(s):
                lines.append(f"  Summe: {float(s.sum())}")
                lines.append(f"  Mittelwert: {float(s.mean())}")
            s_sorted = s.sort_values(ascending=False)
            lines.append("  Top-8 Werte:")
            for val in s_sorted.head(8).tolist():
                lines.append(f"    {val}")

        return "\n".join(lines).strip()

    # -----------------------------
    # PNG speichern
    # -----------------------------
    def on_save_png(self):
        if not self.plot_done:
            messagebox.showinfo("Hinweis", "Kein Plot zum Speichern. Bitte zuerst einen Plot erzeugen.")
            return
        base = "plot"
        if self.current_csv_path:
            base = os.path.splitext(os.path.basename(self.current_csv_path))[0] + "_plot"
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"{base}.png",
            filetypes=[("PNG-Bild", "*.png")]
        )
        if not path:
            return
        try:
            self.ui.fig.savefig(path, dpi=150, bbox_inches="tight")
            messagebox.showinfo("Gespeichert", f"PNG gespeichert: {os.path.basename(path)}")
        except Exception as ex:
            messagebox.showerror("Fehler beim Speichern", str(ex))


if __name__ == "__main__":
    root = tk.Tk()
    AppController(root)
    root.mainloop()
