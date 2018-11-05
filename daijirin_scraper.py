# -*- coding: utf-8 -*-
'''
Addon: Daijirin Definition Scraper
Copyright: (c) Jesse Barkdoll 2017-2019 <https://github.com/barkdoll>

This addon was created to grab and parse definitions from the
大辞林 (daijirin) dictionary hosted on <https://weblio.jp/>


License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
'''

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import pyperclip

# Turn this off to see tracebacks for debugging
sys.tracebacklimit = None


def Daijirin(term):
    # Clears the text file if the 'clear' argument is passed
    def clear():
        clear_file = open('definitions.txt', 'w')
        clear_file.write('')

    # Cuts all definitions in file to clipboard for pasting in Anki
    def cut():
        # Reads the file as bytes ('r+b')
        copy_file = open('definitions.txt', 'r+b').read()
        # Encodes the bytes to utf-8 and copies text to clipboard
        pyperclip.copy(copy_file.decode('utf-8'))
        # Clears the contents of the file
        clear()

    # Outputs definitions.txt to the console
    def list_defs():
        if os.stat("definitions.txt").st_size == 0:
            print("\nThere's no definitions to show!\n")
        else:
            read_file = open('definitions.txt', 'rb')
            print('\n', read_file.read().decode('utf-8'), '\n')

    def search(term):
        # Normally, you would use 'a' as the second argument
        # in the open() method to open a file in append mode.
        # Append mode is the same as write mode,
        # but does not overwrite original file contents).
        # But since the final output needs to be unicode,
        # you have to encode it into UTF-8 bytes instead of a string.
        # Therefore, you have to use 'ab' as the second arg,
        # which I think means append binary.
        text_file = open('definitions.txt', 'ab')

        # Pushes complete entry into final output text file
        def push_entry(txt):
            # checks if definitions.txt is empty or not
            if os.stat("definitions.txt").st_size == 0:
                text_file.write(txt.encode('utf-8'))
            else:
                text_file.write(
                    ('\n\n<div>' + txt + '</div>').encode('utf-8')
                )

        url = 'https://www.weblio.jp/content/{}'.format(term)

        # Opens the url and extracts the source html usings bs4
        sauce = requests.get(url).content
        soup = BeautifulSoup(sauce, 'html.parser')
        daijirin = soup.find(
            'a', href=re.compile(".+/cat/dictionary/ssdjj.*")
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

        if daiji_header is None:
            print(
                "\nNo 大辞林 definitions found for '"+term+"'." +
                "\nTry another term or check your input.\n"
            )
            return

        # Finds the following div containing the Daijirin definitions
        entry = daiji_header.find_next_sibling('div', class_='kijiWrp')
        # Outputs Daijirin header(s) to a list for the user to choose from
        entry_heads = entry.find_all('div', class_='NetDicHead')

        # Function that obtains user-chosen header for defnition output
        def choose_header(header_list):
            if len(header_list) > 1:
                # If there is more than one entry head,
                # user must choose one from the console.
                print(
                    "Choose which one you would like by typing " +
                    "the entry's number and press Enter:\n"
                )

                for q, choices in enumerate(header_list, 1):
                    text = choices.text.encode('utf-8')
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
        chosen_head = choose_header(entry_heads)
        # Finds the body tag that contains definition(s)
        chosen_body = chosen_head.find_next_sibling('div', class_='NetDicBody')
        # Finds the yomigana for the word
        yomigana = chosen_head.find('b').text

        # Omits repetitive yomigana if term is strictly in hiragana
        if yomigana == term:
            yomigana = ''

        # Takes multi-definition entries and generates a list for output
        defs = chosen_body.find_all('span', style="text-indent:0;")

        # Checks for multiple definitions and
        # adds list tags for proper html structure
        if len(defs) > 1:
            stripped = [d.text for d in defs]
            # Removes extra whitespaces in the definition strings
            definition = ["".join(piece.split()) for piece in stripped]

            html = "\n".join(
                [('【' + term + '】 ' + yomigana + '<ol>')] +
                [('<li>' + d + '</li>') for d in definition] +
                ['</ol>']
            )
            push_entry(html)

        # Checks for single definition and parses it in the html
        else:
            single_def = chosen_body.select_one("div div div").text

            definition = "".join(single_def.split())
            html = '【' + term + '】 ' + yomigana + '<br />\n' + definition
            push_entry(html)

        # Shows successful output in console
        print('\n', html, '\n')

    if term == 'clear':
        clear()
    elif term == 'cut':
        cut()
    elif term == 'list':
        list_defs()
    else:
        search(term)


# Initialize!
t = sys.argv[1:]
if len(t) == 0:
    raise ValueError('no terms given. I need a search term pal.')
else:
    [Daijirin(terms) for terms in t]
