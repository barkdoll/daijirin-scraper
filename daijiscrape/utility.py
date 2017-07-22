# -*- coding: utf-8 -*-
#
# Copyright 2014-2017 Stefan van den Akker <neftas@protonmail.com>
#
# This file is part of Power Format Pack.
#
# Power Format Pack is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Power Format Pack is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with Power Format Pack. If not, see http://www.gnu.org/licenses/.

"""
Utility module with helper functions that are needed throughout the addon.
"""

import base64
import os
import re
import string
import time

import BeautifulSoup
from anki.utils import intTime, json, isMac
from aqt.utils import isWin
from PyQt4 import QtGui

import const
import markdown
import preferences
from html2text import html2text
from html2text_overrides import escape_md_section_override
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.smart_strong import SmartEmphasisExtension
from markdown.extensions.tables import TableExtension
from power_format_pack.python_modules import ConfigParser
from prefhelper import PrefHelper


def validate_key_sequence(sequence, platform=u""):
    """
    Check a string that contains a key sequence and determine whether it
    fulfills the key sequence contract: one non-modifier key, and optionaly
    one or more modifier keys. Return a prettified key sequence when the
    key sequence is valid, or else an empty string.
    >>> validate_key_sequence(u"Alt-ctrl-Q")
    u'ctrl+alt+q'
    """

    if not sequence:
        return u""

    # assert isinstance(sequence, unicode), "Input `sequence` not in Unicode"

    modkeys = const.KEY_MODIFIERS
    # Mac OS X has a special modifier, the Cmd key
    if isMac or platform == "darwin":
        modkeys += const.KEY_MODIFIERS_MACOSX
    sequence = sequence.lower()
    # the plus and minus signs can also be part of the key sequence
    # not just serve as delimiters
    if any(sequence.endswith(c) for c in u"+-"):
        parts = split_string(sequence[:-1], u"+-")
        parts += list(sequence[-1:])
    else:
        parts = split_string(sequence, u"+-")
    parts = filter_duplicates(parts)
    # sequence can only contain one function key and cannot be used
    # in combination with a character key
    function_key_found = False
    char_key_found = False
    for word in parts:
        if word in const.KEYS_SEQUENCE:
            # f12+a
            if function_key_found:
                return u""
            char_key_found = True
        if word in const.FUNCTION_KEYS:
            # f12+f11 or a+f12
            if function_key_found or char_key_found:
                return u""
            function_key_found = True
    # sequence should contain at least one non-modifier key
    if all(word in modkeys for word in parts):
        return u""
    for word in parts:
        # unknown modifiers or non-modifiers are not allowed
        if word not in modkeys + const.KEYS_SEQUENCE + const.FUNCTION_KEYS:
            return u""

    return create_pretty_sequence(parts)


def create_pretty_sequence(sequence):
    """
    Return an ordered string created from a key sequence that contains
    modifier and non-modifier keys. The returned order is ctrl, meta,
    shift, alt, non-modifier.
    
    >>> create_pretty_sequence(["meta", "alt", "ctrl", "i"])
    u'ctrl+meta+alt+i'
    """

    if not sequence:
        return u""

    seq = sequence[:]
    pretty_sequence = list()
    if u"ctrl" in sequence:
        seq.remove(u"ctrl")
        pretty_sequence.append(u"ctrl")
    if u"meta" in sequence:
        seq.remove(u"meta")
        pretty_sequence.append(u"meta")
    if u"shift" in sequence:
        seq.remove(u"shift")
        pretty_sequence.append(u"shift")
    if u"alt" in sequence:
        seq.remove(u"alt")
        pretty_sequence.append(u"alt")
    pretty_sequence += seq

    return u"+".join(x for x in pretty_sequence if x)


def check_user_keybindings(default_keybindings, user_keybindings, platform=u""):
    """
    Check the correctness of the user keybindings. If not correct, the
    default binding will be used instead. Return a checked dictionary of
    valid keybindings.
    """

    validated_keybindings = dict()
    for key, value in user_keybindings.iteritems():
        # assert isinstance(key, unicode), "Key `{!r}` is not Unicode".format(key)
        # assert isinstance(value, unicode), "Value `{!r}` is not Unicode".format(value)
        val_binding = validate_key_sequence(value, platform)
        if not val_binding:
            validated_keybindings[key] = default_keybindings.get(key)
        else:
            validated_keybindings[key] = val_binding

    return validated_keybindings


