import os, sys
from urllib.parse import quote
from PyQt5.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QKeySequence, QColor, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLineEdit,
    QGraphicsDropShadowEffect,
    QShortcut,
    QLabel,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class VoidBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoidBrowser")

        # --- Window setup ---
        self.setWindowFlags(Qt.Window)  # native OS frame with X/min/max
        self.resize(960, 540)
        self.center_on_screen()
        self.setStatusBar(None)
        self.menuBar().hide()
        self.setStyleSheet(
            "background-color: #000;"
        )  # optional rounded corners not applied on OS frame

        # --- WebView setup ---
        self.page = QWebEnginePage()
        self.view = QWebEngineView()
        self.view.setPage(self.page)
        self.view.setStyleSheet("background: #1d1d20")
        self.setCentralWidget(self.view)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(resource_path("background.png"))
        self.label.setPixmap(
            pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
        )
        self.label.setGeometry(0, 0, self.width(), self.height())

        # --- Address bar overlay ---
        self.address_bar = QLineEdit(self)
        self.address_bar.setPlaceholderText("Enter URL...")
        self.address_bar.setAlignment(Qt.AlignCenter)
        self.address_bar.setFixedWidth(600)
        self.address_bar.setFixedHeight(42)
        self.address_bar.setFont(QFont("Space Mono", 12))
        self.address_bar.setStyleSheet("""
            QLineEdit {
                background: #1D1D20;
                color: #f2ecce;
                border: 2px solid #333;
                border-radius: 12px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #666;
            }
        """)
        self.address_bar.returnPressed.connect(self.load_url)
        self.address_bar.hide()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.address_bar.setGraphicsEffect(shadow)

        # --- Shortcuts ---
        QShortcut(QKeySequence("Ctrl+Alt+S"), self, activated=self.toggle_address_bar)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.view.reload)
        QShortcut(QKeySequence("Ctrl+Left"), self, activated=self.view.back)
        QShortcut(QKeySequence("Ctrl+Right"), self, activated=self.view.forward)
        QShortcut(QKeySequence("Escape"), self, activated=self.hide_address_bar)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self.go_home)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, activated=self.inject_dark_mode)

    # --- Helper to center window ---
    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def go_home(self):
        self.view.hide()  # hide webview
        self.label.show()  # show the PNG
        self.hide_address_bar()

    # --- Address bar + background resize ---
    def resizeEvent(self, event):
        # --- Resize address bar ---
        w, h = self.width(), self.height()
        bw, bh = self.address_bar.width(), self.address_bar.height()
        self.address_bar.move((w - bw) // 2, (h - bh) // 2)

        # --- Resize background image ---
        if hasattr(self, "label"):
            pixmap = QPixmap(resource_path("background.png"))
            self.label.setPixmap(
                pixmap.scaled(
                    self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            )
            self.label.setGeometry(0, 0, self.width(), self.height())

        super().resizeEvent(event)

    def toggle_address_bar(self):
        if self.address_bar.isVisible():
            self.hide_address_bar()
        else:
            self.show_address_bar()

    def show_address_bar(self):
        self.address_bar.show()
        self.address_bar.setFocus()
        self.fade = QPropertyAnimation(self.address_bar, b"windowOpacity")
        self.fade.setDuration(200)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade.start()

    def hide_address_bar(self):
        self.fade = QPropertyAnimation(self.address_bar, b"windowOpacity")
        self.fade.setDuration(150)
        self.fade.setStartValue(1.0)
        self.fade.setEndValue(0.0)
        self.fade.finished.connect(self.address_bar.hide)
        self.fade.start()

    def load_url(self):
        text = self.address_bar.text().strip()
        if not text:
            return

        # if it looks like a URL, use it; otherwise search on DuckDuckGo
        if text.startswith("http://") or text.startswith("https://") or "." in text:
            url = text if text.startswith("http") else "https://" + text
        else:
            query = quote(text)
            url = f"https://duckduckgo.com/?q={query}"

        self.view.setUrl(QUrl(url))
        self.hide_address_bar()
        self.label.hide()
        self.setCentralWidget(self.view)

    def inject_dark_mode(self):
        dark_css = """
        html, body {
            background-color: #1D1D20 !important;
            color: #f2ecce !important;
        }
        img, video, iframe { filter: brightness(0.8) contrast(1.05); }
        * { scrollbar-color: #444 #111 !important; caret-color: #ccc !important; }
        a { color: #8ab4f8 !important; }
        """

        js = f"""
        (function() {{
            var existing = document.getElementById('void-dark-style');
            if (existing) {{
                existing.remove();  // remove dark mode if already active
                return;
            }}
            var style = document.createElement('style');
            style.id = 'void-dark-style';
            style.textContent = `{dark_css}`;
            document.documentElement.appendChild(style);
        }})();
        """

        self.page.runJavaScript(js)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor("#000"))
    palette.setColor(QPalette.Base, QColor("#000"))
    palette.setColor(QPalette.Text, QColor("#eee"))
    app.setPalette(palette)

    window = VoidBrowser()
    window.show()
    sys.exit(app.exec_())
