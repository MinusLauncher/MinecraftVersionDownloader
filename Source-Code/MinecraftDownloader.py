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
        root.resizable(False, False)  # Empêcher le redimensionnement de la fenêtre

        self.manifest = self.get_version_manifest()
        self.is_downloading = False  # Pour garder une trace de l'état du téléchargement

        # Définir l'icône de la fenêtre après téléchargement
        self.set_window_icon()

        ttk.Label(root, text="Version:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.version_var = tk.StringVar()
        self.version_dropdown = ttk.Combobox(root, textvariable=self.version_var, state="readonly")
        self.version_dropdown['values'] = [version['id'] for version in self.manifest['versions']]
        self.version_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

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
        
        self.current_file_var.set(f"MinecraftDownloader - Version 1.0 (By Minus)")

        self.download_button = ttk.Button(root, text="Download", command=self.start_download)
        self.download_button.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        root.grid_columnconfigure(1, weight=1)


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
                    print("App Launched")
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
        self.download_button.grid_forget()  # Cacher le bouton de téléchargement
        ttk.Button(self.root, text="Fermer", command=self.root.destroy).grid(row=4, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(self.root, text="Open File Location", command=lambda: webbrowser.open(self.save_location_var.get())).grid(row=4, column=2, sticky=(tk.W, tk.E), padx=5, pady=5)

def create_directory_recursive(path):
    if not os.path.exists(path):
        os.makedirs(path)

def show_startup_progress(root):
    startup_window = tk.Toplevel(root)
    startup_window.title("Extracting...")
    startup_window.geometry('300x70')
    startup_window.resizable(False, False)

    ttk.Label(startup_window, text="Extracting...").pack(padx=5, pady=5)

    startup_progress_var = tk.DoubleVar()
    startup_progress_bar = ttk.Progressbar(startup_window, variable=startup_progress_var, maximum=100)
    startup_progress_bar.pack(fill=tk.X, padx=5, pady=5)
    startup_window.update()

    for i in range(101):
        startup_progress_var.set(i)
        time.sleep(0.0030)  # Simuler le processus pendant 5 secondes
        startup_window.update()

    startup_window.destroy()

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
