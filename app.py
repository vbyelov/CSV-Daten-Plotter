# app.py
# Einfache, robuste App-Logik für CSV-Daten-Plotter.
# Kommentare bewusst einfach auf Deutsch.

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import plotter  # unser Modul mit draw(plot_type, ax, df, x_col, y_cols)

# Optionales Hilfsmodul zum Laden/Erkennen (falls vorhanden)
try:
    import data_loader
except Exception:
    data_loader = None

# Optionales UI-Modul (bereitgestellt von dir)
try:
    import ui_main
except Exception:
    ui_main = None


# ---------- Kleine Hilfsfunktionen ----------

def _get_attr(obj, candidates, default=None):
    """Sucht das erste existierende Attribut in 'candidates'."""
    for name in candidates:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default

def _safe_set_text(widget, text):
    """
    Schreibt Text in ein Text-Widget oder Label, falls vorhanden.
    Wenn nichts passt, macht nichts.
    """
    if widget is None:
        return
    try:
        # Text-Widget
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.config(state="disabled")
    except Exception:
        try:
            # Label-ähnlich (hat 'configure' mit 'text')
            widget.configure(text=text)
        except Exception:
            pass


# ---------- Hauptklasse der Anwendung ----------

class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Daten Plotter")

        # 1) UI vom ui_main beziehen (flexibel: Funktion build(...) oder Klasse MainUI)
        self.ui = None
        if ui_main is not None:
            # Versuche unterschiedliche Initialisierungen
            if hasattr(ui_main, "build"):
                # Erwartet: def build(root) -> ui-objekt
                self.ui = ui_main.build(root)
            elif hasattr(ui_main, "MainUI"):
                self.ui = ui_main.MainUI(root)
            elif hasattr(ui_main, "create_ui"):
                self.ui = ui_main.create_ui(root)

        # Falls kein ui_main vorhanden oder fehlgeschlagen: baue sehr einfache Notfall-UI
        if self.ui is None:
            self.ui = self._build_fallback_ui(root)

        # 2) Zentrale UI-Elemente für die Integration finden
        self.plot_container = _get_attr(self.ui, ["plot_frame", "canvas_frame", "plot_area", "plot_container"])
        self.btn_browse = _get_attr(self.ui, ["btn_browse_folder", "btn_folder", "button_browse"])
        self.list_files = _get_attr(self.ui, ["list_files", "files_list", "lb_files"])
        self.list_x = _get_attr(self.ui, ["list_x", "x_list", "lb_x"])
        self.list_y = _get_attr(self.ui, ["list_y", "y_list", "lb_y"])
        self.btn_plot = _get_attr(self.ui, ["btn_plot", "button_plot"])
        self.btn_save = _get_attr(self.ui, ["btn_save_png", "button_save"])
        self.status = _get_attr(self.ui, ["lbl_status", "status_label"])
        self.stats_box = _get_attr(self.ui, ["stats_text", "txt_stats", "stats_label"])

        # StringVar für Plot-Typ (von Radio-Buttons im ui_main gesetzt)
        self.plot_type_var = _get_attr(self.ui, ["plot_type_var", "plot_type"], None)
        if self.plot_type_var is None:
            # Fallback: eigene Variable mit Default "line"
            self.plot_type_var = tk.StringVar(value="line")

        # 3) Matplotlib-Figur einmalig initialisieren
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Canvas einhängen
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 4) Zustand
        self.current_folder = ""
        self.current_path = ""
        self.df = None
        self.columns_info = {"numeric": [], "categorical": [], "datetime": []}

        # 5) Events/Callbacks verbinden
        if self.btn_browse is not None:
            self.btn_browse.configure(command=self.on_browse_folder)
        if self.list_files is not None:
            self.list_files.bind("<<ListboxSelect>>", self.on_file_selected)
        if self.btn_plot is not None:
            self.btn_plot.configure(command=self.on_plot_clicked)
        if self.btn_save is not None:
            self.btn_save.configure(command=self.on_save_png)

        # Falls Radio-Buttons bereits existieren und Variable ändert sich -> neu plotten (optional)
        try:
            self.plot_type_var.trace_add("write", lambda *_: None)  # wir plotten erst beim Klick
        except Exception:
            pass

        _safe_set_text(self.status, "Bereit. Wähle einen Ordner mit CSV-Dateien.")

    # ---------- Fallback-UI (nur wenn ui_main fehlt) ----------

    def _build_fallback_ui(self, root):
        """
        Baut eine sehr einfache Oberfläche, nur für den Notfall.
        In deinem Projekt wird ui_main.py verwendet.
        """
        frame = ttk.Frame(root)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        top = ttk.Frame(frame)
        top.pack(fill="x")
        btn_browse = ttk.Button(top, text="Ordner wählen")
        btn_browse.pack(side="left")
        btn_plot = ttk.Button(top, text="Plotten")
        btn_plot.pack(side="left", padx=6)
        btn_save = ttk.Button(top, text="Als PNG speichern")
        btn_save.pack(side="left")

        mid = ttk.Frame(frame)
        mid.pack(fill="both", expand=True, pady=6)

        # Links: Datei- und Spaltenlisten
        side = ttk.Frame(mid)
        side.pack(side="left", fill="y")
        ttk.Label(side, text="Dateien").pack(anchor="w")
        list_files = tk.Listbox(side, height=8)
        list_files.pack(fill="y", pady=2)

        ttk.Label(side, text="X-Spalte").pack(anchor="w", pady=(8, 0))
        list_x = tk.Listbox(side, height=6, exportselection=False)
        list_x.pack(fill="y", pady=2)

        ttk.Label(side, text="Y-Spalten (Mehrfach)").pack(anchor="w", pady=(8, 0))
        list_y = tk.Listbox(side, height=8, selectmode="extended", exportselection=False)
        list_y.pack(fill="both", pady=2)

        # Mitte: Plotbereich
        plot_frame = ttk.Frame(mid)
        plot_frame.pack(side="left", fill="both", expand=True, padx=8)

        # Rechts: Plot-Typ + Statistik
        right = ttk.Frame(mid)
        right.pack(side="left", fill="y")

        ttk.Label(right, text="Plot-Typ").pack(anchor="w")
        plot_type_var = tk.StringVar(value="line")
        for key, text in [("line", "Line"), ("pie", "Pie"), ("hist", "Histogram"),
                          ("stacked", "Stacked Area"), ("polar", "Polar")]:
            ttk.Radiobutton(right, text=text, value=key, variable=plot_type_var).pack(anchor="w")

        ttk.Label(right, text="Statistik").pack(anchor="w", pady=(8, 0))
        stats_text = tk.Text(right, height=18, width=32, state="disabled")
        stats_text.pack(fill="y")

        status_label = ttk.Label(frame, text="")
        status_label.pack(fill="x", pady=(6, 0))

        # Rückgabe: Dummy-Objekt mit Attributen
        class UIObj:
            pass

        ui = UIObj()
        ui.plot_frame = plot_frame
        ui.btn_browse_folder = btn_browse
        ui.list_files = list_files
        ui.list_x = list_x
        ui.list_y = list_y
        ui.btn_plot = btn_plot
        ui.btn_save_png = btn_save
        ui.plot_type_var = plot_type_var
        ui.stats_text = stats_text
        ui.lbl_status = status_label
        return ui

    # ---------- Datei/Ordner-Handling ----------

    def on_browse_folder(self):
        """Ordner wählen und Dateiliste aktualisieren."""
        folder = filedialog.askdirectory(title="Ordner mit CSV-Dateien auswählen")
        if not folder:
            return
        self.current_folder = folder
        self._fill_file_list()
        _safe_set_text(self.status, f"Ordner gewählt: {folder}")

    def _fill_file_list(self):
        """Listet CSV-Dateien im aktuellen Ordner auf."""
        if self.list_files is None:
            return
        self.list_files.delete(0, "end")
        if not self.current_folder:
            return
        for name in os.listdir(self.current_folder):
            if name.lower().endswith(".csv"):
                self.list_files.insert("end", name)

    def on_file_selected(self, event=None):
        """Beim Klick auf eine Datei wird CSV geladen."""
        sel = None
        try:
            idxs = self.list_files.curselection()
            if idxs:
                sel = self.list_files.get(idxs[0])
        except Exception:
            pass
        if not sel:
            return
        path = os.path.join(self.current_folder, sel)
        self._load_csv(path)

    def _load_csv(self, path):
        """Lädt CSV in DataFrame und aktualisiert X/Y-Listen + Basisstatistik."""
        try:
            if data_loader is not None and hasattr(data_loader, "read_csv"):
                df = data_loader.read_csv(path)
            else:
                # Einfache Variante: automatische Trennzeichen-Erkennung (sep=None erfordert engine="python")
                df = pd.read_csv(path, encoding="utf-8", sep=None, engine="python")
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))
            return

        self.df = df
        self.current_path = path

        # Spaltentypen grob erkennen (entweder über data_loader oder einfach per pandas)
        if data_loader is not None and hasattr(data_loader, "infer_columns"):
            info = data_loader.infer_columns(df)
            # Sicherstellen, dass Keys existieren
            self.columns_info = {
                "numeric": info.get("numeric", []),
                "categorical": info.get("categorical", []),
                "datetime": info.get("datetime", []),
            }
        else:
            numeric = df.select_dtypes(include=["number"]).columns.tolist()
            categorical = [c for c in df.columns if c not in numeric]
            self.columns_info = {"numeric": numeric, "categorical": categorical, "datetime": []}

        # Listen X/Y füllen
        self._fill_xy_lists()

        # Basisstatistik anzeigen
        self._show_basic_stats()

        _safe_set_text(self.status, f"Geladen: {os.path.basename(path)} ({len(df)} Zeilen)")

    def _fill_xy_lists(self):
        """Füllt die Listboxen für X und Y."""
        if self.list_x is not None:
            self.list_x.delete(0, "end")
            for c in self.df.columns:
                self.list_x.insert("end", c)
            # Optional: Standardauswahl X = erste Spalte
            if self.df.columns.tolist():
                self.list_x.selection_clear(0, "end")
                self.list_x.selection_set(0)

        if self.list_y is not None:
            self.list_y.delete(0, "end")
            for c in self.columns_info.get("numeric", []):
                self.list_y.insert("end", c)

    # ---------- Plot + Statistik ----------

    def on_plot_clicked(self):
        """Validiert Auswahl und zeichnet das Diagramm."""
        if self.df is None:
            messagebox.showinfo("Info", "Bitte zuerst eine CSV-Datei laden.")
            return

        x_col = self._get_selected_x()
        y_cols = self._get_selected_y()

        if not x_col:
            messagebox.showwarning("Warnung", "Bitte eine X-Spalte auswählen.")
            return
        if not y_cols:
            messagebox.showwarning("Warnung", "Bitte mind. eine Y-Spalte auswählen.")
            return

        ptype = self.plot_type_var.get()

        # Einfache Validierungen je Plot-Typ
        if ptype in ("pie", "polar") and len(y_cols) != 1:
            messagebox.showwarning("Warnung", "Für Pie/Polar bitte genau eine Y-Spalte auswählen.")
            return
        if ptype == "stacked" and len(y_cols) < 2:
            messagebox.showwarning("Warnung", "Für Stacked Area mind. zwei Y-Spalten auswählen.")
            return

        # Y-Spalten numerisch erzwingen (nicht-darstellbare Werte werden NaN)
        for c in y_cols:
            try:
                self.df[c] = pd.to_numeric(self.df[c], errors="coerce")
            except Exception:
                pass

        try:
            plotter.draw(ptype, self.ax, self.df, x_col, y_cols)
            self.canvas.draw_idle()
        except Exception as e:
            messagebox.showerror("Fehler beim Plotten", str(e))
            return

        # Plot-bezogene Statistik anzeigen
        self._show_plot_stats(ptype, x_col, y_cols)

        _safe_set_text(self.status, f"Gezeichnet: {ptype} (X={x_col}, Y={', '.join(y_cols)})")

    def _get_selected_x(self):
        """Liest die Auswahl aus der X-Listbox."""
        if self.list_x is None:
            return ""
        try:
            idxs = self.list_x.curselection()
            if not idxs:
                return ""
            return self.list_x.get(idxs[0])
        except Exception:
            return ""

    def _get_selected_y(self):
        """Liest Mehrfachauswahl aus der Y-Listbox."""
        res = []
        if self.list_y is None:
            return res
        try:
            for i in self.list_y.curselection():
                res.append(self.list_y.get(i))
        except Exception:
            pass
        return res

    def _show_basic_stats(self):
        """Basisstatistik nach dem Laden der CSV."""
        if self.df is None:
            return
        rows, cols = self.df.shape
        num_n = len(self.columns_info.get("numeric", []))
        cat_n = len(self.columns_info.get("categorical", []))

        txt = []
        txt.append("Basisstatistik (nach dem Laden)")
        txt.append(f"- Zeilen: {rows}")
        txt.append(f"- Spalten: {cols}")
        txt.append(f"- Numerische Spalten: {num_n}")
        txt.append(f"- Kategorische Spalten: {cat_n}")
        _safe_set_text(self.stats_box, "\n".join(txt))

    def _show_plot_stats(self, ptype, x_col, y_cols):
        """Plot-bezogene Statistik gemäß TZ v1.1."""
        if self.df is None:
            return

        lines = []
        if ptype in ("line", "stacked", "hist"):
            lines.append("Plot-Statistik (Line/Stacked/Histogram)")
            for y in y_cols:
                s = pd.to_numeric(self.df[y], errors="coerce")
                lines.append(f"\nSpalte: {y}")
                lines.append(f"  count = {int(s.count())}")
                lines.append(f"  mean  = {round(float(s.mean()), 4) if s.count() else 'NA'}")
                lines.append(f"  std   = {round(float(s.std()), 4) if s.count() > 1 else 'NA'}")
                lines.append(f"  min   = {round(float(s.min()), 4) if s.count() else 'NA'}")
                lines.append(f"  max   = {round(float(s.max()), 4) if s.count() else 'NA'}")
                if ptype == "hist":
                    lines.append(f"  median= {round(float(s.median()), 4) if s.count() else 'NA'}")

        elif ptype in ("pie", "polar"):
            # Aggregation (Summe) pro Kategorie, Top-5, Gesamtsumme, Anzahl Kategorien
            y = y_cols[0]
            try:
                s = pd.to_numeric(self.df[y], errors="coerce")
            except Exception:
                s = self.df[y]
            grp = self.df.groupby(x_col)[y].sum(numeric_only=True)
            grp = grp.sort_values(ascending=False)

            total = float(pd.to_numeric(grp, errors="coerce").sum())
            ncat = int(len(grp.index))

            lines.append("Plot-Statistik (Pie/Polar)")
            lines.append(f"- Anzahl Kategorien: {ncat}")
            lines.append(f"- Gesamtsumme: {round(total, 4)}")

            top5 = grp.head(5)
            lines.append("- Top-5 Kategorien (Summe):")
            for k, v in top5.items():
                try:
                    v = round(float(v), 4)
                except Exception:
                    pass
                lines.append(f"  • {k}: {v}")

        _safe_set_text(self.stats_box, "\n".join(lines))

    # ---------- PNG speichern ----------

    def on_save_png(self):
        """Speichert den aktuellen Plot als PNG."""
        if self.df is None:
            messagebox.showinfo("Info", "Bitte zuerst eine CSV laden und plotten.")
            return
        # Dateiname aus Quell-CSV ableiten
        base = "plot"
        if self.current_path:
            base = os.path.splitext(os.path.basename(self.current_path))[0] + "_plot"

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=base + ".png",
            filetypes=[("PNG", "*.png"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        try:
            self.fig.savefig(path)
            _safe_set_text(self.status, f"Gespeichert: {path}")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))


# ---------- Start ----------

def main():
    root = tk.Tk()
    # Tk-Styles optional
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass

    app = Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