def get_keybinding(keybindings, name_of_key):
    """
    Return the keybinding indicated by `name_of_key`, and capitalize
    the name of each key before the delimiter `+`.
    
    >>> get_keybinding({u"test": u"ctrl+alt+esc"}, u"test")
    u'Ctrl+Alt+Esc'
    """
    keybinding = keybindings.get(name_of_key, u"")
    return string.capwords(keybinding, u"+")


def strip_html_from_markdown(org_html, keep_empty_lines=False):
    """
    Take an `org_html` string and return a Markdown string. Empty lines are
    removed from the result, unless `keep_empty_lines` is set to `True`.
    
    >>> strip_html_from_markdown(u"<p>this <strong>was</strong> a <em>triumph</em>!</p>")
    u'this **was** a _triumph_!\\n'
    """

    if not org_html:
        return u""

    # assert isinstance(org_html, unicode), "Input `org_html` is not Unicode"

    # disable the escaping of Markdown-sensitive characters
    html2text.escape_md_section = escape_md_section_override
    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    md_text = h2t.handle(org_html)
    clean_md = u""
    if keep_empty_lines:
        clean_md = md_text
    else:
        # remove white lines
        for line in md_text.split(u"\n"):
            if line:
                clean_md += (line + u"\n")

    # undo the html2text escaping of dots (which interferes
    # with the creation of ordered lists)
    dot_regex = re.compile(ur"(\d+)\\(\.\s)")
    clean_md = re.sub(dot_regex, ur"\g<1>\g<2>", clean_md)

    # this is needed to keep inner parentheses and whitespace in links and
    # images from prematurely ending the Markdown syntax; e.g.
    # ![](image (1).jpg) would otherwise break on the whitespace in the
    # filename and the inner parentheses, so we change it to
    # ![](image&#32;&#40;1&#41;.jpg) to prevent this from happening
    left_paren_regex = re.compile(ur"\\\(")
    clean_md = replace_link_img_matches(
            left_paren_regex, u"&#40;", clean_md)
    right_paren_regex = re.compile(ur"\\\)")
    clean_md = replace_link_img_matches(
            right_paren_regex, u"&#41;", clean_md)
    whitespace_regex = re.compile(ur"\s+")
    clean_md = replace_link_img_matches(
            whitespace_regex, u"&#32;", clean_md)

    # assert isinstance(clean_md, unicode)
    return clean_md


def get_indices(haystack, needle, needle_end=u""):
    """
    Return a list of lists with the start and end positions of the
    needle(s).
    >>> get_indices(u"just `a` sentence", u"`")
    [[5, 7]]
    >>> get_indices(u"another `sentence", u"`")
    [[8, -1]]
    """
    positions = list()
    if not needle_end:
        needle_end = needle
    start = haystack.find(needle)
    while start != -1:
        end = haystack.find(needle_end, start + 1)
        if end == -1:
            positions.append([start, -1])
            break
        else:
            positions.append([start, end])
            start = haystack.find(needle, end + 1)
    return positions


def filter_indices(positions1, positions3):
    """
    Mark overlaps with code blocks in inline code blocks. `positions1` is
    a list of list with start and end points of inline code blocks
    [[0, 2], [5, 7]]. `positions3` is a list of lists with start and end
    point of fenced code blocks. Modifies `position1` in place. Return `None`.
    
    >>> positions1 = [[2, 5]]
    >>> positions3 = [[5, 10]]
    >>> filter_indices(positions1, positions3)
    >>> positions1[0][1] == -1
    True
    """
    for pos3 in positions3:
        for pos1 in positions1:
            # a ```code `block` what``` are
            if pos3[0] > -1 and pos3[1] > -1:
                if (pos3[0] + 2) <= pos1[0] and pos3[1] >= pos1[1]:
                    pos1[0] = pos1[1] = -1
                    continue
            # a `word ```
            if pos3[0] > -1 and pos3[0] >= pos1[0] and pos3[0] <= pos1[1]:
                pos1[1] = -1
            # ``` word`
            if pos3[1] > -1 and pos3[1] <= pos1[1] and (pos3[1] + 2) >= pos1[0]:
                pos1[0] = -1

    return None


