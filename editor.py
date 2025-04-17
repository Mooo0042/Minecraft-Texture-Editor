# editor.py

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QColorDialog
from PyQt5.QtGui import QPainter, QColor, QImage, QMouseEvent
from PyQt5.QtCore import Qt, QSize
from PIL import Image
class PixelEditor(QWidget):
    def __init__(self, pil_image, save_callback=None):
        super().__init__()
        self.setWindowTitle("Pixel Editor")
        self.image_size = pil_image.size
        self.pixel_size = 16  # Zoomstufe: 1 Pixel = 16px

        self.save_callback = save_callback
        self.current_color = QColor(0, 0, 0)
        self.qimg = self.pil_to_qimage(pil_image)

        self.init_ui()

    def init_ui(self):
        self.setFixedSize(self.image_size[0] * self.pixel_size, self.image_size[1] * self.pixel_size + 40)

        self.color_btn = QPushButton("Farbe wählen")
        self.color_btn.clicked.connect(self.choose_color)

        self.save_btn = QPushButton("Speichern")
        self.save_btn.clicked.connect(self.save_image)

        layout = QVBoxLayout()
        layout.addWidget(self.color_btn)
        layout.addWidget(self.save_btn)
        layout.setContentsMargins(5, self.image_size[1] * self.pixel_size, 5, 5)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        for y in range(self.qimg.height()):
            for x in range(self.qimg.width()):
                color = QColor(self.qimg.pixel(x, y))
                painter.fillRect(x * self.pixel_size, y * self.pixel_size,
                                self.pixel_size, self.pixel_size, color)
                painter.setPen(Qt.gray)
                painter.drawRect(x * self.pixel_size, y * self.pixel_size,
                                self.pixel_size, self.pixel_size)

    def mousePressEvent(self, event: QMouseEvent):
        x = event.x() // self.pixel_size
        y = event.y() // self.pixel_size
        if 0 <= x < self.qimg.width() and 0 <= y < self.qimg.height():
            self.qimg.setPixelColor(x, y, self.current_color)
            self.update()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color

    def save_image(self):
        pil_img = self.qimage_to_pil(self.qimg)
        if self.save_callback:
            self.save_callback(pil_img)
        self.close()

    def pil_to_qimage(self, img):
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
        return qimg

    def qimage_to_pil(self, qimg):
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        img = QImage(ptr, qimg.width(), qimg.height(), QImage.Format_RGBA8888)
        return Image.frombytes("RGBA", (img.width(), img.height()), bytes(ptr))

