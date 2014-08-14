#!/bin/bash

cp -a unicore-cms ./build/

./install_pygit2

${PIP} install praekelt-python-gitmodel