def replace_link_img_matches(regex, new, s):
    """
    Escape characters in Markdown image links that may break in regular HTML.

    >>> replace_link_img_matches(re.compile(ur"\s+"), u"&#32;", u"![](i .jpg)")
    u'![](i&#32;.jpg)'

    >>> replace_link_img_matches(re.compile(ur"\s+"), u"&#32;", u"![this `was a` triumph](i am making)")
    u'![this `was a` triumph](i&#32;am&#32;making)'
    """

    # assert isinstance(s, unicode), "Input `s` is not Unicode"

    # don't escape anything when we're in a (inline) code block
    positions1 = get_indices(s, "`")
    positions3 = get_indices(s, "```")
    filter_indices(positions1, positions3)
    positions_combined = filter(lambda x: x[0] > -1 and x[1] > -1,
                                positions1 + positions3)

    result = re.finditer(const.IS_LINK_OR_IMG_REGEX, s)
    if result:
        for match in result:
            # see if match is inside a code block
            skip = False
            start_match, end_match = match.span()
            for (start_code, end_code) in positions_combined:
                if start_match >= start_code and end_match <= end_code:
                    skip = True
                    break

            if not skip:
                str_to_be_replaced = match.group(1)
                start = s.find(str_to_be_replaced)
                end = start + len(str_to_be_replaced)
                replacement = re.sub(regex, new, str_to_be_replaced)
                # put string back in original string
                str_start = s[:start]
                str_end = s[end:]
                s = str_start + replacement + str_end

    # assert isinstance(s, unicode), "Result `s` is not Unicode"

    return s


def convert_clean_md_to_html(md, put_breaks=False):
    """
    Convert a string containing Markdown syntax to a string with HTML that
    Anki expects.
    """

    # assert isinstance(md, unicode), "Input `md` is not Unicode"

    result = u"<div>"
    location_last_nbsp = -999999999  # take an unlike large previous occurence
    last_char = u""
    for index, char in enumerate(md):
        if char == u"\n":
            result += u"</div><div>"
        elif char == " ":
            if (index - location_last_nbsp) == 1:
                result += char
            else:
                if last_char == u"\n" or last_char in u" ":
                    result += u"&nbsp;"
                    location_last_nbsp = index
                else:
                    result += char
        else:
            result += char
        last_char = char
    # remove last opening <div> tag
    if result.endswith(u"<div>"):
        result = result[:(len(result) - len(u"<div>"))]
    # or add a closing <div> tag
    else:
        result += u"</div>"

    # <div></div> needs to be a visible empty line
    if put_breaks:
        soup = BeautifulSoup.BeautifulSoup(result)
        for elem in soup.findAll(u"div"):
            if not elem.contents:
                elem.append(BeautifulSoup.Tag(soup, u"br"))
        result = unicode(soup)
        soup = None

    # remove "empty" lines that consist solely of (non-breakable) spaces
    soup = BeautifulSoup.BeautifulSoup(result)
    for elem in soup.findAll("div"):
        if elem.string is not None:
            if all(x in ("&nbsp;", " ") for x in elem.string.split()):
                elem.setString(BeautifulSoup.Tag(soup, "br"))
    result = unicode(soup)

    # assert isinstance(result, unicode), "Result `result` is not Unicode"
    return result


def convert_markdown_to_html(clean_md):
    """
    Take a string `clean_md` and return a string where the Markdown syntax is
    converted to HTML.
    
    >>> preferences.PREFS = {"markdown_classful_pygments": True, "markdown_syntax_style": "tango", "markdown_line_nums": False}
    >>> convert_markdown_to_html(u"this **was** a triumph")
    u'<p>this <strong>was</strong> a triumph</p>'
    """

    # assert isinstance(clean_md, unicode), "Input `clean_md` is not Unicode"

    new_html = markdown.markdown(clean_md, output_format="xhtml1",
        extensions=[
            SmartEmphasisExtension(),
            FencedCodeExtension(),
            FootnoteExtension(),
            AttrListExtension(),
            DefListExtension(),
            TableExtension(),
            AbbrExtension(),
            Nl2BrExtension(),
            CodeHiliteExtension(
                noclasses=not preferences.PREFS.get(const.MARKDOWN_CLASSFUL_PYGMENTS),
                pygments_style=preferences.PREFS.get(const.MARKDOWN_SYNTAX_STYLE),
                linenums=preferences.PREFS.get(const.MARKDOWN_LINE_NUMS)),
            SaneListExtension()
        ], lazy_ol=False)

    # assert isinstance(new_html, unicode)

    return new_html


