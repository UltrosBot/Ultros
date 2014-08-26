#!/bin/sh

cp __init__._py __init__.py

if [ $# -eq 0 ]
then
    pydoctor --add-package=. --docformat=restructuredtext --project-name=Ultros --project-url=https://ultros.io --html-use-sorttable --html-use-splitlinks
else
    pydoctor --add-package=. --docformat=restructuredtext --project-name=Ultros --project-url=https://ultros.io --html-use-sorttable --html-use-splitlinks $@
fi

rm __init__.py
