import os

from pyramid import testing
from webtest import TestApp

from cms import main
from cms.tests.utils import BaseTestCase
from cms.tests.utils import RepoHelper


class CategoryTestCase(BaseTestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.repo_path = os.path.join(
            os.getcwd(), '.test_repos', self.id())
        self.repo = RepoHelper.create(self.repo_path)
        self.repo.create_categories()

        settings = {
            'git.path': self.repo.path,
        }
        self.app = TestApp(main({}, **settings))

    def tearDown(self):
        testing.tearDown()
        self.repo.destroy()

    def test_get_categories(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'uuid': resp.json[0]['uuid']}
        resp = self.app.get('/api/categories/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['uuid'], data['uuid'])

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.get('/api/categories/%(uuid)s.json' % data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

    def test_put_category(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        uuid = resp.json[0]['uuid']
        data = {'uuid': uuid, 'title': 'New Title'}
        resp = self.app.put_json(
            '/api/categories/%(uuid)s.json' % data, data, status=200)
        self.assertEquals(resp.json['title'], 'New Title')

        resp = self.app.get('/api/categories/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['title'], 'New Title')

        data = {'uuid': 'some-invalid-id', 'title': 'New Title'}
        resp = self.app.put_json(
            '/api/categories/%(uuid)s.json' % data, data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        data = {'uuid': uuid}
        resp = self.app.put_json(
            '/api/categories/%(uuid)s.json' % data, data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'title is a required field.')

    def test_post_category(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'title': 'New Category'}
        resp = self.app.post_json('/api/categories.json', data, status=201)
        self.assertTrue(resp.location.endswith(
            '/api/categories/%s.json' % resp.json['uuid']))
        self.assertEquals(resp.json['title'], 'New Category')
        new_uuid = resp.json['uuid']

        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data = {'uuid': new_uuid}
        resp = self.app.get('/api/categories/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['title'], 'New Category')
        self.assertEquals(resp.json['uuid'], new_uuid)

        resp = self.app.post_json('/api/categories.json', {}, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'title is a required field.')

    def test_delete_category(self):
        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'uuid': resp.json[0]['uuid']}
        resp = self.app.delete(
            '/api/categories/%(uuid)s.json' % data, status=200)

        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 1)

        data = {'uuid': 'some-invalid-id'}
        resp = self.app.delete(
            '/api/categories/%(uuid)s.json' % data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        resp = self.app.get('/api/categories.json', status=200)
        self.assertEquals(len(resp.json), 1)
