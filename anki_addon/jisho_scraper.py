# -*- coding: utf-8 -*-
'''
Addon: Daijirin Definition Scraper
Copyright: (c) Jesse Barkdoll 2017-2019 <https://github.com/barkdoll>

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

from bs4 import BeautifulSoup
import requests
import os
import sys
import re
from .jisho_config import jisho_config


# Helper function to get icon path
def iconPath():
    here = os.path.dirname(os.path.abspath(__file__))

    # set proper OS path separator
    if isWin:
        sep = '\\'
    else:
        sep = '/'

    icon_path = here + "{0}icons{0}icon.png".format(sep)
    return icon_path


class Scraper:
    def __init__(self, term, jisho='daijirin'):
        self.term = term
        self.jisho = jisho
        self.jisho_name = jisho_config[self.jisho]['name']
        self.url_id = jisho_config[self.jisho]['url_id']

    def scrape(self):
        # Fetch initial page source
        url = 'https://www.weblio.jp/content/{}'.format(self.term)
        sauce = requests.get(url).content
        soup = BeautifulSoup(sauce, "html.parser")

        # Find the header of selected dictionary
        header_url = soup.find('a', href=re.compile(
            ".+/cat/dictionary/{}.*".format(self.url_id))
        )

        try:
            header = header_url.find_parent('div', class_='pbarT')
        except:
            header = None
            pass

        if header is None:
            return None

        # Find the header of selected dictionary
        entry = header.find_next_sibling('div', class_='kijiWrp')

        # Outputs Daijirin header(s) to a list for the user to choose from
        def parse_daijirin_def():
            data = {}

            entry_heads = entry.find_all('div', class_='NetDicHead')

            if len(entry_heads) > 1:
                chosen_head = EntrySelectDialog(entry_heads).selection
                if chosen_head == 'cancelled':
                    return 'cancelled'
            elif len(entry_heads) == 1:
                chosen_head = 0
            else:
                return None

            chosen_body = entry_heads[chosen_head].find_next_sibling(
                'div', class_='NetDicBody')

            data['yomigana'] = entry_heads[chosen_head].find('b').text

            # Omits repetitive yomigana if term is strictly in hiragana
            if data['yomigana'] == self.term:
                data['yomigana'] = ''

            defs = chosen_body.find_all('span', style="text-indent:0;")
            # If multiple definitions
            if len(defs) > 1:
                defs = [d.text for d in defs]
                # Removes extra whitespaces in the definition strings
                stripped = ["".join(piece.split()) for piece in defs]

                data['body'] = "\n".join(
                    ['<ol>'] +
                    [('<li>' + d + '</li>') for d in stripped] +
                    ['</ol>']
                )
            # If only one definition
            else:
                single_def = chosen_body.select_one("div div div").text
                data['body'] = '<br>\n' + "".join(single_def.split())

            return data

        def parse_wiki_def():
            data = {}

            chosen_head = entry.find('h2', class_='midashigo')
            chosen_body = chosen_head\
                .find_next_sibling('div', class_="Wkpja")\
                .find('p', class_=None)\
                .text

            data['yomigana'] = ''
            data['body'] = '<br>\n' + chosen_body

            return data

        def parse_action(dictionary):
            return {
                'daijirin': parse_daijirin_def,
                'wikipedia': parse_wiki_def
            }[dictionary]()

        definition = parse_action(self.jisho)

        html = '【{0}】 {1}{2}'.format(
            self.term, definition['yomigana'], definition['body']
        )
        return html


class ScraperWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent.widget)

        self.web = parent.web

        self.setWindowIcon(QIcon(iconPath()))
        self.setWindowTitle(
            'Search 辞書 definitions ' +
            '(can do multi-word search separated by spaces)'
        )
        self.resize(700, 500)

        vl = QVBoxLayout()
        hl = QHBoxLayout()

        default_font = self.setupFont()

        self.search_box = QLineEdit()
        self.search_box.setFont(default_font)
        hl.addWidget(self.search_box)

        self.jisho_select = QComboBox()
        self.jisho_select.setFont(default_font)
        self.jisho_select.setToolTip('Select dictionary to search on')
        self.jisho_select.addItems(
            [value['name']for key, value in jisho_config.items()]
        )
        self.jisho_select.currentIndexChanged.connect(
            self.set_jisho)
        hl.addWidget(self.jisho_select)

        self.search_btn = QPushButton(u' 検索 (\u23CE) ')
        self.search_btn.setFont(default_font)
        self.search_btn.setToolTip('Search for input term(s)')
        self.search_btn.clicked.connect(self.onSearch)
        hl.addWidget(self.search_btn)

        self.add_btn = QPushButton(u' 追加 (Ctrl+\u23CE) ')
        self.add_btn.setFont(default_font)
        self.add_btn.setToolTip('Add definitions to current note field')
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

        self.call_jisho = self.set_jisho()
        self.search_box.setFocus()
        self.show()

    def setupFont(self):
        font = QFont()
        if sys.platform == "win32":
            font.setFamily("Meiryo")
        elif sys.platform == "darwin":
            try:
                platform
            except NameError:
                import platform
            if platform.mac_ver()[0].startswith("10.10"):
                font.setFamily("Lucida Grande")
        elif sys.platform.startswith("linux"):
            font.setFamily("Luxi Sans")

        font.setPointSize(11)
        return font

    def set_jisho(self):
        jisho_name = str(self.jisho_select.currentText())
        for jisho_k, jisho_v in jisho_config.items():
            if jisho_v['name'] == jisho_name:
                self.jisho = jisho_k
                break
        return

    def onSearch(self):
        query = self.search_box.text()

        if query is '':
            return
        else:
            words = query.split()

        self.setWindowTitle('Searching...')

        results = [Scraper(term, self.jisho).scrape() for term in words]

        for i, result in enumerate(results):
            if result == 'cancelled':
                pass
            elif result is None:
                NoneFound(words[i], self.jisho)
            else:
                if self.output_box.toPlainText() == '':
                    self.output_box.appendPlainText(result)
                else:
                    div_str = '\n<div>\n' + result + '\n</div>'
                    self.output_box.appendPlainText(div_str)

        self.search_box.setText('')
        self.search_box.setFocus()
        self.setWindowTitle(
            'Search 辞書 definitions ' +
            '(can do multi-word search separated by spaces)'
        )

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
        self.web.eval(
            "document.execCommand('insertHTML', false, %s);"
            % json.dumps(data)
        )

        self.close()


class EntrySelectDialog(QDialog):
    def __init__(self, choice_list):
        super().__init__()
        self.choice_list = choice_list

        self.setWindowTitle('Choose entry')
        self.setWindowIcon(QIcon(iconPath()))

        self.resize(300, 300)

        font = ScraperWindow.setupFont(self)
        # self.setFont(font)

        self.listing = QListWidget()
        self.listing.setFont(font)
        for choice in choice_list:
            c = choice.text
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
    def __init__(self, search, jisho):
        super().__init__()

        self.setWindowIcon(QIcon(iconPath()))
        font = ScraperWindow.setupFont(self)
        self.setFont(font)

        search_url = 'https://www.weblio.jp/content/{}'.format(search)

        self.setIcon(QMessageBox.Information)
        self.setText("No " + jisho_config[jisho]['name'] +
                     " definitions found for " + search)
        self.setInformativeText(
            "<a href=\"" + search_url + "\">Check weblio results " +
            "for other dictionary definitions.</a>"
        )
        self.setWindowTitle("None found")

        self.exec_()


def addMyButton(buttons, editor):
    editor._links['大辞林'] = ScraperWindow

    buttons.insert(
        0,
        editor._addButton(
            iconPath(),  # "/full/path/to/icon.png",
            "大辞林",  # link name
            "Add definitions from 大辞林"
        )
    )
    return buttons


addHook("setupEditorButtons", addMyButton)
