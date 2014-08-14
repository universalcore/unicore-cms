#!/bin/bash

cp -a unicore-cms ./build/

echo `pwd`
cd build/unicore-cms/; ./install_pygit2

${PIP} install praekelt-python-gitmodel

