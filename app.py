# app.py
# Kurzer, gut lesbarer Einstiegspunkt für das GUI.
# Fokus: einfacher Flow 1) Ordner → 2) Datei → 3) Plottyp → 4) Plotten → 5) Grafik + kurze Statistik.
# Keine Sonderprüfungen, keine Statusleiste, keine Shortcuts. Radiobuttons HORIZONTAL in einer Zeile,
# rechts daneben "Plotten" und "Als PNG speichern".
# Dateiliste: nur Dateinamen (keine Größen-Spalte).

import os
import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

# Optional: lokales plotter-Modul (falls vorhanden).
try:
    import plotter  # erwartet Funktionen: plot_line / plot_bar / plot_pie / plot_polar / plot_stacked ODER plot(...)
except Exception:
    plotter = None


# --- Spaltenwahl (bewusst einfach) --------------------------------------------

def first_non_numeric_col(df: pd.DataFrame):
    """Erste nicht-numerische Spalte (für Kategorien/Achsenbeschriftung)."""
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None

def numeric_cols(df: pd.DataFrame):
    """Alle numerischen Spalten als Liste (für y-Werte)."""
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

def choose_columns(df: pd.DataFrame, plot_type: str):
    """
    Heuristik:
    - Line/Bar/Stacked: x = erste nicht-numerische Spalte oder Index; y = alle numerischen Spalten
    - Pie: labels = erste nicht-numerische oder Index; values = erste numerische
    - Polar: r = erste numerische; theta = gleichmäßig (wird im plotter erzeugt)
    """
    num = numeric_cols(df)
    non = first_non_numeric_col(df)

    if plot_type in ("Line", "Bar", "Stacked"):
        x = non if non is not None else None
        y = num
        return {"x": x, "y_cols": y}

    if plot_type == "Pie":
        values = num[0] if num else None
        labels = non if non is not None else None
        return {"labels": labels, "values": values}

    if plot_type == "Polar":
        r = num[0] if num else None
        return {"r": r}

    # Fallback generisch
    return {"x": non, "y_cols": num}


