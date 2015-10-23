#!/bin/bash

# First, make sure we're in the right place.
# This takes care of symlinks and such, too.

pushd . > /dev/null
SCRIPT_PATH="${BASH_SOURCE[0]}";

if ([ -h "${SCRIPT_PATH}" ])
 then
  while([ -h "${SCRIPT_PATH}" ])
   do cd `dirname "$SCRIPT_PATH"`; SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi

cd `dirname ${SCRIPT_PATH}` > /dev/null
SCRIPT_PATH=`pwd`;
popd  > /dev/null
cd $SCRIPT_PATH/../

mkdir -p logs/update/

echo "Pulling changes.."

git pull &> logs/update/git.log

if [ $? -ne 0 ]; then
    echo ""
    echo "Unable to pull changes."
    echo ""
    echo "== LOGS =="
    tail -n20 logs/update/git.log
    exit 1
fi

echo "Installing new modules.."

python packages.py setup &> logs/update/modules.log

if [ $? -ne 0 ]; then
    echo ""
    echo "Unable to install new modules."
    echo ""
    echo "== LOGS =="
    tail -n20 logs/update/modules.log
    exit 1
fi

echo "Updating pacakges.."

python packages.py update all &> logs/update/packages.log

if [ $? -ne 0 ]; then
    echo ""
    echo "Unable to update packages."
    echo ""
    echo "== LOGS =="
    tail -n20 logs/update/packages.log
    exit 1
fi

echo "Updated successfully."