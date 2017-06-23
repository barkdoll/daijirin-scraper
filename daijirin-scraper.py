# Should change this to scrape weblio.jp instead of kotobank. They have a SLIGHTLY easier structure to work with for extracting the dictionary data

import bs4 as bs
import urllib.request
import urllib.parse
import sys


# pushes complete entry into final output list
def pushEntry():
    if len(entries) < 1:
        entries.append(html)
    else:
        entries.append('\n\n<div>' + html + '</div>')

term = sys.argv[1]

# Creates an ASCII-friendly URL to query a webbrowser search
converted_term = urllib.parse.quote(term, safe='')
url = 'http://www.weblio.jp/content/' + converted_term

# Opens the url and extracts the source html usings bs4
sauce = urllib.request.urlopen(url)
soup = bs.BeautifulSoup(sauce, 'lxml')


daijirin = soup.find('a', href="http://www.weblio.jp/cat/dictionary/ssdjj")

# used to locate the div after it for extracting definitions
daiji_header = daijirin.find_parent('div', class_="pbarT")

# Finds the div containing the Daijirin definitions
entry = daiji_header.find_next_sibling('div', class_='kijiWrp')

# BIG BIG BIG TODO: change this to a find_all that can distinguish from multiple definitions and allow the user to select the one he wants to keep. Also find the correct yomigana based on the users selection.

entry_head = entry.find('div', class_='NetDicHead')

entry_body = entry.find('div', class_='NetDicBody')

yomigana = entry_head.find('b').get_text()

definition = []
parsed = ''
html = []
entries = []

# Takes multi-definition entries and generates a list for output
def_numbers = entry.find_all('div', style="float:left")

multi_defs = []
for n in def_numbers:
    multi_defs.append(n.next_sibling)


print(multi_defs)

# TODO: Put this in function so that multiple definitions can be generated for entries list

# Checks for multiple definitions and adds list tags for proper html structure
if len(multi_defs) > 1:
    stripped = []

    for i in multi_defs:
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

    # Converts html list to one whole string for pushing to the entries list
    html = '\n'.join(html)
    pushEntry()


# Checks for single definition and parses it in the html
else:
    one_div = entry_body.select_one("div div div").get_text()

    definition = ' '.join(one_div.split())
    html = '【' + term + '】 ' + yomigana + '<br />\n' + definition



    pushEntry()



print('\nEntries: ')
for x in entries:
    print(x)

