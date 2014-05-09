#!/bin/sh

if [ ! -d "Ultros" ]; then
    echo "** Creating virtualenv.. **"
    pip install virtualenv
    virtualenv Ultros

    echo "** Activating virtualenv.. **"
    source Ultros/bin/activate

    echo "** Installing packages.. **"
    python packages.py setup
else
    echo "** Activating virtualenv.. **"
    source Ultros/bin/activate
fi

echo "**Starting Ultros.. **"
python run.py

echo "**Deactivating virtualenv.. **"
deactivate