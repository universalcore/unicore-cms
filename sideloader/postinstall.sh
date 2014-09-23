pip="${VENV}/bin/pip"
cd /var/praekelt/unicore-cms/ && echo `pwd` && ./utils/install_libgit2.sh && cd ~/

$pip install cffi "praekelt-python-gitmodel>=0.1.2" /var/praekelt/unicore-cms/
