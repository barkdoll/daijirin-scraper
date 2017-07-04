import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtGui import QIcon


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50,50,500,300)
        self.setWindowTitle('Daijirin Definition Grabber')
        # self.setWindowIcon('pic.png')
        self.show()

app = QApplication(sys.argv)
Gui = Window()
sys.exit(app.exec_())