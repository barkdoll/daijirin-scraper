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


class Daijirin():

    def __init__():
        print('hi')

    def search(term):

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

        # Function that obtains user-chosen header for defnition output
        def choose_header(header_list):
            if len(header_list) > 1:
                # If there is more than one entry head,
                # user must choose one from the console.
                print("Choose which one you would like by typing " +
                      "the entry's number and press Enter:\n")
                for q, choices in enumerate(header_list, 1):
                    text = choices.get_text().encode('utf-8')
                    print(u'{0}. '.format(q) + text.decode('utf-8'))

                # The extra space looks clean :)
                print('')

                # Checks if the user's input is a valid number from the listing
                while True:
                    try:
                        chosen = header_list[int(input()) - 1]
                        break
                    except IndexError:
                        print("Error: enter a number that's on the list.")
                        continue
            # If there is only one header, it will be selected
            # automatically for extracting defintions
            else:
                chosen = header_list[0]
            return chosen

        # Runs the above function to get the proper header
        chosen_head = choose_header(entry_head)
        # Finds the body tag that contains definition(s)
        chosen_body = chosen_head.find_next_sibling('div', class_='NetDicBody')
        # Finds the yomigana for the word
        yomigana = chosen_head.find('b').get_text()

        # Omits repetitive yomigana if term is strictly in hiragana
        if yomigana == term:
            yomigana = ''

        # Takes multi-definition entries and generates a list for output
        def_numbers = chosen_body.find_all('div', style="float:left")

        defs = []
        definition = []
        html = []

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

            html.append('【' + term + '】 ' + yomigana)

            # Creates list out of definitions
            html.append('<ol>')

            for k in definition:
                html.append('<li>' + k + '</li>')

            html.append('</ol>')

            # Converts html list to one whole string
            # for pushing to the entries list
            html = '\n'.join(html)
            push_entry()

        # Checks for single definition and parses it in the html
        else:
            one_div = chosen_body.select_one("div div div").get_text()

            definition = ' '.join(one_div.split())
            html = '【' + term + '】 ' + yomigana + '<br />\n' + definition
            push_entry()

        # Shows successful output in console
        print('\n', html, '\n')
