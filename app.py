# app.py
# Einstiegspunkt der Anwendung.
# Verbindet die GUI (ui_main.py) mit den Datenfunktionen (data_loader.py) und dem Plotter.

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui_main import MainUI
from data_loader import list_csv_files, load_csv, infer_columns
from plotter import make_plot


class AppController:
    """
    Steuert die App-Logik:
    - Ordner wählen und CSV-Liste anzeigen
    - CSV laden, Spalten analysieren
    - Plot erzeugen (inkl. Mehrfachauswahl Y)
    - Plot im GUI anzeigen und als PNG speichern
    """
    def __init__(self, root: tk.Tk):
        self.root = root

        # GUI aufbauen
        self.ui = MainUI(root)

        # interner Zustand
        self.current_folder = None
        self.current_filename = None
        self.df = None
        self.colinfo = None

        # Plot/Canvas
        self.current_figure = None
        self.canvas = None

        # Aktionen verbinden
        self.ui.btn_choose_folder.configure(command=self.on_choose_folder)
        self.ui.btn_load_file.configure(command=self.on_load_file)
        self.ui.btn_plot.configure(state="disabled", command=self.on_plot)
        self.ui.btn_save_png.configure(command=self.on_save_png)

        # Doppelklick: Datei laden
        self.ui.listbox_files.bind("<Double-Button-1>", self.on_double_click_file)

    # ------------------------------
    # Event-Handler
    # ------------------------------

    def on_choose_folder(self):
        """Ordner wählen und CSV-Dateiliste füllen."""
        folder = filedialog.askdirectory(title="Ordner mit CSV-Dateien wählen")
        if not folder:
            return

        self.current_folder = folder
        self.refresh_file_list()

        # Zustand zurücksetzen
        self.df = None
        self.colinfo = None
        self.ui.cmb_x.set("X-Spalte")
        self.ui.cmb_x.configure(values=[])
        self._fill_y_list([])
        self.ui.btn_plot.configure(state="disabled")

        # Plotbereich leeren
        self._clear_plot_area()

        # Titel aktualisieren
        self.root.title(f"CSV Daten Plotter — {self.current_folder}")

    def refresh_file_list(self):
        """CSV-Dateien im gewählten Ordner anzeigen."""
        self.ui.listbox_files.delete(0, tk.END)
        if not self.current_folder:
            return

        files = list_csv_files(self.current_folder)
        if not files:
            messagebox.showinfo("Info", "Keine CSV-Dateien im Ordner gefunden.")
            return

        for name in files:
            self.ui.listbox_files.insert(tk.END, name)

    def on_double_click_file(self, event):
        """Bei Doppelklick die Datei laden."""
        self.on_load_file()

    def on_load_file(self):
        """CSV laden, Spalten erkennen und Auswahlfelder füllen."""
        if not self.current_folder:
            messagebox.showwarning("Hinweis", "Bitte zuerst einen Ordner wählen.")
            return

        selection = self.ui.listbox_files.curselection()
        if not selection:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine CSV-Datei in der Liste auswählen.")
            return

        filename = self.ui.listbox_files.get(selection[0])
        full_path = os.path.join(self.current_folder, filename)

        # CSV laden
        try:
            df, used_enc = load_csv(full_path, sep=None)
        except ValueError as e:
            messagebox.showerror("Fehler beim Laden", str(e))
            return

        # Spaltentypen erkennen
        colinfo = infer_columns(df)

        # X-Kandidaten (alle Spalten)
        all_cols = df.columns.tolist()
        self.ui.cmb_x.configure(values=all_cols)
        self.ui.cmb_x.set("X-Spalte")

        # Y-Kandidaten (numerische Spalten)
        numeric_cols = colinfo.get("numeric", [])
        self._fill_y_list(numeric_cols)

        # Zustand speichern
        self.current_filename = filename
        self.df = df
        self.colinfo = colinfo

        # Plot möglich
        self.ui.btn_plot.configure(state="normal")

        # Plotbereich leeren
        self._clear_plot_area()

        # Feedback
        messagebox.showinfo(
            "Geladen",
            (
                f"Datei geladen: {filename}\n"
                f"Encoding: {used_enc}\n"
                f"Spalten gesamt: {len(all_cols)}\n"
                f"Numerisch: {len(colinfo.get('numeric', []))}, "
                f"Datum: {len(colinfo.get('datetime', []))}, "
                f"Kategorisch: {len(colinfo.get('categorical', []))}"
            )
        )

    def on_plot(self):
        """Plot entsprechend der Auswahl erstellen und anzeigen."""
        if self.df is None:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine CSV-Datei laden.")
            return

        plot_type = (self.ui.cmb_plot_type.get() or "").strip()
        if not plot_type:
            messagebox.showwarning("Hinweis", "Bitte zuerst einen Plottyp wählen.")
            return

        x_col = self.ui.cmb_x.get()
        if x_col == "X-Spalte":
            x_col = None

        y_cols = self._get_selected_y_cols()

        try:
            # Line / Histogram / Stacked Area nutzen y_cols (1..n)
            if plot_type == "Line":
                if not x_col or not y_cols:
                    raise ValueError("Für Line bitte X-Spalte und mindestens eine Y-Spalte wählen.")
                fig = make_plot("Line", self.df, x_col=x_col, y_cols=y_cols, title=self.current_filename)

            elif plot_type == "Histogram":
                if not y_cols:
                    raise ValueError("Für Histogramm bitte mindestens eine numerische Spalte wählen.")
                fig = make_plot("Histogram", self.df, y_cols=y_cols, title=self.current_filename)

            elif plot_type == "Stacked Area":
                if not x_col or len(y_cols) < 2:
                    raise ValueError("Für Stacked Area bitte X-Spalte und mindestens zwei Y-Spalten wählen.")
                fig = make_plot("Stacked Area", self.df, x_col=x_col, y_cols=y_cols, title=self.current_filename)

            # Pie / Polar erwarten Kategorie (X) + einen Wert (Y)
            elif plot_type == "Pie":
                if not x_col or len(y_cols) != 1:
                    raise ValueError("Für Pie bitte X=Kategorie und genau eine Y-Spalte wählen.")
                fig = make_plot("Pie", self.df, category_col=x_col, value_col=y_cols[0], title=self.current_filename)

            elif plot_type == "Polar":
                if not x_col or len(y_cols) != 1:
                    raise ValueError("Für Polar bitte X=Kategorie und genau eine Y-Spalte wählen.")
                fig = make_plot("Polar", self.df, category_col=x_col, value_col=y_cols[0], title=self.current_filename)

            else:
                raise ValueError(f"Unbekannter Plot-Typ: {plot_type}")

        except ValueError as e:
            messagebox.showerror("Plot-Fehler", str(e))
            return
        except Exception as e:
            messagebox.showerror("Unerwarteter Fehler", f"{type(e).__name__}: {e}")
            return

        self._render_figure(fig)

    def on_save_png(self):
        """Aktuellen Plot als PNG speichern."""
        if self.current_figure is None:
            messagebox.showwarning("Hinweis", "Es gibt keinen Plot zum Speichern.")
            return

        initial = "plot.png"
        if self.current_filename:
            base, _ = os.path.splitext(self.current_filename)
            initial = f"{base}.png"

        path = filedialog.asksaveasfilename(
            title="Plot als PNG speichern",
            defaultextension=".png",
            initialfile=initial,
            filetypes=[("PNG-Datei", "*.png")]
        )
        if not path:
            return

        try:
            self.current_figure.savefig(path, dpi=150, bbox_inches="tight")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"{type(e).__name__}: {e}")
            return

        messagebox.showinfo("Gespeichert", f"Plot gespeichert:\n{path}")

    # ------------------------------
    # Hilfsfunktionen (intern)
    # ------------------------------

    def _fill_y_list(self, cols):
        """Listbox der Y-Spalten befüllen (Mehrfachauswahl möglich)."""
        self.ui.lst_y.delete(0, tk.END)
        for c in cols:
            self.ui.lst_y.insert(tk.END, c)

    def _get_selected_y_cols(self):
        """Ausgewählte Y-Spalten aus der Listbox lesen."""
        idxs = self.ui.lst_y.curselection()
        return [self.ui.lst_y.get(i) for i in idxs]

    def _render_figure(self, fig):
        """Figure im unteren Bereich anzeigen (vorherige Inhalte ersetzen)."""
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if self.ui.lbl_placeholder.winfo_exists():
            self.ui.lbl_placeholder.pack_forget()

        self.current_figure = fig
        self.canvas = FigureCanvasTkAgg(fig, master=self.ui.frame_plot)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _clear_plot_area(self):
        """Plot-Bereich leeren und Platzhalter anzeigen."""
        self.current_figure = None
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if self.ui.lbl_placeholder.winfo_exists():
            self.ui.lbl_placeholder.pack_forget()
            self.ui.lbl_placeholder.pack(expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = AppController(root)
    root.mainloop()


#test with other csv