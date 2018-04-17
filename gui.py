# from aqt import editor
# import utility

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import json
# for escaping html characters
# import utility
from Daijiscrape import Daijirin



class EntrySelectDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(EntrySelectDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle('Choose entry')
        self.resize(500, 300)

        self.listing = QListWidget()
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.onAccepted)
        self.buttonBox.rejected.connect(self.onRejected)

        for i in range(10):
            self.listing.addItem(str(i))
        w = QWidget()
        vl = QVBoxLayout()
        vl.addWidget(self.listing)
        vl.addWidget(self.buttonBox)

        w.setLayout(vl)
        self.setLayout(vl)

    def onAccepted(self, s):
        print('accepted', s)

    def onRejected(self, s):
        print('REJECTED', s)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle('大辞林 definitions from weblio.jp')
        self.resize(700, 500)

        vl = QVBoxLayout()
        hl = QHBoxLayout()

        default_font = self.setupFont()

        self.search_box = QLineEdit()
        self.search_box.setFont(default_font)
        hl.addWidget(self.search_box)

        self.search_btn = QPushButton('検索')
        self.search_btn.setFont(default_font)
        hl.addWidget(self.search_btn)
        

        self.add_btn = QPushButton('追加')
        self.add_btn.setFont(default_font)
        hl.addWidget(self.add_btn)

        self.search_btn.clicked.connect(self.onSearch)

        output_font = QFont()
        output_font.setFamily('Meiryo')
        output_font.setPointSize(9)

        output_box = QPlainTextEdit()
        output_box.setFont(output_font)

        vl.addLayout(hl)
        vl.addWidget(output_box)

        widget = QWidget()
        widget.setLayout(vl)
        self.setCentralWidget(widget)

    def setupFont(self):
        font = QFont()
        if sys.platform == "win32":
            font.setFamily("Meiryo")
            pointSize = 11
        elif sys.platform == "darwin":
            try:
                platform
            except NameError:
                import platform
            if platform.mac_ver()[0].startswith("10.10"):
                font.setFamily("Lucida Grande")
            pointSize = 11
        elif sys.platform.startswith("linux"):
            font.setFamily("Luxi Sans")

        font.setPointSize(pointSize)
        return font

    def onSearch(self):
        term = self.search_box.text()
        print(term)
        self.setWindowTitle('searching...')
        Daijirin.search(term)
        

    
    def onAdd(self, s):
        print('s is ' + s)
        print('onAdd executed')

    def multiEntryFind(self, s):
        print('click', s)

        dlg = EntrySelectDialog(self)
        if dlg.exec_():
            print('success')
        else:
            print('FAIL')


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec_()