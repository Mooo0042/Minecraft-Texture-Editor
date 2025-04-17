# gui.py
MC_VERSION_FORMATS = {
    "1.20.x": 15,
    "1.19.x": 13,
    "1.18.x": 8,
    "1.17.x": 7,
    "1.16.x": 6,
    "1.15–1.13": 5,
    "1.12–1.11": 3,
    "1.10–1.6": 2,
    "1.5": 1
}

import os
import zipfile
import io
from PIL import Image
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QLabel,
    QScrollArea, QWidget, QGridLayout, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from editor import PixelEditor  # WICHTIG: editor.py muss vorhanden sein

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Texture Editor")
        self.setGeometry(100, 100, 1000, 700)

        self.edited_images = {}     # Bearbeitete Texturen
        self.original_images = {}   # Originaltexturen
        self.editor_windows = []    # Fenster offen halten!

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()

        # Neue ComboBox für Version
        self.version_box = QComboBox()
        self.version_box.addItems(MC_VERSION_FORMATS.keys())
        top_bar.addWidget(QLabel("Minecraft Version:"))
        top_bar.addWidget(self.version_box)

        # Import- und Export-Button
        self.import_btn = QPushButton("Mod-JAR öffnen")
        self.import_btn.clicked.connect(self.open_jar)
        top_bar.addWidget(self.import_btn)

        self.export_btn = QPushButton("Exportieren")
        self.export_btn.clicked.connect(self.export_textures)
        top_bar.addWidget(self.export_btn)

        top_bar.addStretch()    

        # Galerie
        self.scroll_area = QScrollArea()
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.content_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addLayout(top_bar)

        main_layout.addWidget(self.scroll_area)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def open_jar(self):
        jar_path, _ = QFileDialog.getOpenFileName(self, "Mod-JAR auswählen", "", "JAR-Dateien (*.jar)")
        if not jar_path:
            return

        extracted_images = self.extract_textures_from_jar(jar_path)
        self.original_images = {name: img for name, img in extracted_images}
        self.display_images()  # Alle Originaltexturen anzeigen

    def extract_textures_from_jar(self, jar_path):
        pngs = []
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for file in jar.namelist():
                if file.endswith('.png') and file.startswith("assets/"):
                    with jar.open(file) as img_file:
                        png_data = img_file.read()
                        try:
                            image = Image.open(io.BytesIO(png_data)).convert("RGBA")
                            pngs.append((file, image))
                        except Exception as e:
                            print(f"Fehler beim Laden von {file}: {e}")
        return pngs

    def export_textures(self):
        if not self.edited_images:
            QMessageBox.warning(self, "Keine Änderungen", "Es gibt keine bearbeiteten Texturen zum Exportieren.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Texture Pack exportieren", "", "Minecraft Texture Pack (*.zip)")
        if not save_path:
            return

        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            selected_version = self.version_box.currentText()
            pack_format = MC_VERSION_FORMATS.get(selected_version, 15)
            # pack.mcmeta schreiben
            mcmeta_path = os.path.join(temp_dir, "pack.mcmeta")
            print(f"[DEBUG] Exportiere mit pack_format: {pack_format} für Version: {selected_version}")
            with open(mcmeta_path, "w", encoding="utf-8") as f:
                f.write(f'{{\n'
                        f'  "pack": {{\n'
                        f'    "pack_format": {pack_format},\n'  #Ausgewählte Version
                        f'    "description": "§bErstellt mit Texture Editor"\n'
                        f'  }}\n'
                        f'}}')

            # Bilder exportieren
            for name, img in self.edited_images.items():
                out_path = os.path.join(temp_dir, name)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                img.save(out_path, format="PNG")

            # ZIP schreiben
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=temp_dir)
                        zipf.write(file_path, arcname)

        QMessageBox.information(self, "Export abgeschlossen", f"Texture Pack exportiert nach:\n{save_path}")

    def display_images(self):
        # Alte Inhalte löschen
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            self.grid_layout.removeWidget(widget)
            widget.setParent(None)

        # Nur ein Bild pro Name anzeigen (bearbeitet > original)
        all_images = []
        for name, original_img in self.original_images.items():
            if name in self.edited_images:
                all_images.append((name, self.edited_images[name]))
            else:
                all_images.append((name, original_img))

        for i, (name, pil_img) in enumerate(all_images):
            qt_img = self.pil_to_qpixmap(pil_img)
            label = QLabel()
            label.setPixmap(qt_img.scaled(64, 64, Qt.KeepAspectRatio))
            label.setToolTip(name)

            def open_editor(pil_img=pil_img, filename=name):
                def save_callback(edited_img):
                    self.edited_images[filename] = edited_img
                    print(f"Bearbeitet: {filename}")
                    self.display_images()
                editor = PixelEditor(pil_img.copy(), save_callback)
                editor.show()
                self.editor_windows.append(editor)

            def on_click(event, pil_img=pil_img, filename=name):
                if event.button() == Qt.LeftButton:
                    open_editor(pil_img, filename)
                elif event.button() == Qt.RightButton and filename in self.edited_images:
                    self.edited_images.pop(filename)
                    print(f"Zurückgesetzt: {filename}")
                    self.display_images()

            label.mousePressEvent = on_click

            self.grid_layout.addWidget(label, i // 10, i % 10)

    def pil_to_qpixmap(self, img):
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg)
