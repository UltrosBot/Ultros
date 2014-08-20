#!/bin/sh

touch __init__.py

if [ $# -eq 0 ]
then
    pydoctor --add-package=. --docformat=restructuredtext --project-name=Ultros --project-url=https://ultros.io
else
    pydoctor --add-package=. --docformat=restructuredtext --project-name=Ultros --project-url=https://ultros.io $@
fi

rm __init__.py
