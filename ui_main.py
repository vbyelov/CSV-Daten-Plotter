# ui_main.py
# Einfache GUI-Oberfläche (Skelett) für CSV Daten Plotter

import tkinter as tk
from tkinter import ttk


class MainUI:
    def __init__(self, root):
        # Hauptfenster
        self.root = root
        self.root.title("CSV Daten Plotter")
        self.root.geometry("1000x700")  # Breite x Höhe

        # --- Oberer Bereich: Dateiauswahl ---
        frame_top = ttk.Frame(root, padding="10")
        frame_top.pack(side="top", fill="x")

        # Knopf: Ordner wählen
        self.btn_choose_folder = ttk.Button(frame_top, text="Ordner wählen")
        self.btn_choose_folder.pack(side="left", padx=5)

        # Liste der CSV-Dateien
        self.listbox_files = tk.Listbox(frame_top, height=5)
        self.listbox_files.pack(side="left", fill="x", expand=True, padx=5)

        # Knopf: Datei laden
        self.btn_load_file = ttk.Button(frame_top, text="Datei laden")
        self.btn_load_file.pack(side="left", padx=5)

        # --- Mittlerer Bereich: Spalten und Plottyp ---
        frame_middle = ttk.Frame(root, padding="10")
        frame_middle.pack(side="top", fill="x")

        # Dropdown für Plottyp
        self.cmb_plot_type = ttk.Combobox(
            frame_middle,
            values=["Line", "Pie", "Histogram", "Stacked Area", "Polar"],
            state="readonly"
        )
        self.cmb_plot_type.set("Plottyp")
        self.cmb_plot_type.pack(side="left", padx=5)

        # Dropdown für X-Spalte
        self.cmb_x = ttk.Combobox(frame_middle, values=[], state="readonly")
        self.cmb_x.set("X-Spalte")
        self.cmb_x.pack(side="left", padx=5)

        # Listbox für Y-Spalten (Mehrfachauswahl)
        self.lst_y = tk.Listbox(frame_middle, selectmode="extended", height=5, exportselection=False)
        self.lst_y.pack(side="left", padx=5)

        # Knopf: Plot anzeigen
        self.btn_plot = ttk.Button(frame_middle, text="Plot anzeigen")
        self.btn_plot.pack(side="left", padx=5)

        # Knopf: Plot speichern (PNG)
        self.btn_save_png = ttk.Button(frame_middle, text="Plot speichern (PNG)")
        self.btn_save_png.pack(side="left", padx=5)

        # --- Unterer Bereich: Canvas für Plot ---
        frame_bottom = ttk.Frame(root, padding="10")
        frame_bottom.pack(side="top", fill="both", expand=True)

        # Container für das Diagramm (wird von app.py genutzt)
        self.frame_plot = frame_bottom

        # Platzhalter-Label
        self.lbl_placeholder = ttk.Label(frame_bottom, text="Hier erscheint das Diagramm")
        self.lbl_placeholder.pack(expand=True)


# Testlauf: wenn Datei direkt gestartet wird
if __name__ == "__main__":
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()

#end of file