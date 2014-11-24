#!/bin/bash

set -e

virtualenv ve
source ve/bin/activate
git pull
pip install -e .
pip install --upgrade elastic-git
git clone https://github.com/universalcore/unicore-cms-content-ffl-tanzania repo
eg-tools resync -c development.ini -m unicore.content.models.Category -f mappings/category.mapping.json -r true
eg-tools resync -c development.ini -m unicore.content.models.Page -f mappings/page.mapping.json
pserve development.ini --reload