def is_same_html(html_one, html_two):
    """
    Return `True` when `html_one` is the same as `html_two`, `False` otherwise.
    """
    # assert isinstance(html_one, unicode), "Input `html_one` is not Unicode"
    # assert isinstance(html_two, unicode), "Input `html_two` is not Unicode"
    return html_one == html_two


def is_same_markdown(md_one, md_two):
    """
    Return `True` when `md_one` is the same as `md_two`, `False` otherwise.
    
    >>> md_one = u"this **was** a triumph\\n"
    >>> md_two = u"this   **was**   a   triumph   \\n"
    >>> is_same_markdown(md_one, md_two)
    True
    """
    # assert isinstance(md_one, unicode), "Input `md_one` is not Unicode"
    # assert isinstance(md_two, unicode), "Input `md_two` is not Unicode"
    compare_one = remove_white_space(md_one)
    compare_two = remove_white_space(md_two)
    return compare_one == compare_two


def is_same_text(text_one, text_two):
    """
    Return `True` when `text_one` is the same as `text_two`, `False` otherwise.
    """

    # assert isinstance(text_one, unicode), "Input `text_one` is not Unicode"
    # assert isinstance(text_two, unicode), "Input `text_two` is not Unicode"
    return text_one == text_two


def remove_white_space(s):
    """
    Return a string that is equal to string `s`, but has all whitespace removed
    from it.
    
    >>> remove_white_space(u"this\\nwas\\ta    triumph")
    u'thiswasatriumph'
    """

    # assert isinstance(s, unicode), "Input `s` is not Unicode"

    return u"".join(char for char in s if not char.isspace())


def markdown_data_to_json(unique_id, isconverted, md):
    """
    Return a dictionary with information that is needed for the database.
    """

    # assert isinstance(md, unicode), "Input `md` is not Unicode"

    return  {
                "id": unique_id,
                "isconverted": isconverted,
                "md": md,
                "lastmodified": intTime()
            }


def merge_dicts(existing, new):
    """
    Merge two dictionaries. The values from `new` dictionary take precedence
    over the values from the `existing` dictionary where there are duplicate
    keys. Return a dictionary that contains the key-value pairs from both
    dicts.
    
    >>> a = {u"a": 1, u"b": 2}
    >>> b = {u"b": -1, u"c": 3}
    >>> ret = merge_dicts(a, b)
    >>> ret["b"] == -1
    True
    """

    return dict(existing.items() + new.items())


def json_dump_and_compress(data):
    """
    Take a string `data` and JSONify it. Return the resultant string, encoded
    in base64.
    """

    encoded = unicode(base64.b64encode(json.dumps(data)))
    # assert isinstance(encoded, unicode), "Output `encoded` is not Unicode"
    return encoded


def decompress_and_json_load(data):
    """
    Decode a base64-encoded string and return a string that is valid JSON.
    """

    if not data:
        return u""

    # assert isinstance(data, unicode), "Input `data` is not Unicode"

    try:
        decoded = base64.b64decode(data)
    except (TypeError, UnicodeEncodeError) as e:
        # `data` is not a valid base64-encoded string
        print e  # TODO: should be logged
        return "corrupted"

    try:
        ret = json.loads(decoded)
        return ret
    except ValueError as e:
        print e  # TODO: should be logged
        return "corrupted"


def wrap_string(at_start, a_string, at_end):
    """
    Return a string `a_string` that has the `at_start` string prepended and
    the `at_end` string appended to it.
    >>> wrap_string("a", "b", "c")
    'abc'
    """
    return at_start + a_string + at_end


def concat(a, b):
    """
    Concatenate two Unicode strings to each other.
    
    >>> concat(u"a", u"b")
    u'ab'
    """
    return a + b


