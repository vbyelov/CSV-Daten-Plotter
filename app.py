# app.py
# Layout-Variante B: Grafik oben (100% Breite), Statistik unten.
# Ergänzt um explizite Achsenwahl: X (Combobox), Y (Listbox Mehrfachauswahl).
# Keine Toolbar über dem Plot.

import os
import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

try:
    import plotter
except Exception:
    plotter = None


def first_non_numeric_col(df: pd.DataFrame):
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None

def numeric_cols(df: pd.DataFrame):
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

def choose_columns(df: pd.DataFrame, plot_type: str, x_choice: str | None, y_choices: list[str] | None):
    """Nimmt Nutzerwahl, sonst Heuristik."""
    num = numeric_cols(df)
    non = first_non_numeric_col(df)

    # Nutzerwahl hat Vorrang
    if plot_type in ("Line", "Bar", "Stacked"):
        x = x_choice if x_choice in df.columns else (non if non is not None else None)
        y = [c for c in (y_choices or num) if c in df.columns]
        return {"x": x, "y_cols": y}

    if plot_type == "Pie":
        # Für Pie: ein Wertefeld + Labels (x)
        values = (y_choices[0] if y_choices else (num[0] if num else None))
        labels = x_choice if (x_choice in df.columns if x_choice else False) else (non if non is not None else None)
        return {"labels": labels, "values": values}

    if plot_type == "Polar":
        # Für Polar: r aus erster Y-Auswahl
        r = (y_choices[0] if y_choices else (num[0] if num else None))
        return {"r": r}

    # Fallback generisch
    return {"x": non, "y_cols": num}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV Daten Plotter")
        self.geometry("1100x750")

        self.current_folder = tk.StringVar(value="")
        self.current_file = None
        self.plot_type = tk.StringVar(value="Line")
        self.df = None

        # Nutzerwahl X/Y
        self.x_var = tk.StringVar(value="")
        self.y_listbox = None  # wird später erstellt

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)  # PanedWindow

        # Row 0: Ordnerwahl
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Ordner:").grid(row=0, column=0, padx=(0, 6))
        self.entry_folder = ttk.Entry(top, textvariable=self.current_folder)
        self.entry_folder.grid(row=0, column=1, sticky="ew")
        ttk.Button(top, text="Durchsuchen", command=self.choose_folder).grid(row=0, column=2, padx=(6, 0))

        # Row 1: Dateiliste
        files_frame = ttk.Frame(self)
        files_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(files_frame, columns=("name",), show="headings")
        self.tree.heading("name", text="Datei")
        self.tree.column("name", width=800, minwidth=200, stretch=True, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_file_select)
        yscroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(files_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        # Row 2: Plottyp + Buttons (in einer Zeile)
        controls = ttk.Frame(self)
        controls.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 2))
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

        # Row 3: Achsenwahl (X/Y)
        axes_frame = ttk.LabelFrame(self, text="Spaltenwahl")
        axes_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(2, 4))
        axes_frame.columnconfigure(1, weight=1)
        axes_frame.columnconfigure(3, weight=1)

        # X: Combobox
        ttk.Label(axes_frame, text="X:").grid(row=0, column=0, padx=(6, 6), pady=6, sticky="w")
        self.x_combo = ttk.Combobox(axes_frame, textvariable=self.x_var, state="readonly", values=[])
        self.x_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        # Y: Listbox (Mehrfachauswahl)
        ttk.Label(axes_frame, text="Y:").grid(row=0, column=2, padx=(6, 6), pady=6, sticky="w")
        y_frame = ttk.Frame(axes_frame)
        y_frame.grid(row=0, column=3, sticky="ew")
        y_frame.columnconfigure(0, weight=1)
        self.y_listbox = tk.Listbox(y_frame, selectmode="extended", height=4, exportselection=False)
        self.y_listbox.grid(row=0, column=0, sticky="ew")
        y_scroll = ttk.Scrollbar(y_frame, orient="vertical", command=self.y_listbox.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.y_listbox.configure(yscrollcommand=y_scroll.set)

        # Row 4: PanedWindow vertikal (Plot oben, Statistik unten)
        paned = ttk.Panedwindow(self, orient="vertical")
        paned.grid(row=4, column=0, sticky="nsew", padx=8, pady=(4, 8))

        top_plot = ttk.Frame(paned)
        top_plot.columnconfigure(0, weight=1)
        top_plot.rowconfigure(0, weight=1)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=top_plot)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        bottom_stats = ttk.LabelFrame(paned, text="Statistik")
        bottom_stats.rowconfigure(0, weight=1)
        bottom_stats.columnconfigure(0, weight=1)
        self.txt_stats = tk.Text(bottom_stats, height=8, wrap="word")
        self.txt_stats.grid(row=0, column=0, sticky="nsew", padx=(6,0), pady=6)
        stats_scroll = ttk.Scrollbar(bottom_stats, orient="vertical", command=self.txt_stats.yview)
        stats_scroll.grid(row=0, column=1, sticky="ns", padx=(0,6), pady=6)
        self.txt_stats.configure(yscrollcommand=stats_scroll.set)

        paned.add(top_plot, weight=3)
        paned.add(bottom_stats, weight=1)

    # --- Aktionen ---
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.current_folder.set(folder)
        self.fill_files()

    def fill_files(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        folder = self.current_folder.get()
        if not folder:
            return
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith(".csv"):
                self.tree.insert("", "end", values=(name,))

    def on_file_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0], "values")[0]
        self.current_file = os.path.join(self.current_folder.get(), name)
        self.df = pd.read_csv(self.current_file)

        # X/Y Optionen füllen
        cols = list(self.df.columns)
        self.x_combo["values"] = cols
        # Standard X
        non = first_non_numeric_col(self.df)
        if non:
            self.x_var.set(non)
        else:
            self.x_var.set("")  # optional leer lassen

        # Y-Liste
        self.y_listbox.delete(0, "end")
        num = numeric_cols(self.df)
        for c in cols:
            self.y_listbox.insert("end", c)
        # Standard Y: alle numerischen Spalten selektieren
        for i, c in enumerate(cols):
            if c in num:
                self.y_listbox.selection_set(i)

        self.btn_plot.config(state="normal")
        self.btn_png.config(state="normal")

    def _get_y_selection(self):
        sel_idx = self.y_listbox.curselection()
        return [self.y_listbox.get(i) for i in sel_idx]

    def plot(self):
        if self.df is None:
            return
        ptype = self.plot_type.get()
        x_choice = self.x_var.get().strip() or None
        y_choices = self._get_y_selection()
        cols = choose_columns(self.df, ptype, x_choice, y_choices)

        self.figure.clear()
        if ptype == "Polar":
            self.ax = self.figure.add_subplot(111, projection="polar")
        else:
            self.ax = self.figure.add_subplot(111)

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
                used_plotter = False

        if not used_plotter:
            self._simple_plot(ptype, cols)

        self.ax.set_title(f"{ptype} – {os.path.basename(self.current_file)}")
        self.canvas.draw()
        self.update_stats(ptype, cols)

    def _simple_plot(self, ptype: str, cols: dict):
        df = self.df
        if ptype in ("Line", "Bar", "Stacked"):
            x = cols.get("x")
            ycols = cols.get("y_cols", [])
            ycols = [c for c in ycols if c in df.columns]
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
