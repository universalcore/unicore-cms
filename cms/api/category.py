from cornice.resource import resource, view
from cms.api import validators, utils
from gitmodel.exceptions import DoesNotExist


@resource(
    collection_path='/api/categories.json',
    path='/api/categories/{uuid}.json'
)
class CategoryApi(utils.ApiBase):

    def collection_get(self):
        models = self.get_repo_models()
        return [c.to_dict() for c in models.GitCategoryModel().all()]

    @view(renderer='json')
    def get(self):
        models = self.get_repo_models()
        uuid = self.request.matchdict['uuid']
        try:
            category = models.GitCategoryModel().get(uuid)
            return category.to_dict()
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')

    @view(validators=validators.validate_category, renderer='json')
    def put(self):
        uuid = self.request.matchdict['uuid']
        title = self.request.validated['title']

        models = self.get_repo_models()
        try:
            category = models.GitCategoryModel().get(uuid)
            category.title = title
            category.save(True, message='Category updated: %s' % title)
            self.get_registered_ws().sync_repo_index()
            return category.to_dict()
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')

    @view(validators=validators.validate_category, renderer='json')
    def collection_post(self):
        title = self.request.validated['title']

        models = self.get_repo_models()

        category = models.GitCategoryModel(title=title)
        category.save(True, message='Category added: %s' % title)
        self.get_registered_ws().sync_repo_index()

        next = '/api/categories/%s.json' % category.id
        self.request.response.status = 201
        self.request.response.location = next
        return category.to_dict()

    @view()
    def delete(self):
        uuid = self.request.matchdict['uuid']
        models = self.get_repo_models()
        try:
            category = models.GitCategoryModel().get(uuid)
            models.GitCategoryModel.delete(
                uuid, True, message='Category delete: %s' % category.title)
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Category not found.')