def insert_md_data(unique_id, isconverted, md, html):
    """
    Creates a HTML string that contains the Markdown data needed for reversion.
    Returns the input `html` string with the Markdown data appended.
    """
    md_dict = markdown_data_to_json(unique_id, isconverted, md)
    md_dict_compr = json_dump_and_compress(md_dict)
    wrapped_md_dict_compr = wrap_string(const.START_HTML_MARKER,
                                        md_dict_compr,
                                        const.END_HTML_MARKER)
    return concat(html, wrapped_md_dict_compr)


def get_md_data_from_string(html):
    """
    Read a string `html` and extract compressed Markdown data from it, if
    it is available. Return a dictionary that contains this data, otherwise
    return the empty string.
    """
    if not html:
        return u""
    # assert isinstance(html, unicode), "Input `html` is not Unicode"
    if const.START_HTML_MARKER not in html:
        return u""
    start = html.find(const.START_HTML_MARKER) + len(const.START_HTML_MARKER)
    end = html.find(const.END_HTML_MARKER, start)
    if start == -1 or end == -1:
        return u""
    compr_str = html[start:end]
    return compr_str


def create_counter(start=0, step=1):
    """
    Generator that creates infinite numbers. `start` indicates the first
    number that will be returned, `step` the number that should be added
    or subtracted from the previous number on subsequent call to the
    generator.
    
    >>> c = create_counter(10, 2)
    >>> c.next()
    10
    >>> c.next()
    12
    """
    num = start
    while True:
        yield num
        num += step


def escape_html_chars(s):
    """
    Escape HTML characters in a string. Return a safe string.
    >>> escape_html_chars(u"this&that")
    u'this&amp;that'
    >>> escape_html_chars(u"#lorem")
    u'#lorem'
    """
    if not s:
        return u""

    # assert isinstance(s, unicode), "Input `s` is not Unicode"

    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }

    result = u"".join(html_escape_table.get(c, c) for c in s)
    # assert isinstance(result, unicode)
    return result


def get_alignment(s):
    """
    Return the alignment of a table based on input `s`. If `s` not in the
    list, return the default value.
    >>> get_alignment(u":-")
    u'left'
    >>> get_alignment(u":-:")
    u'center'
    >>> get_alignment(u"-:")
    u'right'
    >>> get_alignment(u"random text")
    u'left'
    """
    # assert isinstance(s, unicode), "Input is not Unicode"
    alignments = {u":-": u"left", u":-:": u"center", u"-:": u"right"}
    default = u"left"
    if s not in alignments:
        return default
    return alignments[s]


def check_size_heading(s):
    """
    Determine by counting the number of leading hashes in the string the
    size of the heading. Return an int that is the length of the hashes,
    or -1 if no hashes were found at the beginning of the string.
    
    >>> check_size_heading(u"######heading")
    6
    >>> check_size_heading(u"lorem ipsum")
    -1
    >>> check_size_heading(u"lorem #ipsum")
    -1
    >>> check_size_heading(u"    ##lorem")
    2
    >>> check_size_heading(u"# # # #lorem")
    1
    """
    # assert isinstance(s, unicode), "Input is not Unicode"
    # HTML headers go from <h1> to <h6>
    regex = re.compile(ur"^(#{1,6})")
    s = s.strip()
    if s.startswith(u"#"):
        size_heading = len(regex.match(s).group(1))
        return size_heading
    else:
        return -1


def strip_leading_whitespace(s):
    """
    Remove leading whitespace from a string `s`. Whitespace is defined as
    a space, a tab, linefeed, return, formfeed, vertical tab or a
    non-breakable space.
    
    >>> strip_leading_whitespace(u" This")
    u'This'
    >>> strip_leading_whitespace(u"\\tThis")
    u'This'
    >>> strip_leading_whitespace(u"\\nThis")
    u'This'
    >>> strip_leading_whitespace(u"\\rThis")
    u'This'
    >>> strip_leading_whitespace(u"&nbsp;This")
    u'This'
    >>> strip_leading_whitespace(u"\\n\\t\\r      &nbsp;     And")
    u'And'
    """
    # assert isinstance(s, unicode), "Input is not Unicode"
    if not s:
        return s
    while True:
        if any(s.startswith(c) for c in string.whitespace):
            s = s.lstrip()
        elif s.startswith(u"&nbsp;"):
            s = s.lstrip(u"&nbsp;")
        else:
            break
    return s


