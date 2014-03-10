#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setuptranslations.py

Generate and manipulate translation files for a flask app.
Assumes areas in jinja2 templates are marked with {% trans %}..{% endtrans %}
or gettext, _, or other gettext variants.
Related: flask, flask-babel, pybabel, jinja2, i18n, gobabslate
    1. Run pybabel with extract option
        pybabel extract -F babel.cfg -o messages.pot .
    2. Run pybabel with init option for each language
        pybabel init -i messages.pot -d translations -l fr
        pybabel init -i messages.pot -d translations -l de
    3. Pull translations from Google Translate API into babel files
    4. Remove #fuzzy from message.po files.
    5. Run pybabel with compile option
        pybabel compile -d translations
"""
import sys
import codecs
from subprocess import Popen
from goslate import Goslate

pybabel_extract = ['pybabel', 'extract', '-F' 'babel.cfg',
                                         '-o' 'messages.pot', '.']
pybabel_init_lang = ['pybabel', 'init', '-i', 'messages.pot',
                                        '-d', 'translations', '-l']
pybabel_compile = ['pybabel', 'compile', '-d', 'translations']


def get_language_codes():
    try:
        from config import LANGUAGES, LANGUAGE_DEFAULT
        return [lang for lang in LANGUAGES.keys() if lang != LANGUAGE_DEFAULT]
    except:
        return ['fr', 'de']


def return_code(args):
    return Popen(args).communicate()[0]


def process_babel_file(lang, remove_fuzzy=False):
    gs = Goslate()
    filename = 'translations/' + lang + '/LC_MESSAGES/messages.po'
    file_stream = codecs.open(filename,          'r', 'utf-8')
    file_output = codecs.open(filename + '.tmp', 'w', 'utf-8')
    finding_input, data = False, u''
    for line in file_stream:
        if finding_input is True and line == u'msgstr ""\n':
            finding_input = False
            new_text = gs.translate(data, lang).replace('"', '\\"')
            file_output.write(u'msgstr "' + new_text + u'"\n')
            continue
        elif finding_input is True:
            data += line.replace('\n', ' ').replace('\\n"', ' ').strip('"')\
                        .replace('\\"', '"')
        elif line == u'msgid ""\n' or line[:7] == u'msgid "':
            finding_input = True
            data = u'' if line == u'msgid ""\n' else line[7:].strip()\
                .strip('"').replace('\\"', '"')
        elif line == '#, fuzzy\n' and remove_fuzzy:
            continue
        file_output.write(line)
    file_stream.close()
    file_output.close()
    Popen(['cp', filename + '.tmp', filename]).communicate()


def main():
    if return_code(pybabel_extract) is not None:
        sys.exit('pybabel failed to extract translations')
    for language_code in get_language_codes():
        if return_code(pybabel_init_lang + [language_code]) is not None:
            print('Failed to add language: %s', language_code)
            continue
        process_babel_file(language_code, remove_fuzzy=True)
    if return_code(pybabel_compile) is not None:
        sys.exit('pybabel was unable to compile translations')

if __name__ == '__main__':
    main()
