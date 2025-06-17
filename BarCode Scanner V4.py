import sys
import cv2
import json
import urllib.request
from pyzbar.pyzbar import decode
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class BarCode_Scanner(QWidget):
    def __init__(self, camera_index=0):
        super().__init__()
        self.setWindowTitle("Barcode Scanner with Image")

        # 1) Title
        self.Title = QLabel("SCAN PRODUCT BARCODE:", self)
        self.Title.setAlignment(Qt.AlignCenter)
        self.Title.setStyleSheet("font-size: 18px; font-weight: bold;")

        # 2) Video feed
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        # 3) Product image
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(200, 200)  # Reserve space

        # 4) Info labels
        self.desc1 = QLabel("", self)
        self.desc2 = QLabel("", self)
        self.desc3 = QLabel("", self)
        self.halal_label = QLabel("", self)
        self.halal_label.setWordWrap(True)
        self.halal_label.setAlignment(Qt.AlignCenter)
        self.halal_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # 5) Layout: video + image side by side, then details below
        top_row = QHBoxLayout()
        top_row.addWidget(self.video_label, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(self.Title)
        layout.addLayout(top_row)
        layout.addWidget(self.image_label, 1)
        layout.addWidget(self.desc1)
        layout.addWidget(self.desc2)
        layout.addWidget(self.desc3)
        layout.addWidget(self.halal_label)
        self.setLayout(layout)

        # 6) OpenCV camera
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera.")

        # 7) Timer for live feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~33 FPS

        self.last_barcode = None

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        barcodes = decode(frame)
        if barcodes:
            raw = barcodes[0].data.decode('utf-8', errors='replace')
            if raw != self.last_barcode:
                self.last_barcode = raw
                self.search_api(raw)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    def search_api(self, barcode_value):
        api_key = "0679hdynayu05li2yowaxjz9alhhpv"
        url = (
            f"https://api.barcodelookup.com/v3/products"
            f"?barcode={barcode_value}&formatted=y&key={api_key}"
        )
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.loads(resp.read().decode())
            product = data["products"][0]

            # --- Load product image ---
            images = product.get("images", [])
            if images:
                img_url = images[0]
                try:
                    raw_data = urllib.request.urlopen(img_url).read()
                    pix = QPixmap()
                    pix.loadFromData(raw_data)
                    # scale to fit
                    self.image_label.setPixmap(pix.scaled(
                        self.image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ))
                except Exception:
                    self.image_label.clear()
            else:
                self.image_label.clear()

            # --- Text info ---
            name = product.get("title", "Unknown")
            nutrition = product.get("nutrition_facts", "N/A")
            self.ingredients = product.get("ingredients", "")

            self.desc1.setText(f"Product: {name}")
            self.desc2.setText(f"Nutrition: {nutrition}")
            self.desc3.setText(f"Ingredients: {self.ingredients}")
            print(f"Scanned: {name}")

        except Exception as e:
            print("API request failed:", e)
            self.desc1.setText("API Error")
            self.desc2.clear()
            self.desc3.clear()
            self.halal_label.clear()
            self.image_label.clear()
            return

        self.check_halal()

    def check_halal(self):
        haram_list = [
            "gelatin","lard","suet","tallow","mono- and diglycerides",
            "glycerin","stearic acid","calcium stearate",
            "sucrose esters of fatty acids","rennet","chymosin",
            "l-cysteine","pancreatin","trypsin","pepsin",
            "carmine","cochineal extract","shellac","isinglass",
            "alcohol","ethanol","wine vinegar",
            "vitamin d3","bone char"
        ]
        text = self.ingredients.lower()
        found = any(item in text for item in haram_list)

        if found:
            self.halal_label.setText("NOT HALAL\nX")
            print("Product is NOT HALAL")
        else:
            self.halal_label.setText("✅ HALAL")
            print("Product is HALAL")

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BarCode_Scanner()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())
