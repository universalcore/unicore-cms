#!/bin/bash
set -e
# Any subsequent commands which fail will cause the shell script to exit immediately

export LIBGIT2=$VIRTUAL_ENV
export LDFLAGS="-Wl,-rpath='$LIBGIT2/lib',--enable-new-dtags $LDFLAGS"

LIBGIT2_VERSION='0.21.1'

# pygit version has an issue with pushing remotes via ssh (#431)
# downgrading back to 0.21.2
PYGIT2_VERSION='0.21.2'

# only download if version doesn't exist locally
if [ ! -d "libgit2-$LIBGIT2_VERSION" ]; then
    wget https://github.com/libgit2/libgit2/archive/v$LIBGIT2_VERSION.tar.gz
    tar xzf v$LIBGIT2_VERSION.tar.gz
fi

cd "libgit2-$LIBGIT2_VERSION"
cmake . -DCMAKE_INSTALL_PREFIX=$LIBGIT2
cmake --build . --target install
cmake --build .
make
make install
pip install cffi
pip install pygit2==$PYGIT2_VERSION
cd ..

# cleaning up
rm v0.21.1.tar.gz*
