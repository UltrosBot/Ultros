#!/bin/sh

if [ $# -eq 0 ]
then
    pydoctor --add-package=. --docformat=restructuredtext
else
    pydoctor --add-package=. --docformat=restructuredtext $@
fi