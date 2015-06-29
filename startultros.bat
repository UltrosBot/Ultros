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

GOTO :START

:START

pip install --upgrade certifi
for /f %i in ('python -m certifi') do set SSL_CERT_FILE=%i

echo "** Starting Ultros.. **"
python run.py %*

echo "** Updating.. **"
python run.py --update

echo "** Updating plugins.. **"
python packages.py update all --overwrite

GOTO :START

echo "** Deactivating virtualenv.. **"
deactivate