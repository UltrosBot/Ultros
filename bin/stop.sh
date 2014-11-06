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

# OK, now issue a standard kill signal.

PID=$(cat ultros.pid)

echo "Stopping process.."

kill $PID

echo "Waiting 15 seconds for process to terminate.."
echo ""

# Wait ten seconds for it to be killed.

sleep 15

# If it wasn't killed, we'd better kill it.

if ps -p $PID > /dev/null
then
    echo "Process didn't die, killing forcibly..."
    echo ""
    kill -9 $PID
    sleep 2

    # If the process didn't die, we should notify the admin
    if ps -p $PID > /dev/null
    then
        echo "We weren't able to kill the process."
        echo "Please attempt to do so yourself."
        echo ""
        echo "PID: $PID"
    fi

    # Output the latest logs

    echo ""
    echo "====== LATEST LOG ======"
    echo ""

    tail -n20 logs/output.log
fi