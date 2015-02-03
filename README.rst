Installation of Unicore CMS
===========================

.. code-block:: bash

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install -e .

Running Unicore CMS for local development
-----------------------------------------

This is a Pyramid_ application, that uses Elasticsearch and Redis.

For OS X we recommend you install Elasticsearch and Redis with Brew_:

.. code-block:: bash

    $ brew install elasticsearch
    $ brew install redis

Start Elasticsearch in a separate Terminal tab:

.. code-block:: bash

    $ elasticsearch

Start Redis in a separate Terminal tab:

.. code-block:: bash

    $ redis-server

For Linux install them with your package manager (apt, rpm, yum etc...)
and make sure it's running as a service.

Then start the server:

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
.. _Brew: http://brew.sh
