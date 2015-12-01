import datetime

from system.enums import ProtocolState

__author__ = 'Gareth Coles'

#: The current version. This gets replaced if you're using git.
__version__ = "1.1.0"
__version_info__ = "Not being run from a Git repo."
__release__ = "1.1.0"

version_info = {
    "release": __release__,
    "hash": None,
    "commit": None
}

try:
    from git import repo

    r = repo.Repo(".")
    heads = r.heads
    master = heads[0]
    commit = master.commit

    __version__ = "Git: %s" % commit
    __version_info__ = "Last commit by %s (%s) - %s" % \
                       (commit.author,
                        datetime.datetime.fromtimestamp(
                            commit.committed_date
                        ).strftime("%d %b, %Y - %H:%M:%S"),
                        commit.summary.replace("\n", " / "))

    version_info["hash"] = str(commit)
    version_info["commit"] = commit.summary.replace("\n", " / ")
except Exception:
    if __version__ is None:
        __version__ = "1.1.0"
        __version_info__ = "Unable to get last commit."
