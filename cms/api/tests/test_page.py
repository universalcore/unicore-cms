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
        resp = self.app.get('/api/pages.json', data, status=200)
        self.assertEquals(resp.json['uuid'], data['uuid'])

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.get('/api/pages.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Page not found.')
