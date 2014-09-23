Installation of Unicore CMS
===========================

Unicore CMS builds on top of libgit2 and pygit2, both require some
fiddling to get installed.

Installing on OS X
------------------

Installing is easy with [brew](http://brew.sh) & pip, the only thing you
need to make sure of is that your version of `libgit2` and `pygit2` are
[compatible](http://www.pygit2.org/install.html#requirements).

    $ brew install libffi
    $ brew install libgit2

The requirements.txt file doesn't pin a specific version because it
varies per platform. For OS X the following `pip` package versions work:

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install cffi==0.8.6
    (ve)$ pip install pygit2==0.20.3
    (ve)$ python -c 'import pygit2; print pygit2.__version__'
    0.20.3
    (ve)$ pip install -e .

Installing on Linux (Ubuntu/Debian)
-----------------------------------

See the instructions in the `utils/install_libgit2.sh` shell script.

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ sh utils/install_libgit2.sh
    (ve)$ pip install -e .


Running Unicore CMS for local development
-----------------------------------------

This is a [Pyramid](http://docs.pylonsproject.org/en/latest/docs/pyramid.html) application

    (ve)$ pserve development.ini --reload

Running Unicore CMS tests
-------------------------

    (ve)$ python setup.py test
