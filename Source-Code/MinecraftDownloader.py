import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import tkinter as tk
from tkinter import ttk
import threading
import time
import shutil
from ttkthemes import ThemedTk
import threading
import webbrowser
import tempfile

class MinecraftDownloaderGUI:
    def __init__(self, root):
        self.root = root
        root.title('Minecraft Version Downloader')
        root.geometry('570x300')
        root.resizable(False, False)

        self.manifest = self.get_version_manifest()
        self.is_downloading = False

        self.set_window_icon()

        # Appliquer le style avant de créer l'interface utilisateur
        apply_large_style()

        style = ttk.Style()
        style.configure('Large.TButton', font=('Arial', 12))  # Bouton plus grand
        style.configure('Large.TCombobox', font=('Arial', 12))  # Combobox plus grand
        style.configure('Large.TEntry', font=('Arial', 12))  # Entry plus grand
        style.configure('Large.TLabel', font=('Arial', 12))  # Label plus grand

        # Configuration de la grille pour une meilleure adaptation à la nouvelle taille
        root.grid_columnconfigure(1, weight=1)
        for i in range(5):  # Supposons que vous ayez 5 lignes
            root.grid_rowconfigure(i, weight=1)

        # Define the show_all_versions_var attribute before calling update_version_dropdown
        self.show_all_versions_var = tk.BooleanVar()
        self.show_all_versions_var.set(False)  # Default to showing only 1.x versions

        # Correction du label "Version:"
        ttk.Label(root, text="Version:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.version_var = tk.StringVar()
        self.version_dropdown = ttk.Combobox(root, textvariable=self.version_var, state="readonly")
        self.version_dropdown['values'] = [version['id'] for version in self.manifest['versions']]
        self.version_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # Lier les événements de clic et de sélection
        self.version_dropdown.bind('<Button-1>', on_combobox_click)
        self.version_dropdown.bind('<<ComboboxSelected>>', on_combobox_selected)

        # Now it's safe to call update_version_dropdown, as all necessary attributes are defined
        self.update_version_dropdown()

        # Correction du label "Emplacement:" (à la bonne place avec le bon index de ligne)
        ttk.Label(root, text="Emplacement:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.save_location_var = tk.StringVar()
        self.save_location_entry = ttk.Entry(root, textvariable=self.save_location_var)
        self.save_location_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(root, text="Browse", command=self.browse_save_location).grid(row=1, column=2, padx=5)


        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.current_file_var = tk.StringVar()
        self.current_file_label = ttk.Label(root, textvariable=self.current_file_var)
        self.current_file_label.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Initialize the Checkbutton after defining show_all_versions_var
        self.show_all_versions_checkbox = ttk.Checkbutton(root, text="Afficher toutes les versions", variable=self.show_all_versions_var, command=self.update_version_dropdown)
        self.show_all_versions_checkbox.grid(row=0, column=2, sticky=tk.W, padx=5)
        
        self.current_file_var.set(f"MinecraftDownloader - Version 1.4 (By Minus)")

        self.download_button = ttk.Button(root, text="Download", command=self.start_download)
        self.download_button.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        root.grid_columnconfigure(1, weight=1)


    def update_version_dropdown(self):
        # Votre logique pour mettre à jour le combobox en fonction de la case à cocher
        if self.show_all_versions_var.get():
            versions = [version['id'] for version in self.manifest['versions']]
        else:
            versions = [version['id'] for version in self.manifest['versions'] if version['id'].startswith("1.")]
        self.version_dropdown['values'] = versions
        if versions:
            self.version_dropdown.current(0)

    def set_window_icon(self):
        icon_url = 'https://raw.githubusercontent.com/MinusLauncher/Resources/main/icon.ico'
        icon_path = self.download_icon(icon_url)
        if icon_path:
            self.root.iconbitmap(icon_path)
        else:
            messagebox.showerror("Erreur", "Les serveurs de Minus sont fermés")

    def download_icon(self, url):
        try:
            icon_dir = os.path.join(tempfile.gettempdir(), 'Minus', 'MinecraftDownloader')
            os.makedirs(icon_dir, exist_ok=True)
            icon_path = os.path.join(icon_dir, 'icon.ico')
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                    print(self.manifest['versions'])  # Pour déboguer et vérifier les données
                    time.sleep(0.3)
                    clear_console()
                    print("Running : Minus.MinecraftDownloader")
                return icon_path
        except Exception as e:
            print(f"Erreur lors du téléchargement : {e}")
            return None

    def get_version_manifest(self):
        url = 'https://launchermeta.mojang.com/mc/game/version_manifest.json'
        response = requests.get(url)
        return response.json()

    def browse_save_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_location_var.set(directory)

    def start_download(self):
        if not self.is_downloading:
            self.is_downloading = True
            self.download_button.config(text="Annuler", command=self.cancel_download)
            
            version_id = self.version_var.get()
            save_location = self.save_location_var.get()

            if not version_id or not save_location:
                messagebox.showerror("Erreur", "Veuillez sélectionner une version et spécifier un emplacement de sauvegarde.")
                self.is_downloading = False
                self.download_button.config(text="Download", command=self.start_download)
                return
            
            # Démarrage du téléchargement dans un nouveau thread pour éviter de bloquer l'interface utilisateur
            download_thread = threading.Thread(target=self.download_version_files, args=(version_id, save_location), daemon=True)
            download_thread.start()
        else:
            self.cancel_download



    def cancel_download(self):
        self.is_downloading = False
        # Mettre à jour l'interface utilisateur pour refléter l'annulation
        self.download_button.config(text="Download", command=self.start_download)
        messagebox.showinfo("Download Cancelled", "The download has been cancelled.")

        

    def progress_update(self, file, current, total):
        percentage = (current / total) * 100
        self.progress_var.set(percentage)
        self.current_file_var.set(f"Downloading: {os.path.basename(file)} ({percentage:.2f}%)")
        print(f"File: {os.path.basename(file)} - {percentage:.2f}%")
        clear_console()
        print("Running : Minus.MinecraftDownloader")
        self.root.update_idletasks()

    def download_version_files(self, version_id, save_location):
        try:
            version_info_url = next((v['url'] for v in self.manifest['versions'] if v['id'] == version_id), None)
            response = requests.get(version_info_url)
            version_info = response.json()

            client_url = version_info['downloads']['client']['url']
            client_path = os.path.join(save_location, f'{version_id}.jar')
            self.download_file_with_progress(client_url, client_path, self.progress_update)

            libraries = version_info.get('libraries', [])
            for library in libraries:
                artifact = library.get('downloads', {}).get('artifact', {})
                if artifact:
                    url = artifact.get('url')
                    path = artifact.get('path')
                    if url and path:
                        self.download_file_with_progress(url, os.path.join(save_location, 'libraries', path), self.progress_update)

            self.root.after(0, self.update_ui_post_download)
        except Exception as e:
            messagebox.showerror("Error", f"Erreur lors du téléchargement. Erreur: {str(e)}")

    def download_file_with_progress(self, url, path, progress_callback):
        response = requests.get(url, stream=True)
        total_length = int(response.headers.get('content-length', 0))
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'wb') as file:
            dl = 0
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                file.write(data)
                progress_callback(path, dl, total_length)

    def update_ui_post_download(self):
        messagebox.showinfo("MinecraftDownloader", "Version téléchargée avec succès.")
        self.current_file_var.set(f"Version téléchargée avec succès")
        print(f"Version téléchargée avec succès")
        self.download_button.grid_forget()  # Cacher le bouton de téléchargement
        ttk.Button(self.root, text="Fermer", command=self.root.destroy).grid(row=4, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(self.root, text="Open File Location", command=lambda: webbrowser.open(self.save_location_var.get())).grid(row=4, column=2, sticky=(tk.W, tk.E), padx=5, pady=5)

# Effacer l'écran/console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def create_directory_recursive(path):
    if not os.path.exists(path):
        os.makedirs(path)

def show_startup_progress(root):
    print("MD API - [Downloading updates...]")
    startup_window = tk.Toplevel(root)
    startup_window.title("Extracting...")
    startup_window.geometry('300x70')
    startup_window.resizable(False, False)

    ttk.Label(startup_window, text="Extracting...").pack(padx=5, pady=5)

    startup_progress_var = tk.DoubleVar()
    startup_progress_bar = ttk.Progressbar(startup_window, variable=startup_progress_var, maximum=100)
    startup_progress_bar.pack(fill=tk.X, padx=5, pady=5)
    startup_window.update()

    print("MD API - [Downloading JSON official Versions...]")
    time.sleep(3)
    clear_console()
    

    for i in range(101):
        startup_progress_var.set(i)
        time.sleep(0.0030)  # Simuler le processus pendant 5 secondes
        startup_window.update()

    time.sleep(0.10)
    print("MD API - [Checking Version...]")

    startup_window.destroy()


def apply_large_style():
    style = ttk.Style()

    # Configurer un style plus grand pour tous les widgets
    style.configure('TButton', font=('Arial', 12), padding=10)
    style.configure('TLabel', font=('Arial', 12), padding=10)
    style.configure('TEntry', font=('Arial', 12), padding=10)
    style.configure('TCombobox', font=('Arial', 12), padding=10)
    style.configure('TCheckbutton', font=('Arial', 12), padding=10)
    style.configure('TProgressbar', thickness=20)

    # Augmenter la hauteur des lignes dans le combobox
    style.map('TCombobox', fieldbackground=[('readonly', 'white')])
    style.map('TCombobox', selectbackground=[('readonly', 'white')])
    style.map('TCombobox', selectforeground=[('readonly', 'black')])

def on_combobox_click(event):
    event.widget.config(style='Clicked.TCombobox')

def on_combobox_selected(event):
    event.widget.config(style='TCombobox')

def main():
    root = tk.Tk()
    root.withdraw()  # Cache la fenêtre principale temporairement

    show_startup_progress(root)  # Affiche la barre de chargement au démarrage

    # Après la barre de chargement, préparer et montrer la fenêtre principale
    root.deiconify()  # Montre la fenêtre principale après le chargement
    app = MinecraftDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
