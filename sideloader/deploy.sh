#!/bin/bash

cp -a unicore-cms ./build/

cd build/; ./install_pygit2

${PIP} install praekelt-python-gitmodel