def create_horizontal_rule():
    """
    Returns a QFrame that is a sunken, horizontal rule.
    """
    frame = QtGui.QFrame()
    frame.setFrameShape(QtGui.QFrame.HLine)
    frame.setFrameShadow(QtGui.QFrame.Sunken)
    return frame


def unescape_html(html):
    """
    Unescapes escaped HTML sequences.
    >>> unescape_html(u"&amp;")
    u'&'
    """
    return const.HTML_PARSER.unescape(html)


def start_safe_block(hashmap):
    """
    Mark the start of a safe block for the onFocus event.
    """
    if not all(key in hashmap for key in (u"start_time", u"safe_block")):
        return None
    hashmap[u"safe_block"] = True
    hashmap[u"start_time"] = time.time()


def end_safe_block(hashmap):
    """
    Mark the end of a safe block for the onFocus event.
    """
    if not all(key in hashmap for key in (u"start_time", u"safe_block")):
        return None
    hashmap[u"safe_block"] = False


def remove_whitespace_before_abbreviation_definition(md):
    """
    Remove the two leading spaces that are put by `html2text` when it
    translates an HTML abbreviation to Markdown.
    """
    if not md:
        return md
    # assert isinstance(md, unicode), "Input `md` is not Unicode"
    regex = re.compile(r"( |\&nbsp;)+(\*\[[^]]*\]:)")
    return re.sub(regex, r"\2", md)


def remove_leading_whitespace_from_dd_element(md, add_newline=False):
    """
    Change the input `md` to make sure it will transform to the correct HTML.
    """
    if not md:
        return md
    # assert isinstance(md, unicode), "Input `md` is not Unicode"
    markdown = md
    regex = re.compile(r"(\n) {4}(: .*?\n)")
    result = re.findall(regex, markdown)
    replacement = r"\1\2\n" if add_newline else r"\1\2"
    markdown = re.sub(regex, replacement, markdown, count=(len(result)-1))
    markdown = re.sub(regex, r"\1\2", markdown)
    return markdown


def put_colons_in_html_def_list(html):
    """
    Insert colons as the first child of a `<dd>` tag.
    """
    # assert isinstance(html, unicode), "Input `html` is not Unicode"
    if not html:
        return html
    soup = BeautifulSoup.BeautifulSoup(html)
    dds = soup.findAll(name="dd")
    for dd in dds:
        # catch rare cases when `<dd>` is defined, but `<dt>` not
        prevSib = dd.previousSibling
        while unicode(prevSib) == u"\n":
            prevSib = prevSib.previousSibling
        if (prevSib is None or prevSib.name != u"dt"):
            continue
        dd.insert(0, u": ")
    return unicode(soup)


def filter_duplicates(sequence):
    """
    Return a list of elements without duplicates. The order of the
    original collection may be changed in the returned list.
    """
    if not sequence:
        return list()
    return list(set(sequence))


def split_string(text, splitlist):
    """
    Change all separators defined in a string `splitlist` to the first
    separator in `splitlist` and then split the text on that one separator.
    Return a list with the original string if `splitlist` is the empty
    string or `None`. Return a list of strings, with no empty strings in it.
    >>> splitlist = u"@#$"
    >>> s = u"one@two#three$"
    >>> split_string(s, splitlist)
    [u'one', u'two', u'three']
    """

    # assert isinstance(text, unicode), "Input `text` is not Unicode"
    # assert isinstance(splitlist, unicode), "Input `splitlist` is not Unicode"

    if not splitlist:
        return [text]
    for sep in splitlist:
        text = text.replace(sep, splitlist[0])
    return [x for x in text.split(splitlist[0]) if x]


def downArrow():
    if isWin:
        return u"▼"
    # windows 10 is lacking the smaller arrow on English installs
    return u"▾"


def get_config_parser(path=None):
    """
    Return a RawConfigParser for the specified path.
    """
    if path is None:
        path = os.path.join(PrefHelper.get_addons_folder(),
                            const.FOLDER_NAME,
                            const.CONFIG_FILENAME)
    config = ConfigParser.ConfigParser()
    ret = config.read(path)
    if not ret:
        raise Exception("Could not read config file {!r}".format(path))
    return config


def set_tool_tip(elem, tip):
    """
    Set a "rich-text" tool tip for `elem`, as that will trigger automatic
    word-wrap in Qt.
    """
    elem.setToolTip("<font>" + tip + "</font>")
