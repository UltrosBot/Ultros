.. _installation:

Installation
============

Over time, Ultros' installation steps have changed significantly. Ultros attempts
to be as cross-platform as possible, but it would also be true that Ultros does
target Linux as its primary platform. Special instructions have been included for
other platforms below.

If you're just looking to set up your bot, please refer to the :ref:`configuration`
page.

.. _installation_requirements:

Requirements
============

Ultros' optimal environment requires the following.

* Git
* Python 2.6 or 2.7 (Mac users, see below for installation instructions)
* Pip and Virtualenv
* The latest OpenSSL distribution for your system

Once you have all of the above installed, you'll want to set up a Virtualenv.
Please read the `Virtualenv docs`_ for more info. While setting one up is an
optional step, we feel that it's a good idea to keep sets of packages separate
from other system applications, so we do recommend using it.

.. _installation_windows:

Windows
=======

.. highlight:: bat
   :linenothreshold: 1

To install on Windows, you'll need to set up a few extra things.

* Download and install the latest version of Python 2.x (**Not Python 3.x**) from the `Python website`_.
* Follow `these instructions`_ to add Python to your PATH.
* Install Twisted from `the Twisted site`_, making sure you pick the 32-bit or 64-bit version as appropriate.
* Download and install OpenSSL for Windows `from this site`_, making sure to pick the latest full release - **not** the "Light" version.
* Download and install PyOpenSSL `from here`_, making sure you pick the 32-bit or 64-bit version as appropriate.
* Install the `latest version`_ of MSysGit, either allowing it to install to System32, or adding the install location to your PATH like you did for Python.

Once you've done the above, open a command prompt (**cmd.exe** if you're using the run box), and do the
following.

1. **cd** to the location you're installing Ultros to.
2. **Clone the respository** from https://github.com/UltrosBot/Ultros.git
3. **cd** to the newly-created **Ultros/** folder.
4. **python -m ensurepip** to ensure that pip is installed.
5. If you're using Virtualenv, this is a good time to set it up, according to the `Virtualenv docs`_.
6. Run **pip install -r requirements.txt**.

Assuming all of the above completed successfully, you should now be ready to configure Ultros -
see the :ref:`configuration` page for more information on this. The above steps may be summarized
within this simple batch script ::

    @ECHO off
    REM Download Ultros
    cd C:\path\to\install\ultros\to
    git clone https://github.com/UltrosBot/Ultros.git
    cd Ultros

    REM Install pip
    python -m ensurepip

    REM If you're not using Virtualenv, you can skip this section
    pip install virtualenv
    virtualenv venv
    venv\Scripts\activate

    REM Finally, set up requirements
    pip install -r requirements.txt

.. _installation_linux:

Linux
=====

.. highlight:: sh
   :linenothreshold: 1

Linux is our preferred operating system, and we highly recommend that you use it to host
your bot. To do so, you'll need the following.

* Git
* Python 2.7
    * Most distributions will install Python 2 by default when you specify **python**, however some distributions (such as Arch) will install Python 3. Ultros does not support Python 3 and will not be able to until Twisted does, so be careful of this.
    * You'll also need the development headers, usually from the corresponding **-dev** package, as well as pip, often from the corresponding **-pip** package.
* **libffi** and **libffi-dev**
* The latest version of OpenSSL
* Your distro's equivalent of build-essential (A C compiler and headers)

Once you have all of the above installed, you may proceed to download and set up Ultros as follows::

    # Download Ultros
    cd /path/to/install/ultros/to
    git clone https://github.com/UltrosBot/Ultros.git
    cd Ultros

    # If you're not using Virtualenv, you can skip this section
    pip install virtualenv
    virtualenv venv
    source venv/bin/activate

    # Finally, set up requirements
    pip install -r requirements.txt

Assuming all of the above completed successfully, you should now be ready to configure Ultros -
see the :ref:`configuration` page for more information on this.

.. warning:: We highly recommend that you **do not run Ultros as root**. It
             does not require administrator privileges, and you should not
             grant it access to them. You may like to create a separate user
             for Ultros, which will also provide you with a convenient
             location to store it.

.. _installation_mac:

Mac OSX
=======

.. note:: These instructions are for Mavericks (10.9), and may differ slightly for
          different versions of OSX.

You'll need to do a few things before you can set up Ultros.

1. Install Homebrew_, if you haven't already.
2. Set up your environment `as shown here`_.
3. Open Terminal.app and run the following ::

    brew install git
    brew install python

  This may take a while to complete, and may also require you to update Xcode.
  However, you should install Python this way instead of downloading it from the
  Python website.

Now you're able to set up Ultros. ::

    # Download Ultros
    cd /path/to/install/ultros/to
    git clone https://github.com/UltrosBot/Ultros.git
    cd Ultros

    # If you're not using Virtualenv, you can skip this section
    pip install virtualenv
    virtualenv venv
    source venv/bin/activate

    # Finally, set up requirements
    pip install -r requirements.txt

Assuming all of the above completed successfully, you should now be ready to configure Ultros -
see the :ref:`configuration` page for more information on this.

.. Footnote links, etc

.. _the site: https://ultros.io
.. _Virtualenv docs: https://virtualenv.pypa.io/en/latest/

.. Windows links

.. _Python website: https://www.python.org/downloads/
.. _these instructions: http://www.anthonydebarros.com/2014/02/16/setting-up-python-in-windows-8-1/
.. _the Twisted site: https://twistedmatrix.com/trac/wiki/Downloads/
.. _from this site: https://slproweb.com/products/Win32OpenSSL.html
.. _from here: https://www.egenix.com/products/python/pyOpenSSL/#Download
.. _latest version: https://msysgit.github.io/

.. Mac links

.. _Homebrew: http://brew.sh/
.. _as shown here: http://hackercodex.com/guide/mac-osx-mavericks-10.9-configuration/