# --- GUI ----------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Daten Plotter")
        self.geometry("1000x700")

        # Zustand
        self.current_folder = tk.StringVar(value="")
        self.current_file = None
        self.plot_type = tk.StringVar(value="Line")
        self.df = None

        # Layout: Grundraster
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)   # Dateiliste wächst
        self.rowconfigure(3, weight=1)   # PanedWindow wächst

        # Zeile 0: Ordnerwahl
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Ordner:").grid(row=0, column=0, padx=(0, 6))
        self.entry_folder = ttk.Entry(top, textvariable=self.current_folder)
        self.entry_folder.grid(row=0, column=1, sticky="ew")
        ttk.Button(top, text="Durchsuchen", command=self.choose_folder).grid(row=0, column=2, padx=(6, 0))

        # Zeile 1: Dateiliste (nur Dateinamen) + Scrollbars
        files_frame = ttk.Frame(self)
        files_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(files_frame, columns=("name",), show="headings")
        self.tree.heading("name", text="Datei")
        # Spalte darf über die gesamte Breite wachsen
        self.tree.column("name", width=800, minwidth=200, stretch=True, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_file_select)

        yscroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(files_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        # Zeile 2: EIN REIHENLAYOUT
        # Links: Label "Plottyp:" + Radiobuttons HORIZONTAL
        # Rechts: Buttons [Plotten] [Als PNG speichern]
        controls = ttk.Frame(self)
        controls.grid(row=2, column=0, sticky="ew", padx=8, pady=4)
        # Zwei große Bereiche: 0 (Radios) wächst, 1 (Buttons) bleibt kompakt
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=0)

        radios_row = ttk.Frame(controls)
        radios_row.grid(row=0, column=0, sticky="w")

        ttk.Label(radios_row, text="Plottyp:").grid(row=0, column=0, padx=(0, 8), sticky="w")

        radio_names = ("Line", "Bar", "Pie", "Polar", "Stacked")
        for col, name in enumerate(radio_names, start=1):
            ttk.Radiobutton(radios_row, text=name, value=name, variable=self.plot_type)\
                .grid(row=0, column=col, padx=(0, 10), sticky="w")

        buttons_row = ttk.Frame(controls)
        buttons_row.grid(row=0, column=1, sticky="e")
        self.btn_plot = ttk.Button(buttons_row, text="Plotten", command=self.plot, state="disabled")
        self.btn_png = ttk.Button(buttons_row, text="Als PNG speichern", command=self.save_png, state="disabled")
        self.btn_plot.grid(row=0, column=0, padx=4)
        self.btn_png.grid(row=0, column=1, padx=4)

        # Zeile 3: PanedWindow (links Canvas, rechts Statistik)
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.grid(row=3, column=0, sticky="nsew", padx=8, pady=(4, 8))

        # Links: Matplotlib
        left = ttk.Frame(paned)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)  # Standard-Achse (wird bei Polar ersetzt)
        self.canvas = FigureCanvasTkAgg(self.figure, master=left)
        toolbar = NavigationToolbar2Tk(self.canvas, left, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=0, column=0, sticky="w", pady=(4, 0))
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

        # Rechts: Statistik (kurzes Textfeld)
        right = ttk.LabelFrame(paned, text="Statistik")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.txt_stats = tk.Text(right, height=10, wrap="word")
        self.txt_stats.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        paned.add(left, weight=3)
        paned.add(right, weight=2)

    # --- Aktionen --------------------------------------------------------------

    def choose_folder(self):
        """Ordnerdialog öffnen und Dateiliste auffüllen (nur *.csv)."""
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.current_folder.set(folder)
        self.fill_files()

    def fill_files(self):
        """Dateiliste neu befüllen (CSV im Ordner)."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        folder = self.current_folder.get()
        if not folder:
            return
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith(".csv"):
                self.tree.insert("", "end", values=(name,))

    def on_file_select(self, _event=None):
        """Ausgewählte Datei merken, CSV laden und Buttons aktivieren."""
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "values")[0]
        self.current_file = os.path.join(self.current_folder.get(), name)
        self.df = pd.read_csv(self.current_file)
        self.btn_plot.config(state="normal")
        self.btn_png.config(state="normal")

    def plot(self):
        """Plot zeichnen (plotter.* nutzen, sonst einfacher Fallback)."""
        if self.df is None:
            return

        ptype = self.plot_type.get()
        cols = choose_columns(self.df, ptype)

        # Figure für jeden Plot frisch vorbereiten (Polar/Normal wechseln)
        self.figure.clear()
        if ptype == "Polar":
            self.ax = self.figure.add_subplot(111, projection="polar")
        else:
            self.ax = self.figure.add_subplot(111)

        # plotter-Modul bevorzugt aufrufen
        used_plotter = False
        if plotter is not None:
            func_map = {
                "Line": "plot_line",
                "Bar": "plot_bar",
                "Pie": "plot_pie",
                "Polar": "plot_polar",
                "Stacked": "plot_stacked",
            }
            func_name = func_map.get(ptype)
            try:
                if func_name and hasattr(plotter, func_name):
                    getattr(plotter, func_name)(self.ax, self.df, **cols)
                    used_plotter = True
                elif hasattr(plotter, "plot"):
                    plotter.plot(self.ax, self.df, ptype, **cols)
                    used_plotter = True
            except Exception:
                used_plotter = False  # Vorgabe: keine Meldungen/Prüfungen

        # Fallback: sehr einfacher Plot
        if not used_plotter:
            self._simple_plot(ptype, cols)

        self.ax.set_title(f"{ptype} – {os.path.basename(self.current_file)}")
        self.canvas.draw()
        self.update_stats(ptype, cols)

    def _simple_plot(self, ptype: str, cols: dict):
        """Minimaler Fallback-Plot, falls plotter.py nicht greift."""
        df = self.df
        if ptype in ("Line", "Bar", "Stacked"):
            x = cols.get("x")
            ycols = cols.get("y_cols", [])
            data = df.set_index(x) if (x in df.columns if x is not None else False) else df
            if ptype == "Bar":
                data[ycols].plot(kind="bar", ax=self.ax)
            elif ptype == "Stacked":
                data[ycols].plot(kind="area", stacked=True, ax=self.ax)
            else:
                data[ycols].plot(ax=self.ax)
            self.ax.legend(loc="best")
        elif ptype == "Pie":
            labels = cols.get("labels")
            values = cols.get("values")
            series = df[values] if (values in df.columns if values is not None else False) else None
            lbls = df[labels] if (labels in df.columns if labels is not None else False) else df.index
            if series is not None:
                self.ax.pie(series, labels=lbls, autopct="%1.1f%%")
        elif ptype == "Polar":
            rcol = cols.get("r")
            r = df[rcol].to_numpy() if (rcol in df.columns if rcol is not None else False) else np.ones(len(df))
            theta = np.linspace(0, 2*np.pi, len(r), endpoint=False)
            self.ax.plot(theta, r)
        else:
            df.plot(ax=self.ax)

    def update_stats(self, ptype: str, cols: dict):
        """Kurze Statistik rechts anzeigen."""
        self.txt_stats.delete("1.0", "end")
        df = self.df
        num = numeric_cols(df)

        lines = []
        lines.append(f"Datei: {os.path.basename(self.current_file)}")
        lines.append(f"Zeilen × Spalten: {df.shape[0]} × {df.shape[1]}")
        lines.append(f"Plottyp: {ptype}")
        if "x" in cols and cols["x"]:
            lines.append(f"X: {cols['x']}")
        if "y_cols" in cols and cols["y_cols"]:
            lines.append(f"Y: {', '.join(cols['y_cols'][:5])}" + (" ..." if len(cols['y_cols']) > 5 else ""))
        if "labels" in cols and cols["labels"]:
            lines.append(f"Labels: {cols['labels']}")
        if "values" in cols and cols["values"]:
            lines.append(f"Werte: {cols['values']}")
        if "r" in cols and cols["r"]:
            lines.append(f"R (Polar): {cols['r']}")

        for c in num[:2]:
            s = df[c].dropna()
            lines.append(f"\n[{c}]  min={s.min():.3g}  max={s.max():.3g}  mean={s.mean():.3g}")

        self.txt_stats.insert("1.0", "\n".join(lines))

    def save_png(self):
        """Aktuelle Figur als PNG speichern."""
        if self.df is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile="plot.png"
        )
        if not path:
            return
        self.figure.savefig(path, bbox_inches="tight", dpi=150)


if __name__ == "__main__":
    App().mainloop()
