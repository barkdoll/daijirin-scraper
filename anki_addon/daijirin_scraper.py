# -*- coding: utf-8 -*-
'''
Addon: Daijirin Definition Scraper
Copyright: (c) Jesse Barkdoll 2017-2018 <https://github.com/barkdoll>

This addon was created to grab and parse definitions from the
大辞林 (daijirin) dictionary hosted on <https://weblio.jp/>


License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
'''


from aqt import mw, editor
from aqt.utils import showInfo, tooltip, isWin
from anki.utils import json
from anki.hooks import addHook
from aqt.qt import *

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import bs4 as bs
import urllib.request
import urllib.parse
import os
import sys
import re

# helper function to get icon path
def iconPath():
    here = os.path.dirname(os.path.abspath(__file__))
    
    if isWin:
        slash = '\\'
    else:
        slash = '/'    
    
    icon_path = here + "{0}icons{0}icon.png".format(slash)
    return icon_path


def Daijirin(term):

    # Creates an ASCII-friendly URL to query a webbrowser search
    converted_term = urllib.parse.quote(term, safe='')
    url = 'https://www.weblio.jp/content/' + converted_term

    # Opens the url and extracts the source html usings bs4
    sauce = urllib.request.urlopen(url)
    soup = bs.BeautifulSoup(sauce, "html.parser")
    daijirin = soup.find(
        'a', href="https://www.weblio.jp/cat/dictionary/ssdjj"
    )

    # Function used to locate Daijirin section of the web page
    def get_header():
        try:
            grabbed = daijirin.find_parent('div', class_='pbarT')
        except:
            grabbed = None
            pass

        return grabbed

    # Locates the header div that indicates the following definition
    # is a Daijirin definition
    daiji_header = get_header()
    # Handles terms with no entries found
    if daiji_header is None:
        return None

    # Finds the following div containing the Daijirin definitions
    entry = daiji_header.find_next_sibling('div', class_='kijiWrp')
    # Outputs Daijirin header(s) to a list for the user to choose from
    entry_heads = entry.find_all('div', class_='NetDicHead')

    if len(entry_heads) > 1:
        chosen_head = EntrySelectDialog(entry_heads).selection
        if chosen_head == 'cancelled':
            return 'cancelled'
    elif len(entry_heads) == 1:
        chosen_head = 0
    else:
        return None

    chosen_body = (
        entry_heads[chosen_head].find_next_sibling('div', class_='NetDicBody')
    )

    # Finds the yomigana for the word
    yomigana = entry_heads[chosen_head].find('b').get_text()
    # Omits repetitive yomigana if term is strictly in hiragana
    if yomigana == term:
        yomigana = ''

    # Takes multi-definition entries and generates a list for output
    def_numbers = chosen_body.find_all('div', style="float:left")

    defs = []
    definition = []
    html_str = []

    for n in def_numbers:
        defs.append(n.next_sibling)

    # Checks for multiple definitions and
    # adds list tags for proper html structure
    if len(defs) > 1:
        stripped = []

        for i in defs:
            text = i.get_text()
            stripped.append(text)

        # Removes extra whitespaces in the definition strings
        for j in stripped:
            definition.append(' '.join(j.split()))

        html_str.append('【' + term + '】 ' + yomigana)

        # Creates list out of definitions
        html_str.append('<ol>')

        for k in definition:
            html_str.append('<li>' + k + '</li>')

        html_str.append('</ol>')

        # Converts html list to one whole string
        # for pushing to the entries list
        html_str = '\n'.join(html_str)
        return html_str

    # Checks for single definition and parses it in the html
    else:
        one_div = chosen_body.select_one("div div div").get_text()

        definition = ' '.join(one_div.split())
        html_str = '【' + term + '】 ' + yomigana + '<br />\n' + definition
        return html_str


class ScraperWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent.widget)

        self.web = parent.web

        self.setWindowIcon(QIcon( iconPath() ))
        self.setWindowTitle('Search 大辞林 definitions from weblio.jp')
        self.resize(700, 500)

        vl = QVBoxLayout()
        hl = QHBoxLayout()

        default_font = self.setupFont()

        self.search_box = QLineEdit()
        self.search_box.setFont(default_font)
        hl.addWidget(self.search_box)

        self.search_btn = QPushButton(u' 検索 (\u23CE) ')
        self.search_btn.setFont(default_font)
        self.search_btn.clicked.connect(self.onSearch)
        hl.addWidget(self.search_btn)

        self.add_btn = QPushButton(u' 追加 (Ctrl+\u23CE) ')
        self.add_btn.setFont(default_font)
        self.add_btn.clicked.connect(self.onAdd)
        hl.addWidget(self.add_btn)

        output_font = default_font
        output_font.setPointSize(default_font.pointSize() - 1)
        output_font.setFamily('Meiryo')

        self.output_box = QPlainTextEdit()
        self.output_box.setFont(output_font)

        vl.addLayout(hl)
        vl.addWidget(self.output_box)
        self.setLayout(vl)

        self.search_box.setFocus()
        self.show()

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
        term = re.sub(r'\s', '', term)

        if term is '':
            return

        self.setWindowTitle('Searching...')
        result = Daijirin(term)

        if result == 'cancelled':
            pass
        elif result is None:
            NoneFound(term)
        else:
            if self.output_box.toPlainText() == '':
                self.output_box.appendPlainText(result)
            else:
                div_str = '\n<div>\n' + result + '\n</div>'
                self.output_box.appendPlainText(div_str)

        self.search_box.setText('')
        self.search_box.setFocus()
        self.setWindowTitle('Search 大辞林 definitions from weblio.jp')

    def keyPressEvent(self, event):
        mods = QApplication.keyboardModifiers()

        # Listens for 'Enter' key binding
        if (event.key() == Qt.Key_Enter or 
            event.key() == Qt.Key_Return):
            self.onSearch()

        # Listens for 'Ctrl+Enter' kb shortcut
        if (event.key() == Qt.Key_Enter and 
            mods == Qt.ControlModifier or
            event.key() == Qt.Key_Return and 
            mods == Qt.ControlModifier):
            self.onAdd()
        
        if (event.key() == Qt.Key_Escape):
            self.close()

    def onAdd(self):
        data = self.output_box.toPlainText()

        # TODO: Figure out how document.execCmd is working
        # Possible alternative: Line 395 / editor.py
        # self.note.fields[field] = html
        self.web.eval("document.execCommand('insertHTML', false, %s);" 
            % json.dumps(data))

        self.close()


class EntrySelectDialog(QDialog):
    def __init__(self, choice_list):
        super().__init__()
        self.choice_list = choice_list

        self.setWindowTitle('Choose entry')
        self.setWindowIcon(QIcon( iconPath() ))        

        self.resize(300, 300)

        font = ScraperWindow.setupFont(self)
        # self.setFont(font)

        self.listing = QListWidget()
        self.listing.setFont(font)
        for choice in choice_list:
            c = choice.get_text()
            self.listing.addItem(c)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)

        w = QWidget()
        vl = QVBoxLayout()
        vl.addWidget(self.listing)
        vl.addWidget(self.buttonBox)

        w.setLayout(vl)
        self.setLayout(vl)

        self.exec_()

    def onAccept(self):
        self.selection = self.listing.currentRow()
        self.accept()

    def onReject(self):
        self.selection = 'cancelled'
        self.reject()

    def keyPressEvent(self, event):
        cr = self.listing.currentRow()
        # Listens for 'Enter' key binding
        if (event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
            self.onAccept()

    # overrides closing of ScraperWindow when clicking
    # the corner 'X' to close the selection dialog box
    def closeEvent(self, event):
        self.onReject()


class NoneFound(QMessageBox):
    def __init__(self, search):
        super().__init__()

        self.search = search
        self.setWindowIcon(QIcon( iconPath() ))        

        font = ScraperWindow.setupFont(self)
        self.setFont(font)

        converted_term = urllib.parse.quote(self.search, safe='')
        url = 'https://www.weblio.jp/content/' + converted_term

        self.setIcon(QMessageBox.Information)
        self.setText("No 大辞林 definitions found for " + self.search)
        self.setInformativeText("<a href=\""+url+"\">Check weblio results " +
                                "for other dictionary definitions.</a>")
        self.setWindowTitle("None found")

        self.exec_()


def addMyButton(buttons, editor):
    editor._links['大辞林'] = ScraperWindow

    buttons.insert(0, editor._addButton(
        iconPath(), # "/full/path/to/icon.png",
        "大辞林", # link name
        "Add definitions from 大辞林"))
    return buttons


addHook("setupEditorButtons", addMyButton)
