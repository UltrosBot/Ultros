@ECHO off

IF EXIST Ultros GOTO :INSTALLED

echo ** Creating virtualenv.. **
pip install virtualenv
virtualenv Ultros

echo "** Activating virtualenv.. **"
Ultros/Scripts/activate

echo "** Installing packages.. **"
python packages.py setup

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