cd ..
python C:\Python27\Tools\i18n\pygettext.py -k __ *.py */*.py */*/*.py */*/*/*.py
cd translations
mv ../messages.pot .