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
from jisho_config import jisho_config

# Comment this out to see tracebacks for debugging
# sys.tracebacklimit = None


class Scraper:
    def __init__(self, term, jisho='daijirin'):
        self.term = term
        self.jisho = jisho
        self.jisho_name = jisho_config[self.jisho]['name']
        self.url_id = jisho_config[self.jisho]['url_id']
        self.scrape()

    def scrape(self):
        # Fetch initial page source
        url = 'https://www.weblio.jp/content/{}'.format(self.term)
        sauce = requests.get(url).content
        soup = BeautifulSoup(sauce, 'html.parser')

        # Find the header of selected dictionary
        header_url = soup.find(
            'a', href=re.compile(
                ".+/cat/dictionary/{}.*".format(self.url_id)
                )
        )

        try:
            header = header_url.find_parent('div', class_='pbarT')
        except:
            header = None
            pass

        if header is None:
            return None

        # Finds the following element containing
        # the chosen dictionary's definitions
        entry = header.find_next_sibling('div', class_='kijiWrp')

        # Outputs Daijirin header(s) to a list for the user to choose from
        def parse_daijirin_def():
            data = {}

            entry_heads = entry.find_all('div', class_='NetDicHead')
            # Finds the yomigana for the word

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

                    # Checks if the user's input is a valid number
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
            chosen_body = chosen_head.find_next_sibling(
                'div', class_='NetDicBody'
            )

            # Takes multi-definition entries and generates a list for output
            defs = chosen_body.find_all('span', style="text-indent:0;")

            data['yomigana'] = chosen_head.find('b').text
            # Omits repetitive yomigana if term is strictly in hiragana
            if data['yomigana'] == self.term:
                data['yomigana'] = ''

            # Handle multiple definitions and parse html list
            if len(defs) > 1:
                defs = [d.text for d in defs]
                # Removes extra whitespaces in the definition strings
                stripped = ["".join(piece.split()) for piece in defs]

                data['body'] = "\n".join(
                    ['<ol>'] +
                    [('<li>' + d + '</li>') for d in stripped] +
                    ['</ol>']
                )

            # Checks for single definition and parses it in the html
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


# Pushes complete entry into final output text file
def write_txt_file(txt):
    text_file = open('definitions.txt', 'ab')
    # checks if definitions.txt is empty or not
    if os.stat("definitions.txt").st_size == 0:
        text_file.write(txt.encode('utf-8'))
    else:
        text_file.write(
            ('\n\n<div>' + txt + '</div>').encode('utf-8')
        )


# Clears the text file if the 'clear' argument is passed
def clear():
    clear_file = open('definitions.txt', 'w')
    clear_file.write('')


# Initialize!
args = sys.argv[1:]

if len(args) == 0:
    raise ValueError('no terms given. I need a search term pal.')

else:
    if any("list" in a for a in args):
        if os.stat("definitions.txt").st_size == 0:
            print("\nThere's no definitions to show!\n")
        else:
            read_file = open('definitions.txt', 'rb')
            print('\n', read_file.read().decode('utf-8'), '\n')

    elif any("cut" in a for a in args):
        # Reads the file as bytes ('r+b')
        copy_file = open('definitions.txt', 'r+b').read()
        # Encodes the bytes to utf-8 and copies text to clipboard
        pyperclip.copy(copy_file.decode('utf-8'))
        # Clears the contents of the file
        clear()

    elif any("clear" in a for a in args):
        clear()

    else:
        call_jisho = 'daijirin'

        if any("--wiki" in a for a in args):
            call_jisho = 'wikipedia'
            args = [a for a in args if a != "--wiki"]

        accumulator = []
        for term in args:
            item = Scraper(term, call_jisho).scrape()
            if item:
                write_txt_file(item)
                accumulator.append(item)
            else:
                print(
                    "\nNo " + jisho_config[call_jisho]['name'] +
                    " definitions found for '" + term +
                    "'.\nCheck your input or try another dictionary.\n"
                )

        print('\n' + '\n\n'.join(accumulator) + '\n')
