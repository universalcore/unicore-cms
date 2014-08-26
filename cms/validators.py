import json


def update_validated_field(request, data, key):
    if key in data and data[key] is not None:
        request.validated[key] = data[key]


def validate_required_field(request, data, key):
    if key in data and data[key] is not None:
        update_validated_field(request, data, key)
    else:
        request.errors.add('body', key, '%s is a required field.' % key)


def validate_post_category(request):
    data = json.loads(request.body)
    validate_required_field(request, data, 'uuid')
    validate_required_field(request, data, 'title')
