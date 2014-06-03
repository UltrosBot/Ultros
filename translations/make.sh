#!/bin/sh
cd ..
pygettext.py -k __ *.py */*.py */*/*.py */*/*/*.py
cd translations
mv ../messages.pot .