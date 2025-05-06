from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QTextBrowser, QVBoxLayout

class HelpWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.browser)

        self.load_help_file()

    def load_help_file(self):
        # Change the file path to your own external help file path
        file_path = './help.html'
        url = QUrl(file_path)
        self.browser.setSource(url)

if __name__ == '__main__':
    app = QApplication([])
    help_widget = HelpWidget()
    help_widget.show()
    app.exec_()
