import json


def validate_required_field(request, data, key):
    if key in data and data[key] is not None:
        request.validated[key] = data[key]
    else:
        request.errors.add('body', key, '%s is a required field.' % key)


def validate_optional_field(request, data, key):
    if key in data and data[key] is not None:
        request.validated[key] = data[key]


def validate_category(request):
    data = json.loads(request.body)
    validate_required_field(request, data, 'title')


def validate_localisation(request):
    data = json.loads(request.body)
    validate_required_field(request, data, 'locale')
    validate_optional_field(request, data, 'image')
    validate_optional_field(request, data, 'image_host')


def validate_put_category(request):
    data = json.loads(request.body)
    validate_required_field(request, data, 'title')


def validate_page(request):
    data = json.loads(request.body)
    validate_required_field(request, data, 'title')
    validate_required_field(request, data, 'content')
    validate_optional_field(request, data, 'primary_category')
