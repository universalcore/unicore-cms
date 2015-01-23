from pyramid import testing

from cms.tests.base import UnicoreTestCase


class PageTestCase(UnicoreTestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.workspace = self.mk_workspace()
        self.category1, self.category2 = self.create_categories(self.workspace)
        self.create_pages(self.workspace)

        self.app = self.mk_app(self.workspace, settings={
            'git.content_repo_url': '',
        })

    def tearDown(self):
        testing.tearDown()

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
        [page] = self.create_pages(
            self.workspace,
            count=1, primary_category=self.category1.uuid,
            title='Test Category Page',
            content='this is sample content for a hygiene page')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

        resp = self.app.get('/api/pages/%s.json' % (page.uuid,), status=200)
        self.assertEquals(resp.json['title'], 'Test Category Page')
        self.assertEquals(resp.json['primary_category'], self.category1.uuid)

        data = {'primary_category': self.category1.uuid}
        resp = self.app.get('/api/pages.json', data, status=200)
        self.assertEquals(len(resp.json), 1)

    def test_post_page(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {
            'title': 'New Page',
            'content': 'Sample page content',
        }
        resp = self.app.post_json('/api/pages.json', data, status=201)
        self.assertTrue(resp.location.endswith(
            '/api/pages/%s.json' % resp.json['uuid']))
        self.assertEquals(resp.json['title'], 'New Page')
        new_uuid = resp.json['uuid']

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data = {'uuid': new_uuid}
        resp = self.app.get('/api/pages/%(uuid)s.json' % data, status=200)
        self.assertEquals(resp.json['title'], 'New Page')
        self.assertEquals(resp.json['uuid'], new_uuid)

        resp = self.app.post_json('/api/pages.json', {}, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'title is a required field.')
        self.assertEquals(
            resp.json['errors'][1]['description'],
            'content is a required field.')

    def test_post_page_with_category(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {
            'title': 'New Page',
            'content': 'Sample page content',
            'primary_category': self.category1.uuid
        }
        resp = self.app.post_json('/api/pages.json', data, status=201)
        self.assertTrue(resp.location.endswith(
            '/api/pages/%s.json' % resp.json['uuid']))
        self.assertEquals(resp.json['title'], 'New Page')
        self.assertEquals(resp.json['primary_category'], self.category1.uuid)

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

        data['primary_category'] = 'some-invalid-id'
        resp = self.app.post_json('/api/pages.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 3)

    def test_put_page(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)
        uuid = resp.json[0]['uuid']

        data = {
            'uuid': uuid,
            'title': 'Another New Page',
            'content': 'Another sample page content',
            'primary_category': self.category1.uuid
        }
        resp = self.app.put_json(
            '/api/pages/%s.json' % uuid, data, status=200)
        self.assertEquals(resp.json['title'], 'Another New Page')
        self.assertEquals(resp.json['primary_category'], self.category1.uuid)

        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {
            'title': 'Yet Another New Page',
            'content': 'Yet Another sample page content',
            'primary_category': self.category1.uuid
        }
        resp = self.app.put_json(
            '/api/pages/some-invalid-id.json', data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Page not found.')

        data['primary_category'] = 'some-invalid-id'
        resp = self.app.put_json(
            '/api/pages/%s.json' % uuid, data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Category not found.')

        resp = self.app.get('/api/pages/%s.json' % uuid, status=200)
        self.assertEquals(resp.json['uuid'], uuid)
        self.assertEquals(resp.json['title'], 'Another New Page')
        self.assertEquals(resp.json['content'], 'Another sample page content')
        self.assertEquals(resp.json['primary_category'], self.category1.uuid)

    def test_put_page_with_blank_category(self):
        resp = self.app.get('/api/pages.json', status=200)
        self.assertEquals(len(resp.json), 2)
        uuid = resp.json[0]['uuid']

        data = {
            'uuid': uuid,
            'title': 'Edited Page with no category',
            'content': 'Another sample page content',
            'primary_category': ''
        }
        resp = self.app.put_json(
            '/api/pages/%s.json' % uuid, data, status=200)
        self.assertEquals(resp.json['title'], 'Edited Page with no category')
        self.assertEquals(resp.json['content'], 'Another sample page content')
        self.assertEquals(resp.json['primary_category'], None)

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
