.. _installation:

Installation
============

Ultros requires the following for its basic functions:

* Python 2.6 or 2.7 32-bit (NOT 64-bit as some libraries don't support it yet)
    * Twisted
    * Zope.Interface
    * Kitchen
    * Yapsy 1.10.2 (Specifically, as they keep changing their API)
    * PyYAML
* Optionally, the following are required for some core features
    * To support SSL in protocols:
        * PyOpenSSL
    * For the Mumble protocol:
        * Google Protobuf
    * For the URLs plugin:
        * BeautifulSoup 4
        * Netaddr

.. _downloading:

Downloading Ultros
------------------

We highly recommend you use Git to download Ultros, as it allows you to easily keep it up to date,
without worrying about patching or moving files around.

* For Windows, you can install MSysGit here (Allow it to install to System32): https://code.google.com/p/msysgit/downloads/detail?name=Git-1.9.0-preview20140217.exe
    * Where I mention a terminal below, you can use "Git Bash" from your start menu.
* On Linux, install Git from your package manager.

Next, open a terminal and run the following commands:

.. code:: bash
    cd <path>  # Replace <path> with the directory you want to store Ultros in
    git clone https://github.com/UltrosBot/Ultros.git
    cd Ultros

You will now have a full copy of Ultros, just waiting to be set up!

To update Ultros in future, simply do the following:

.. code:: bash
    cd <path>/Ultros  # Replace <path> with the directory from above
    git pull --rebase

If you're thick-skulled, paranoid about wasting space or just don't like Git, you can download a zipball from the site_, but you will have to keep it up-to-date manually.

Please see below for OS-specific installation instructions.

.. _installation-windows:

Windows
-------

* Download and install Python 2.7.6: https://www.python.org/ftp/python/2.7.6/python-2.7.6.msi
* Add Python to your PATH: http://www.anthonydebarros.com/2011/10/15/setting-up-python-in-windows-7/
* Install pip by downloading and running this script (Just copy it into a file ending in .py and run it): https://raw.github.com/pypa/pip/master/contrib/get-pip.py
* Download and install Twisted: http://twistedmatrix.com/Releases/Twisted/13.2/Twisted-13.2.0.win32-py2.7.msi
* If you require SSL support:
    * Download and install OpenSSL for Windows: http://slproweb.com/download/Win32OpenSSL-1_0_1f.exe
    * Download and install PyOpenSSL: https://pypi.python.org/packages/2.7/p/pyOpenSSL/pyOpenSSL-0.13.1.win32-py2.7.exe
    * You'll see some errors in the next step if you don't do this, but Ultros should still work just fine for things that don't need SSL.

Now, open a command prompt, and run the following (replacing **<path>** with the *path to wherever you downloaded Ultros*):

.. code:: batch

    cd <path>
    pip install -r requirements.txt

Once this is done, you can start Ultros. On Windows, you should never do this by double-clicking run.py, it's always much safer
to run it in a command prompt, so that you'll be able to shut Ultros down properly.

You may create a batch script using either of the below methods for starting Ultros.

To start Ultros normally:

.. code:: batch

    @ECHO off
    echo Starting Ultros..
    python run.py
    PAUSE

To start Ultros in debug mode:

.. code:: batch

    @ECHO off
    echo Starting Ultros in debug mode..
    python run.py --debug
    PAUSE

When you want to stop Ultros, instead of closing the window, **click on it and press CTRL+C to stop it gracefully**, and *then* close the window.
Due to some annoying quirks in Windows, if you don't do this, then Ultros may not have time to save all its data. If you do this and lose some
data, then it's not a bug, and we would appreciate if you would use the above method for stopping Ultros, instead of reporting it as one.

.. _installation-linux:

Linux
-----

As the superior operating system for hosting practically anything, we highly recommend you use Linux to host your bot
if you plan to keep it online for long periods of time. Linux also has a much easier setup, as follows.

* Install Python from your package manager.
    * Most package managers will install the latest version of Python 2, but some versions of Linux will install Python 3.
      Remember to check which version it installs!
* If you need SSL, remember to install the standard OpenSSL package from your package manger, as well as a compiler (such as gcc)
  and the Python development package.
    * You'll see some errors in the next step if you don't do this, but Ultros should still work just fine for things that don't need SSL.
* Use pip to install all of the required modules.

If you're on a recent version of Ubuntu or Debian, you should be able to do all of this in a method similar to the following, replacing <path> with the path
to your copy of Ultros.

.. code:: bash

    sudo apt-get install python python-dev openssl gcc
    cd <path>
    pip install -r requirements.txt

Naturally, you should replace the call to apt-get above with a call to your distro's package manager if you're not using Ubuntu or Debian.

Once you've done this, you can start Ultros using one of the following methods.

To start Ultros normally:

.. code:: bash

    cd <path>
    python run.py

To start Ultros in debug mode:

.. code:: bash

    cd <path>
    python run.py --debug

.. _installation-mac:

Mac OSX
-------

* First of all, you should install Homebrew, if you haven't already: http://brew.sh/
* Open Terminal.app and run the following:

.. code:: bash

    brew install python
    cd <path>  # Replace <path> with the directory you downloaded Ultros to
    pip install -r requirements.txt

That's it, you should be good to go!

To start Ultros normally:

.. code:: bash

    cd <path>
    python run.py

To start Ultros in debug mode:

.. code:: bash

    cd <path>
    python run.py --debug

.. _installation-configuration:

Configuration
-------------

For configuration, please see the :ref:`configuration` page.

.. _site: http://ultros.io