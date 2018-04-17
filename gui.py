# from aqt import editor
# import utility

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import bs4 as bs
import urllib.request
import urllib.parse
import sys
import os
import pyperclip
import json
# for escaping html characters
# import utility


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.output_box = QPlainTextEdit()
        self.output_box.setFont(output_font)

        vl.addLayout(hl)
        vl.addWidget(self.output_box)

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
        self.setWindowTitle('searching...')
        self.output_box.appendPlainText(Daijirin().search(term))


class Daijirin:

    def search(self, term):

        text_file = open('definitions.txt', 'ab')

        # Pushes complete entry into final output text file
        def push_entry():
            # checks if definitions.txt is empty or not
            if os.stat("definitions.txt").st_size == 0:
                text_file.write(html.encode('utf-8'))
            else:
                text_file.write(('\n\n<div>' + html +
                                '</div>').encode('utf-8'))

        # Creates an ASCII-friendly URL to query a webbrowser search
        converted_term = urllib.parse.quote(term, safe='')
        url = 'https://www.weblio.jp/content/' + converted_term

        # Opens the url and extracts the source html usings bs4
        sauce = urllib.request.urlopen(url)
        soup = bs.BeautifulSoup(sauce, 'lxml')
        daijirin = soup.find(
            'a', href="https://www.weblio.jp/cat/dictionary/ssdjj"
        )

        # Function used to locate Daijirin section of the web page
        def get_header():
            try:
                grabbed = daijirin.find_parent('div', class_='pbarT')
                return grabbed
            # TODO: figure out how to hide the AttributeError output
            except AttributeError:
                print("\nSorry! We couldn\'t find any 大辞林 definitions for " +
                      "\'{0}\'.\nTry another term or check your input.\n"
                      .format(term))

        # Locates the header div that indicates the following definition
        # is a Daijirin definition
        daiji_header = get_header()
        # Finds the following div containing the Daijirin definitions
        entry = daiji_header.find_next_sibling('div', class_='kijiWrp')
        # Outputs Daijirin header(s) to a list for the user to choose from
        entry_head = entry.find_all('div', class_='NetDicHead')

        entry_list = []
        entry_list.extend(entry_head)

        if len(entry_list) > 1:
            chosen_head = EntrySelectDialog(entry_list)
            print(chosen_head)
            return chosen_head

        elif len(entry_list) == 1:
            chosen_head = entry_list[0]
            print(chosen_head)
            return chosen_head
        else:
            print('')
            # NoneFound() Dialog


class EntrySelectDialog(QDialog):
    def __init__(self, choice_list):
        super().__init__()
        self.choice_list = choice_list

        self.setWindowTitle('Choose entry')
        self.resize(300, 300)

        self.listing = QListWidget()
        self.setupList(self.choice_list)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.setEntry)
        self.buttonBox.rejected.connect(self.onRejected)

        w = QWidget()
        vl = QVBoxLayout()
        vl.addWidget(self.listing)
        vl.addWidget(self.buttonBox)

        w.setLayout(vl)
        self.setLayout(vl)

        self.exec_()

    def setupList(self, choices):
        for choice in choices:
            c = choice.get_text()
            self.listing.addItem(c)

    def setEntry(self):
        print('ACCEPTED')
        return 'yo yo'

    def onRejected(self):
        print('REJECTED')


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec_()
