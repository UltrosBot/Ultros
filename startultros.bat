@ECHO off

IF EXIST Ultros GOTO :INSTALLED

echo ** Creating virtualenv.. **
pip install virtualenv
virtualenv Ultros

echo "** Activating virtualenv.. **"
Ultros/Scripts/activate

echo "** Installing dependencies.. **"
python packages.py setup

echo "** Reinstalling packages.. **"
python packages.py update all

GOTO :START

:INSTALLED

echo "** Activating virtualenv.. **"
Ultros/Scripts/activate

GOTO :INSTALLED

:START

echo "**Starting Ultros.. **"
python run.py

echo "**Deactivating virtualenv.. **"
deactivate