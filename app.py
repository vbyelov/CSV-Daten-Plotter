import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

# Externe Module aus dem Projekt
import data_loader
import plotter

# UI-Baustein (Radiobuttons statt Combobox)
from ui_main import UIMain

# Matplotlib-Einbettung
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class App(tk.Tk):
    """
    Hauptanwendung für den CSV-Daten-Plotter.

    Änderungen ggü. früherer Version:
    - Diagrammtyp wird über Radiobuttons in UIMain gewählt.
    - app.py reagiert über einfache Callback-Methoden.
    - Klarer, anfängerfreundlicher Code mit deutschen Kommentaren.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("CSV-Daten-Plotter")
        self.geometry("1000x700")  # Fenstergröße kann bei Bedarf angepasst werden

        # ---- Zustandsvariablen --------------------------------------------------
        self.current_df = None  # Geladene Daten (pandas.DataFrame)
        self.current_chart_type: str = "line"  # Default wie im UI
        self.selected_x: Optional[str] = None
        self.selected_y: Optional[str] = None

        # ---- Layout: oben Steuerung, unten Plot --------------------------------
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # UI (Steuerbereich) – Callbacks werden direkt an Methoden delegiert
        self.ui = UIMain(
            self,
            on_open_csv=self._on_open_csv,
            on_chart_type_changed=self._on_chart_type_changed,
            on_x_changed=self._on_x_changed,
            on_y_changed=self._on_y_changed,
            on_plot_clicked=self._on_plot_clicked,
        )
        self.ui.grid(row=0, column=0, sticky="ew")

        # Plot-Bereich (Matplotlib)
        self._build_plot_area()

        # Anfangszustand der Felder konsistent setzen
        self._update_field_states()

    # ---------------------------------------------------------------------
    # Plot-Bereich (Matplotlib) aufbauen
    # ---------------------------------------------------------------------
    def _build_plot_area(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Figur + Achse
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Vorschau")

        # Canvas in Tk einbetten
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        widget = self.canvas.get_tk_widget()
        widget.grid(row=0, column=0, sticky="nsew")

    # ---------------------------------------------------------------------
    # Callbacks aus der UI
    # ---------------------------------------------------------------------
    def _on_open_csv(self) -> None:
        """CSV-Datei wählen, laden und Spalten in die UI übernehmen."""
        path = filedialog.askopenfilename(
            title="CSV-Datei wählen",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return

        # Pfad im Eingabefeld anzeigen
        try:
            self.ui.ent_path.delete(0, tk.END)
            self.ui.ent_path.insert(0, path)
        except Exception:
            # Falls ent_path in UIMain anders heißt, stillschweigend ignorieren
            pass

        # CSV laden (data_loader übernimmt die Details/Kodierung etc.)
        try:
            df = data_loader.load_csv(path)
        except Exception as exc:
            messagebox.showerror("Fehler beim Laden", f"Datei kann nicht gelesen werden:\n{exc}")
            return

        if df is None or df.empty:
            messagebox.showwarning("Hinweis", "Die Datei enthält keine Daten oder konnte nicht geladen werden.")
            return

        self.current_df = df

        # Spaltentypen ermitteln (einfach/nützlich für UI)
        try:
            types = data_loader.infer_columns(df)
            numeric = types.get("numeric", [])
            categorical = types.get("categorical", [])
        except Exception:
            # Fallback: alles als Kategorie, außer numerisch automatisch erkannt
            numeric = [c for c in df.columns if str(df[c].dtype).startswith(("int", "float"))]
            categorical = [c for c in df.columns if c not in numeric]

        # Spalten in die UI einsetzen
        self.ui.set_columns(numeric=numeric, categorical=categorical)

        # Auswahl zurücksetzen, Feldzustände ggf. neu setzen
        self.selected_x = None
        self.selected_y = None
        self._update_field_states()

    def _on_chart_type_changed(self, chart_key: str) -> None:
        """Reagiert auf die Radiobutton-Auswahl (Diagrammtyp)."""
        self.current_chart_type = chart_key
        self._update_field_states()
        # Optional direktes Neuzeichnen:
        # self._plot()

    def _on_x_changed(self, col: str) -> None:
        """X-Spalte geändert (Combobox in der UI)."""
        self.selected_x = col

    def _on_y_changed(self, col: str) -> None:
        """Y-Spalte geändert (Combobox in der UI)."""
        self.selected_y = col

    def _on_plot_clicked(self) -> None:
        self._plot()

    # ---------------------------------------------------------------------
    # Hilfslogik: Felder aktivieren/deaktivieren je nach Diagrammtyp
    # ---------------------------------------------------------------------
    def _update_field_states(self) -> None:
        """
        Aktiviert/Deaktiviert X/Y je nach Diagrammtyp.
        - hist: nur Y (numerisch), X wird deaktiviert
        - pie: X = Kategorie, Y = numerischer Wert
        - sonst: X und Y wie üblich
        """
        t = self.current_chart_type

        if t == "hist":
            self.ui.cmb_x.set("")
            self.selected_x = None
            self.ui.cmb_x.config(state="disabled")
            self.ui.cmb_y.config(state="readonly")
        elif t == "pie":
            self.ui.cmb_x.config(state="readonly")
            self.ui.cmb_y.config(state="readonly")
        else:
            self.ui.cmb_x.config(state="readonly")
            self.ui.cmb_y.config(state="readonly")

    # ---------------------------------------------------------------------
    # Zeichnen
    # ---------------------------------------------------------------------
    def _plot(self) -> None:
        """Zentrale Plot-Funktion: validiert Eingaben und zeichnet über plotter.draw."""
        if self.current_df is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine CSV-Datei laden.")
            return

        chart_key = self.current_chart_type
        x = self.selected_x
        y = self.selected_y

        # Einfache Validierungsregeln (anfängerfreundlich)
        if chart_key == "hist":
            if not y:
                messagebox.showwarning("Eingabe fehlt", "Bitte eine Y-Spalte für das Histogramm wählen (numerisch).")
                return
        elif chart_key == "pie":
            if not x or not y:
                messagebox.showwarning("Eingabe fehlt", "Bitte Kategorie (X) und Wert (Y) für das Kreisdiagramm wählen.")
                return
        else:
            if not x or not y:
                messagebox.showwarning("Eingabe fehlt", "Bitte X- und Y-Spalte wählen.")
                return

        # Achse leeren und zeichnen lassen
        self.ax.clear()
        try:
            plotter.draw(
                chart_type=chart_key,
                df=self.current_df,
                x=x,
                y=y,
                ax=self.ax,
            )
            self.canvas.draw_idle()
        except Exception as exc:
            messagebox.showerror("Fehler beim Plotten", f"Darstellung fehlgeschlagen:\n{exc}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
