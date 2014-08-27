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