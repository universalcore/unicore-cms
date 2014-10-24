Installation of Unicore CMS
===========================

.. code-block:: bash

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install -e .

Running Unicore CMS for local development
-----------------------------------------

This is a Pyramid_ application.

.. code-block:: bash

    (ve)$ pserve development.ini --reload

It'll run happily with the stock ``development.ini`` file provided but
it will be without any content.

For a better experience add an entry to it to have it load a
content repository::

    git.content_repo_url = https://github.com/your/content-repo.git

Running Unicore CMS tests
-------------------------

.. code-block:: bash

    (ve)$ pip install -r requirements-dev.txt
    (ve)$ py.test cms


.. _Pyramid: http://docs.pylonsproject.org/en/latest/docs/pyramid.html
