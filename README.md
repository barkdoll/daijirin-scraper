# Daijirin Scraper | 大辞林 スクレーパー
## Purpose of this script
To scrape dictionary definition data from [weblio.jp](http://www.weblio.jp/) for definitions from the all-wonderful 三省堂 大辞林 (Daijirin), a monolingual Japanese dictionary. It then parses the proper HTML to it for use with my proprietary Anki definition template (CSS stylesheet for this template will be available when I get closer to finishing the add-on).

## Goals for this project
This is my first script written in Python. I would like to eventually create a GUI in PyQt so that it can be bundled and shipped directly into Anki as a shared add-on.

## Now
Right now it can be ran through the Python 3 interpreter and scrape for a word passed in as an argument immediately following the script. Tested with Python 3.6.1

## Third-party modules used in this script
* BeautfulSoup4
* urllib.request
* urllib.parse
* sys

### Warning: this add-on will only support single-level nested definitions. 
It will not support multi-level nested definitions. At that point, I think you would be doing yourself a disservice listing out an entire definition on a flash card. Also, with Weblio's terrible web architecture, the means by which creating something that could extract multi-level nests would be taxing, and I need to move on to other things (like studying Japanese and building more tools to help with language study). You should be able to find the one or two specific definitions that the word is utilizing in the sentence's context, and copy those manually into your card.
