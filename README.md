# Daijirin Scraper | 大辞林 スクレーパー
## Purpose of this addon
To scrape dictionary definition data from [weblio.jp](http://www.weblio.jp/) for definitions from the all-wonderful 三省堂 大辞林 (Daijirin), a Japanese dictionary. It then parses the proper HTML to be injected into note fields. A template is included in the file **daijirin-scraper-example-card-layout.apkg**, which you can double click and import directly into Anki (desktop version).

[**Click here to go to the shared addon page.**](https://ankiweb.net/shared/info/311119199)

## Goals for this project
This is my first Python project. The goal was to learn more of the Anki codebase and automate a time-consuming process of adding definitions to cards.

### NOTE: this add-on currently supports single-level list definitions only
It will not support multi-level nested definitions. At that point, I think you would be doing yourself a disservice listing out an entire definition on a flash card. Also, with Weblio's archaic HTML structure, the means by which creating something that could extract multi-level nests would not be an efficient effort, and I need to focus my time and energy on other things (like studying Japanese and building more tools to help people learn languages). If someone would like to implement this feature, I am open to contributions.

If you need to reference a word with a lengthy multi-nested list of definitions, I would suggest finding the one or two specific definitions and copy-pasting them from the website.

## Standalone CLI version

This project began as a command line script. The script adds the definitions to a text file (`definitions.txt`) which could be copied to clipboard and pasted into Anki.

### Instructions for using the standalone version

I suggest using Git Bash or some other bash terminal emulator on Windows.
 
To run the script and add a definitions to the text file, run the following command.

```
/path/to/python.exe /path/to/daijirin_scraper.py 言葉
```
(言葉 can obviously be replaced with any term you would like to try)

You can alternatively make an alias as a shortcut for running the script like this:
```
alias daijirin="/path/to/python(.exe) /path/to/daijirin_scraper.py $1" 
```

Then you could just run it like this
```
daijirin 言葉
```
instead of this
```
/path/to/python(.exe) /path/to/daijirin_scraper.py 言葉
```

If the entered term was found, it will be printed to the console along with the definitions and added to **definitions.txt**. If the term could not be found, an error will print stating that no terms matched. In some cases you might need to search for the term manually on [weblio.jp](http://www.weblio.jp/).

You can view your stored definitions with:
```
daijirin list
```

Once you have the desired defnitions in **definitions.txt**, you can run:
```
daijirin cut
```

This will cut the definitions from the text file into your clipboard so you can paste into your Anki card fields. After running this command, **definitions.txt** will be empty so that it is ready when you want to use it next.

If you want to clear the **definitions.txt** file without copying them due to a mistake or otherwise, you can run:
```
daijirin clear
```

### Dependencies, required modules, etc.
* Obviously, you will need Python installed (v3.6)
* BeautfulSoup4
* urllib.request
* urllib.parse
* sys
* os
* pyperclip

### Working with Japanese text in your command line
Your command line program will require a font with Japanese glyphs. I suggest OsakaMono.
Also you will need to set your PYTHONIOENCODING variable to UTF-8 as well by running
```
export PYTHONIOENCODING=utf-8
``` 
Consult Google for help with changing your terminal font :)
