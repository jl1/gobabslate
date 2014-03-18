#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setuptranslations.py

Generate and manipulate translation files for a flask app that uses flask-babel
Assumes areas in jinja2 templates and source code are marked with
{% trans %}..{% endtrans %} or gettext, _, or other gettext variants.

Related: flask, flask-babel, pybabel, jinja2, i18n, gobabslate

Outline of script:
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

app_name = 'default_app'

pybabel_extract = ['pybabel', 'extract',
                   '-F' 'babel.cfg',
                   '-o' 'messages.pot',
                   '.']
pybabel_init_lang = ['pybabel', 'init',
                     '-i' 'messages.pot',
                     '-d', app_name + '/translations',
                     '-l']
pybabel_compile = ['pybabel', 'compile', '-d', app_name + '/translations']

default_languages = ['fr', 'de']


def get_language_codes():
    try:
        app = __import__(app_name)
        languages = app.config.LANGUAGES.keys()
        language_default = app.config.LANGUAGE_DEFAULT
        return [lang for lang in languages if lang != language_default]
    except:
        print('Suitable config not found, using default languages')
        return default_languages


def return_code(args):
    return Popen(args).communicate()[0]


def is_destination_line(line):
    return line == u'msgstr ""\n'

def is_start_of_input(line):
    return line == u'msgid ""\n' or line[:7] == u'msgid "'

def is_fuzzy(line):
    return '#, fuzzy\n' == line

def escape_quotes(line):
    return line.replace('"', '\\"')

def write_new_line(line, data, lang, file_output):
    file_output.write(prepare_output_data(translate_data(data, lang)))

def translate_data(data, lang):
    return Goslate().translate(data, lang)

def prepare_output_data(data):
    return u'msgstr "' + escape_quotes(data) + u'"\n'

def prepare_input_line(line):
    return line[7:].strip().strip('"').replace('\\"', '"')

def clean_input_line(line):
    return line.replace('\n',  ' ')\
               .replace('\\n"', ' ')\
               .strip('"')\
               .replace('\\"', '"')

def record_input_line(line):
    return u'' if line == u'msgid ""\n' else prepare_input_line(line)

def process_babel_file(lang, remove_fuzzy=False):
    gs = Goslate()
    filename = app_name + '/translations/' + lang + '/LC_MESSAGES/messages.po'
    file_input = codecs.open(filename, 'r', 'utf-8')
    file_output = codecs.open(filename + '.tmp', 'w', 'utf-8')
    finding_input, data = False, u''
    for line in file_input:
        if is_destination_line(line) and finding_input:
            finding_input = False
            write_new_line(line, data, lang, file_output)
            continue
        elif finding_input is True:
            data += clean_input_line(line)
        elif is_start_of_input(line):
            finding_input = True
            data = record_input_line(line)
        elif is_fuzzy(line) and remove_fuzzy:
            continue
        file_output.write(line)
    file_input.close()
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
