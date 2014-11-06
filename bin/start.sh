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

# OK, now start the process.

echo "Starting process.."
echo ""

python run.py &> logs/ultros.out &

# Remember to wait for the process to start before checking the pid.

sleep 2

echo "Ultros has been started."
echo "PID: $(cat ultros.pid)"

# Output the latest logs

echo ""
echo "====== LATEST LOG ======"
echo ""

tail -n20 logs/output.log