from cornice.resource import resource, view
from cms.api import validators
from cms.api.base import ApiBase

from unicore.content.models import Localisation


@resource(
    collection_path='/api/localisations.json',
    path='/api/localisations/{locale}.json'
)
class LocalisationApi(ApiBase):

    def collection_get(self):
        return [dict(result.get_object())
                for result in self.workspace.S(Localisation)]

    @view(renderer='json')
    def get(self):
        locale = self.request.matchdict['locale']
        try:
            [loc] = self.workspace.S(Localisation).filter(locale=locale)
            return dict(loc.get_object())
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Localisation not found.')

    @view(validators=validators.validate_localisation, renderer='json')
    def put(self):
        locale = self.request.matchdict['locale']
        image = self.request.validated.get('image')
        image_host = self.request.validated.get('image_host')
        try:
            [loc] = self.workspace.S(Localisation).filter(locale=locale)
            original = loc.get_object()
            updated = original.update(
                {'image': image, 'image_host': image_host})
            self.workspace.save(updated, 'Localisation updated: %s' % locale)
            return dict(updated)
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Localisation not found.')

    @view(validators=validators.validate_localisation, renderer='json')
    def collection_post(self):
        locale = self.request.validated['locale']
        image = self.request.validated.get('image')
        image_host = self.request.validated.get('image_host')

        loc = Localisation(
            {'locale': locale, 'image': image, 'image_host': image_host})
        self.workspace.save(loc, 'Localisation added: %s' % (locale,))
        self.workspace.refresh_index()

        next = '/api/localisations/%s.json' % loc.locale
        self.request.response.status = 201
        self.request.response.location = next
        return dict(loc)

    @view()
    def delete(self):
        locale = self.request.matchdict['locale']
        try:
            [loc] = self.workspace.S(Localisation).filter(locale=locale)
            self.workspace.delete(loc.get_object(), "Removed via API")
            self.workspace.refresh_index()
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Localisation not found.')
