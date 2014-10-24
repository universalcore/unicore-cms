from cornice.resource import resource, view
from cms.api import validators
from cms.api.base import ApiBase

from elasticgit import Q

from unicore.content.models import Page, Category


@resource(
    collection_path='/api/pages.json',
    path='/api/pages/{uuid}.json'
)
class PageApi(ApiBase):

    def validate_primary_category(self, request):
        primary_category_uuid = self.request.validated.get('primary_category')

        if primary_category_uuid is not None:
            if primary_category_uuid:
                try:
                    [category] = self.workspace.S(Category).filter(
                        uuid=primary_category_uuid)
                    self.request.validated['primary_category'] = category
                except ValueError:
                    self.request.errors.add(
                        'api', 'DoesNotExist', 'Category not found.')
            else:
                self.request.validated['primary_category'] = None

    def collection_get(self):
        query = Q()
        primary_category_uuid = self.request.GET.get('primary_category', None)
        if primary_category_uuid is not None:
            query += Q(primary_category=primary_category_uuid)
        return [dict(result.get_object())
                for result in self.workspace.S(Page).query(query)]

    @view(renderer='json')
    def get(self):
        uuid = self.request.matchdict['uuid']

        try:
            [page] = self.workspace.S(Page).filter(uuid=uuid)
            return dict(page.get_object())
        except ValueError:
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

        try:
            [page] = self.workspace.S(Page).filter(uuid=uuid)
            original = page.get_object()
            updated = original.update({
                'title': title,
                'content': content,
                'primary_category': (
                    None
                    if primary_category is None
                    else primary_category.uuid),
            })
            self.workspace.save(updated, 'Page updated: %s' % (title,))
            self.workspace.refresh_index()
            return dict(updated)
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Page not found.')

    @view(
        validators=(validators.validate_page, 'validate_primary_category'),
        renderer='json')
    def collection_post(self):
        title = self.request.validated['title']
        content = self.request.validated['content']
        primary_category = self.request.validated.get('primary_category')

        page = Page({
            'title': title,
            'content': content,
            'primary_category': (
                None
                if primary_category is None
                else primary_category.uuid)
        })
        self.workspace.save(page, 'Page added: %s' % title)
        self.workspace.refresh_index()

        self.request.response.status = 201
        self.request.response.location = '/api/pages/%s.json' % (page.uuid,)
        return dict(page)

    @view()
    def delete(self):
        uuid = self.request.matchdict['uuid']
        try:
            [page] = self.workspace.S(Page).filter(uuid=uuid)
            data = page.get_object()
            self.workspace.delete(data, 'Page delete: %s' % (page.title,))
            self.workspace.refresh_index()
            return dict(data)
        except ValueError:
            self.request.errors.add(
                'api', 'DoesNotExist', 'Page not found.')
