#!/bin/bash

cp -a unicore-cms ./build/

cd unicore-cms/ && echo `pwd` && ./install_pygit2

${PIP} install praekelt-python-gitmodel

