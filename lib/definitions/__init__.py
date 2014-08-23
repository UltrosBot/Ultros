"""
This isn't a Python module, but it's where library definitions go.

If your package requires a library that cannot be installed using pip, you
may use a definitions file here and the relevant files will be downloaded
automatically when the bot starts.

A definitions file is simply a .json file containing a "packages" section, laid
out like this::

    {
        "packages": [
            {
                "name": "Package name",
                "filename": "folder/filename.py",
                "module": "folder.filename",
                "url": "http://site.ext/filename.py",
                "attrib": "[WTFPL] That Guy"
            }
        ]
    }

Note that this will never re-download files, and each entry should only be one
file. Zip files and other archives are not supported.
"""

__author__ = 'Gareth Coles'
