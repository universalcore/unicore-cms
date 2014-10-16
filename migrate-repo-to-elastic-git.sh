#!/bin/bash

# halt on any error
set -e

mkdir -p unicore/content

touch unicore/__init__.py
touch unicore/content/__init__.py

python -m elasticgit.tools \
    migrate-gitmodel-repo \
    ./repo/ unicore.content.models

python -m elasticgit.tools \
    load-schema ./repo/unicore.content.models/GitPageModel.avro.json \
                ./repo/unicore.content.models/GitCategoryModel.avro.json \
                --map-field uuid=elasticgit.models.UUIDField \
                --rename-model GitPageModel=Page \
                --rename-model GitCategoryModel=Category \
                > ./unicore/content/models.py

mv repo/unicore.content.models/*.avro.json ./unicore/
