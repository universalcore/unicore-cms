from pyramid import testing
from webtest import TestApp
from cms import main
from cms.api.tests.utils import BaseTestCase


class CategoryTestCase(BaseTestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.delete_test_repo()
        settings = {'git.path': self.repo_path}
        self.app = TestApp(main({}, **settings))

        self.init_categories()

    def tearDown(self):
        testing.tearDown()
        self.delete_test_repo()

    def test_get_categories(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'uuid': resp.json[0]['id']}
        resp = self.app.get('/api/categories.json', data, status=200)
        self.assertEquals(resp.json['id'], data['uuid'])

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.get('/api/categories.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

    def test_post_category(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        uuid = resp.json[0]['id']
        data = {'uuid': uuid, 'title': 'New Title'}
        resp = self.app.post_json('/api/categories.json', data, status=200)
        self.assertTrue(resp.json['success'])

        resp = self.app.get('/api/categories.json', data, status=200)
        self.assertEquals(resp.json['title'], 'New Title')

        data = {'uuid': 'some-invalid-id', 'title': 'New Title'}
        resp = self.app.post_json('/api/categories.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        data = {'uuid': uuid}
        resp = self.app.post_json('/api/categories.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'title is a required field.')

        data = {'title': 'New Title'}
        resp = self.app.post_json('/api/categories.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'uuid is a required field.')

    def test_put_category(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'title': 'New Category'}
        resp = self.app.put_json('/api/categories.json', data, status=200)
        self.assertEquals(resp.json['title'], 'New Category')
        new_uuid = resp.json['uuid']

        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data = {'uuid': new_uuid}
        resp = self.app.get('/api/categories.json', data, status=200)
        self.assertEquals(resp.json['title'], 'New Category')
        self.assertEquals(resp.json['uuid'], new_uuid)

        resp = self.app.put_json('/api/categories.json', {}, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'title is a required field.')

        # TODO - Test for duplicates

    def test_delete_category(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'uuid': resp.json[0]['uuid']}
        resp = self.app.delete(
            '/api/categories.json?uuid=%(uuid)s' % data, status=200)
        self.assertTrue(resp.json['success'])

        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 1)

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.delete(
            '/api/categories.json?uuid=%(uuid)s' % data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 1)
