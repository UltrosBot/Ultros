#!/bin/sh

touch __init__.py

if [ $# -eq 0 ]
then
    pydoctor --add-package=. --docformat=restructuredtext
else
    pydoctor --add-package=. --docformat=restructuredtext $@
fi

rm __init__.py