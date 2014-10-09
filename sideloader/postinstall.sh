pip="${VENV}/bin/pip"
curl https://raw.githubusercontent.com/praekelt/unicore-cms/develop/utils/install_libgit2.sh | sh

$pip install -r "${INSTALLDIR}/${REPO}/requirements.txt"
