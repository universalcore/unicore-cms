from pyramid import testing
from webtest import TestApp
from cms import main
from cms.api.tests.utils import BaseTestCase


class PageTestCase(BaseTestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.delete_test_repo()
        settings = {'git.path': self.repo_path}
        self.app = TestApp(main({}, **settings))

        self.init_categories()
        self.init_pages()

    def tearDown(self):
        testing.tearDown()
        self.delete_test_repo()

    def test_get_pages(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'uuid': resp.json[0]['uuid']}
        resp = self.app.get('/api/pages/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['uuid'], data['uuid'])

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.get('/api/pages/%(uuid)s.json' % data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Page not found.')

    def test_get_pages_for_category(self):
        models = self.get_repo_models()
        hygiene_category = models.Category.filter(slug='hygiene')[0]
        p = models.Page(
            title='Test Category Page',
            content='this is sample content for a hygiene page',
            primary_category=hygiene_category
        )
        p.save(True, message='added hygiene page')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data = {'uuid': p.id}
        resp = self.app.get('/api/pages/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['title'], 'Test Category Page')
        self.assertEquals(resp.json['primary_category']['slug'], 'hygiene')

        data = {'primary_category': hygiene_category.id}
        resp = self.app.get('/api/pages.json', data, status=200)
        self.assertEquals(len(resp.json), 1)

    def test_put_page(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {
            'title': 'New Page',
            'content': 'Sample page content',
        }
        resp = self.app.put_json('/api/pages.json', data, status=200)
        self.assertEquals(resp.json['title'], 'New Page')
        new_uuid = resp.json['uuid']

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data = {'uuid': new_uuid}
        resp = self.app.get('/api/pages/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['title'], 'New Page')
        self.assertEquals(resp.json['uuid'], new_uuid)

        resp = self.app.put_json('/api/pages.json', {}, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'title is a required field.')
        self.assertEquals(
            resp.json['errors'][1]['description'],
            'content is a required field.')

    def test_put_page_with_category(self):
        models = self.get_repo_models()
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        hygiene_category = models.Category.filter(slug='hygiene')[0]
        data = {
            'title': 'New Page',
            'content': 'Sample page content',
            'primary_category': hygiene_category.id
        }
        resp = self.app.put_json('/api/pages.json', data, status=200)
        self.assertEquals(resp.json['title'], 'New Page')
        self.assertEquals(resp.json['primary_category']['title'], 'Hygiene')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data['primary_category'] = 'some-invalid-id'
        resp = self.app.put_json('/api/pages.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

    def test_post_page(self):
        models = self.get_repo_models()
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)
        uuid = resp.json[0]['uuid']

        diarrhoea_category = models.Category.filter(slug='diarrhoea')[0]
        data = {
            'uuid': uuid,
            'title': 'Another New Page',
            'content': 'Another sample page content',
            'primary_category': diarrhoea_category.id
        }
        resp = self.app.post_json(
            '/api/pages/%s.json' % uuid, data, status=200)
        self.assertEquals(resp.json['title'], 'Another New Page')
        self.assertEquals(resp.json['primary_category']['title'], 'Diarrhoea')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {
            'title': 'Yet Another New Page',
            'content': 'Yet Another sample page content',
            'primary_category': diarrhoea_category.id
        }
        resp = self.app.post_json(
            '/api/pages/some-invalid-id.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Page not found.')

        data['primary_category'] = 'some-invalid-id'
        resp = self.app.post_json(
            '/api/pages/%s.json' % uuid, data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        resp = self.app.get('/api/pages/%s.json' % uuid, status=200)
        self.assertEquals(resp.json['uuid'], uuid)
        self.assertEquals(resp.json['title'], 'Another New Page')
        self.assertEquals(resp.json['content'], 'Another sample page content')
        self.assertEquals(resp.json['primary_category']['title'], 'Diarrhoea')

    def test_delete_page(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'uuid': resp.json[0]['uuid']}
        resp = self.app.delete(
            '/api/pages/%(uuid)s.json' % data, status=200)

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 1)

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.delete(
            '/api/pages/%(uuid)s.json' % data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Page not found.')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 1)
