# Daijirin Scraper | 大辞林 スクレーパー
## Purpose of this addon
To scrape dictionary definition data from [weblio.jp](http://www.weblio.jp/) for definitions from the all-wonderful 三省堂 大辞林 (Daijirin), a Japanese dictionary. It then parses the proper HTML to be injected into note fields. A template is included in the file **daijirin-scraper-example-card-layout.apkg**, which you can double click and import directly into Anki (desktop version).

## Goals for this project
This is my first Python project. The goal was to learn more of the Anki codebase and automate a time-consuming process of adding definitions to cards.

### NOTE: this add-on currently supports single-level list definitions only
It will not support multi-level nested definitions. At that point, I think you would be doing yourself a disservice listing out an entire definition on a flash card. Also, with Weblio's archaic HTML structure, the means by which creating something that could extract multi-level nests would not be an efficient effort, and I need to focus my time and energy on other things (like studying Japanese and building more tools to help people learn languages). If someone would like to implement this feature, I am open to contributions.

If you need to reference a word with a lengthy multi-nested list of definitions, I would suggest finding the one or two specific definitions and copy-pasting them from the website.


## Anki Addon version

[Click here to go to the shared addon page.](https://ankiweb.net/shared/info/311119199)

### Usage
* With the Anki main window open, go to **`Tools` > `Addons`** or type **`Ctrl + Shift + A`**
* Click on the **`Get Add-ons...`** button
* Copy and paste the following code into your Anki addons dialog: <span style="font-size:1.25em">**`311119199`**</span>
* Click **`Ok`**, wait for _Daijirin Dictionary Scraper_ to appear on the addons list, close the window and restart Anki.
* At the main window click **Add** or type `A` to open an editor dialogue. You will see a small green book button in the top right row of editor icons. Click it to begin using.

## Standalone CLI version

This project began as a command line script. The script adds the definitions to a text file (`definitions.txt`) which could be copied to clipboard and pasted into Anki.

### Dependencies, required modules, etc.
* Python v3.6+
* bs4 (Beautiful Soup v4)
* requests
* sys
* os
* pyperclip

After Python and pip are installed, you can get the additional non-standard packages by running:
```
pip install -r requirements.txt
```
from this project's directory.

### Usage

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

### Handling Japanese text on the command line
Your command line program will require a font with Japanese glyphs. I suggest OsakaMono.
Also you will need to set your PYTHONIOENCODING variable to UTF-8 as well by running
```
export PYTHONIOENCODING=utf-8
``` 

If you are using [Hyper](https://github.com/zeit/hyper), you will need the following inside your preferences file (.hyper.js):
```
env: {
      LANG: 'en_US.UTF-8'
},
```

You may obviously have other properties alongside `LANG` inside of `env`, but `LANG` is needed for this application.

Consult Google for help with changing your terminal font :)
