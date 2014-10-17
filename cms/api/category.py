from cornice.resource import resource, view
from cms.api import validators
from cms.api.base import ApiBase

from unicore.content.models import Category


@resource(
    collection_path='/api/categories.json',
    path='/api/categories/{uuid}.json'
)
class CategoryApi(ApiBase):

    def collection_get(self):
        return [dict(result.get_object())
                for result in self.workspace.S(Category)]

    @view(renderer='json')
    def get(self):
        uuid = self.request.matchdict['uuid']
        try:
            [category] = self.workspace.S(Category).filter(uuid=uuid)
            return dict(category.get_object())
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')

    @view(validators=validators.validate_category, renderer='json')
    def put(self):
        uuid = self.request.matchdict['uuid']
        title = self.request.validated['title']
        try:
            [category] = self.workspace.S(Category).filter(uuid=uuid)
            original = category.get_object()
            updated = original.update({'title': title})
            self.workspace.save(updated, 'Category updated: %s' % (title,))
            return dict(updated)
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')

    @view(validators=validators.validate_category, renderer='json')
    def collection_post(self):
        title = self.request.validated['title']

        category = Category({'title': title})
        self.workspace.save(category, 'Category added: %s' % (title,))
        self.workspace.refresh_index()

        next = '/api/categories/%s.json' % category.uuid
        self.request.response.status = 201
        self.request.response.location = next
        return dict(category)

    @view()
    def delete(self):
        uuid = self.request.matchdict['uuid']
        try:
            [category] = self.workspace.S(Category).filter(uuid=uuid)
            self.workspace.delete(category.get_object(), "Removed via API")
            self.workspace.refresh_index()
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')
