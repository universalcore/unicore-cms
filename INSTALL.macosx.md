Installing PyGit2 on Mac OS X
=============================

Installing is easy with brew & pip, the only thing you need to make sure
of is that your version of `libgit2` and `pygit2` are
[compatible](http://www.pygit2.org/install.html#requirements).

    $ brew install libffi
    $ brew install libgit2
    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install cffi==0.8.6
    (ve)$ pip install pygit2==0.20.3
    (ve)$ python -c 'import pygit2; print pygit2.__version__'
    0.20.3
    (ve)$
