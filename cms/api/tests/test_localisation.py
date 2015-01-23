from pyramid import testing

from cms.tests.base import UnicoreTestCase
from unicore.content.models import Localisation


class LocalisationTestCase(UnicoreTestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.workspace = self.mk_workspace()
        self.workspace.setup_custom_mapping(Localisation, {
            'properties': {
                'locale': {
                    'type': 'string',
                    'index': 'not_analyzed',
                }
            }
        })

        self.create_localisation(self.workspace)
        self.app = self.mk_app(self.workspace)

    def tearDown(self):
        testing.tearDown()

    def test_get_localisations(self):
        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 1)

        data = {'locale': resp.json[0]['locale']}
        resp = self.app.get('/api/localisations/%(locale)s.json' % data,
                            status=200)
        self.assertEquals(resp.json['locale'], data['locale'])

        data = {'locale': 'spa_ES'}
        resp = self.app.get('/api/localisations/%(locale)s.json' % data,
                            status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Localisation not found.')

    def test_put_localisation(self):
        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 1)

        locale = resp.json[0]['locale']
        data = {
            'locale': locale,
            'image': 'new-image-uuid',
            'image_host': 'http://some.site.com'}
        resp = self.app.put_json(
            '/api/localisations/%(locale)s.json' % data, data, status=200)
        self.assertEquals(resp.json['image'], 'new-image-uuid')
        self.assertEquals(resp.json['image_host'], 'http://some.site.com')

        resp = self.app.get('/api/localisations/%(locale)s.json' % data,
                            status=200)
        self.assertEquals(resp.json['image'], 'new-image-uuid')

        data = {'locale': 'spa_ES', 'image': 'new-image-uuid'}
        resp = self.app.put_json(
            '/api/localisations/%(locale)s.json' % data, data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Localisation not found.')

    def test_post_localisation(self):
        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 1)

        data = {
            'locale': 'spa_ES',
            'image': 'another-new-image-uuid',
            'image_host': 'http://some.site.com'}
        resp = self.app.post_json('/api/localisations.json', data, status=201)
        self.assertTrue(resp.location.endswith(
            '/api/localisations/%s.json' % resp.json['locale']))
        self.assertEquals(resp.json['image'], 'another-new-image-uuid')
        new_locale = resp.json['locale']

        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'locale': new_locale}
        resp = self.app.get('/api/localisations/%(locale)s.json' % data,
                            status=200)
        self.assertEquals(resp.json['image'], 'another-new-image-uuid')
        self.assertEquals(resp.json['image_host'], 'http://some.site.com')

        resp = self.app.post_json('/api/localisations.json', {}, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'locale is a required field.')

    def test_delete_category(self):
        self.create_localisation(self.workspace, 'spa_ES')
        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 2)

        data = {'locale': resp.json[0]['locale']}
        resp = self.app.delete(
            '/api/localisations/%(locale)s.json' % data, status=200)

        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 1)

        data = {'locale': 'fre_FR'}
        resp = self.app.delete(
            '/api/localisations/%(locale)s.json' % data, status=400)
        self.assertEquals(
            resp.json['errors'][0]['description'],
            'Localisation not found.')

        resp = self.app.get('/api/localisations.json', status=200)
        self.assertEquals(len(resp.json), 1)
