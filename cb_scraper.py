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
import re as Regex
import pyperclip
from cb_config import jisho_config
# from cb_config import kana

# Turn this off to see tracebacks for debugging
sys.tracebacklimit = None


class Scraper:
    def __init__(self, term, jisho='daijirin'):
        self.term = term
        self.jisho = jisho
        self.jisho_name = jisho_config[self.jisho]['name']
        self.url_id = jisho_config[self.jisho]['url_id']
        self.parse_action = jisho_config[self.jisho]['parse_action']

        if self.term == 'clear':
            self.clear()
        elif self.term == 'cut':
            self.cut()
        elif self.term == 'list':
            self.list_defs()
        else:
            self.scrape()

    # Clears the text file if the 'clear' argument is passed
    def clear(self):
        clear_file = open('definitions.txt', 'w')
        clear_file.write('')

    # Cuts all definitions in file to clipboard for pasting in Anki
    def cut(self):
        # Reads the file as bytes ('r+b')
        copy_file = open('definitions.txt', 'r+b').read()
        # Encodes the bytes to utf-8 and copies text to clipboard
        pyperclip.copy(copy_file.decode('utf-8'))
        # Clears the contents of the file
        clear()

    # Outputs definitions.txt to the console
    def list_defs(self):
        if os.stat("definitions.txt").st_size == 0:
            print("\nThere's no definitions to show!\n")
        else:
            read_file = open('definitions.txt', 'rb')
            print('\n', read_file.read().decode('utf-8'), '\n')

    def scrape(self):
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

        url = 'https://www.weblio.jp/content/{}'.format(self.term)

        # Opens the url and extracts the source html usings bs4
        sauce = requests.get(url).content
        soup = BeautifulSoup(sauce, 'html.parser')
        header_url = soup.find(
            'a', href=Regex.compile(
                ".+/cat/dictionary/{}.*".format(self.url_id)
                )
        )

        # Function used to locate selected dicitonary's entry section
        def get_header():
            try:
                grabbed = header_url.find_parent('div', class_='pbarT')
            except:
                grabbed = None
                pass

            return grabbed

        header = get_header()

        if header is None:
            print(
                "\nNo " + self.jisho_name + " definitions found for '" +
                self.term + "'.\nTry another term or check your input.\n"
            )
            return

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

            data['yomigana'] = Regex.sub(
                r'.+（(.+)）と?は、?.+', '\g<1>', chosen_body)

            data['body'] = '<br>\n' + Regex.sub(
                r'.+）と?は、?(.+)', r'\1', chosen_body)

            return data

        definition = eval(self.parse_action)()

        # Omits repetitive yomigana if term is strictly in hiragana
        if definition['yomigana'] == self.term:
            yomigana = ''

        html = '【{0}】 {1}{2}'.format(
            self.term, definition['yomigana'], definition['body']
        )

        push_entry(html)
        # Shows successful output in console
        print('\n', html, '\n')


# Initialize!
args = sys.argv[1:]
if len(args) == 0:
    raise ValueError('no terms given. I need a search term pal.')
else:
    try:
        if any("--wiki" in a for a in args):
            args = [term for term in args if term != "--wiki"]
            [Scraper(terms, 'wikipedia') for terms in args]
        else:
            [Scraper(terms) for terms in args]
    except:
        import traceback
        print(traceback.format_exc())
