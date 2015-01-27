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

# Check if we're already running..

if [ -f ultros.pid ]; then
    PID=$(cat ultros.pid)

    if ps -p $PID > /dev/null
    then
        echo "Ultros is already running."
        echo "PID: $(cat ultros.pid)"
        echo ""
        echo "Please stop Ultros before trying to run it again."
        echo ""
        echo "If you're sure that this is in error, you may delete"
        echo "'ultros.pid' and try again, but we don't support this."

        exit 1
    fi
fi

# OK, now start the process.

echo "Starting process.."
echo ""

python -OO run.py &> logs/ultros.out &

# Remember to wait for the process to start before checking the pid.

sleep 2

echo "Ultros has been started."
echo "PID: $(cat ultros.pid)"

# Output the latest logs

echo ""
echo "====== LATEST LOG ======"
echo ""

tail -n20 logs/ultros.out
