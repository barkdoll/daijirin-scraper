# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import bs4 as bs
import urllib.request
import urllib.parse
import sys
import os
import pyperclip


# NOTE: THIS IS FOR GUI INTEGRATION IN THE PYQT ANKI ADDON.
# IT WILL BE HEAVILY MODIFIED FROM THE ORIGINAL CLI VERSION

# Turn this off to see tracebacks for debugging
sys.tracebacklimit = None


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
            chosen_head = EntrySelectDialog(entry_list).exec_()
            print(chosen_head)

        elif len(entry_list) == 1:
            chosen_head = entry_list[0]
            print(chosen_head)
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

    def setupList(self, choices):
        for choice in choices:
            c = choice.get_text()
            self.listing.addItem(c)

    def setEntry(self):
        print('ACCEPTED')
        self.done()
        return u'fuck'

    def onRejected(self):
        print('REJECTED')
