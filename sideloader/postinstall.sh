pip="${VENV}/bin/pip"
cd /var/praekelt/unicore-cms/ && echo `pwd` && ./install_libgit2 && cd ~/

$pip install cffi "praekelt-python-gitmodel>=0.1.2" /var/praekelt/unicore-cms/
