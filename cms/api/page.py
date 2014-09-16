from cornice.resource import resource, view
from cms.api import validators, utils
from gitmodel.exceptions import DoesNotExist


@resource(
    collection_path='/api/pages.json',
    path='/api/pages/{uuid}.json'
)
class PageApi(utils.ApiBase):

    def validate_primary_category(self, request):
        models = self.get_repo_models()
        primary_category_uuid = self.request.validated.get('primary_category')

        if primary_category_uuid is not None:
            if primary_category_uuid:
                try:
                    category = models.GitCategoryModel.get(
                        primary_category_uuid)
                    self.request.validated['primary_category'] = category
                except DoesNotExist:
                    self.request.errors.add(
                        'api', 'DoesNotExist', 'Category not found.')
            else:
                self.request.validated['primary_category'] = None

    def collection_get(self):
        models = self.get_repo_models()

        primary_category_uuid = self.request.GET.get('primary_category', None)
        if primary_category_uuid:
            try:
                category = models.GitCategoryModel.get(primary_category_uuid)
                return [
                    p.to_dict()
                    for p in models.GitPageModel.filter(
                        primary_category=category)
                ]
            except DoesNotExist:
                self.request.errors.add(
                    'api', 'DoesNotExist', 'Category not found.')
                return

        return [p.to_dict() for p in models.GitPageModel.all()]

    @view(renderer='json')
    def get(self):
        models = self.get_repo_models()

        uuid = self.request.matchdict['uuid']

        try:
            page = models.GitPageModel.get(uuid)
            return page.to_dict()
        except DoesNotExist:
            self.request.errors.add('api', 'DoesNotExist', 'Page not found.')
            return

    @view(
        validators=(validators.validate_page, 'validate_primary_category'),
        renderer='json')
    def put(self):
        uuid = self.request.matchdict['uuid']
        title = self.request.validated['title']
        content = self.request.validated['content']
        primary_category = self.request.validated.get('primary_category')

        models = self.get_repo_models()
        try:
            page = models.GitPageModel.get(uuid)
            page.title = title
            page.content = content
            page.primary_category = primary_category
            page.save(True, message='Page updated: %s' % title)
            self.get_registered_ws().sync_repo_index()
            return page.to_dict()
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Page not found.')

    @view(
        validators=(validators.validate_page, 'validate_primary_category'),
        renderer='json')
    def collection_post(self):
        title = self.request.validated['title']
        content = self.request.validated['content']
        primary_category = self.request.validated.get('primary_category')

        models = self.get_repo_models()

        page = models.GitPageModel(
            title=title,
            content=content,
            primary_category=primary_category
        )
        page.save(True, message='Page added: %s' % title)
        self.get_registered_ws().sync_repo_index()

        self.request.response.status = 201
        self.request.response.location = '/api/pages/%s.json' % page.id
        return page.to_dict()

    @view()
    def delete(self):
        uuid = self.request.matchdict['uuid']
        models = self.get_repo_models()
        try:
            page = models.GitPageModel().get(uuid)
            models.GitPageModel.delete(
                uuid, True, message='Page delete: %s' % page.title)
        except DoesNotExist:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Page not found.')
