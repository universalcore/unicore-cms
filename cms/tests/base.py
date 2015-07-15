import os
import tempfile
from ConfigParser import ConfigParser
from datetime import datetime
from uuid import uuid4

from beaker.session import Session
from webtest import TestApp
from unittest import TestCase

from pyramid import testing

from cms import main, USER_DATA_SESSION_KEY

from elasticgit import EG

from slugify import slugify

from unicore.content.models import Category, Page, Localisation


class UnicoreTestCase(TestCase):

    destroy = 'KEEP_REPO' not in os.environ

    def mk_workspace(self, working_dir='.test_repos/',
                     name=None,
                     url='http://localhost',
                     index_prefix=None,
                     auto_destroy=None,
                     author_name='Test Kees',
                     author_email='kees@example.org'):
        name = name or self.id()
        index_prefix = index_prefix or name.lower().replace('.', '-')
        auto_destroy = auto_destroy or self.destroy
        workspace = EG.workspace(os.path.join(working_dir, name), es={
            'urls': [url],
        }, index_prefix=index_prefix)
        if auto_destroy:
            self.addCleanup(workspace.destroy)

        workspace.setup(author_name, author_email)
        while not workspace.index_ready():
            pass

        return workspace

    def mk_app(self, workspace, ini_config={}, settings={}, main=main,
               extra_environ={}):
        ini_defaults = {
            'celery': {
                'CELERY_ALWAYS_EAGER': True,
            }
        }
        ini_defaults.update(ini_config)

        settings_defaults = {
            'git.path': workspace.working_dir,
            'es.index_prefix': workspace.index_prefix,
            'unicorehub.host': 'http://hub.unicore.io',
            'unicorehub.app_id': 'sample-app-id',
            'unicorehub.app_password': 'sample-password',
            'unicorehub.redirect_to_https': None,
        }
        settings_defaults.update(settings)

        config_file = self.mk_configfile(ini_defaults)
        app = TestApp(main({
            '__file__': config_file,
            'here': os.path.dirname(workspace.working_dir),
        }, **settings_defaults), extra_environ=extra_environ)
        return app

    def mk_tempfile(self):
        fp, pathname = tempfile.mkstemp(text=True)
        self.addCleanup(os.unlink, pathname)
        return os.fdopen(fp, 'w'), pathname

    def mk_configfile(self, data):
        fp, pathname = self.mk_tempfile()
        with fp:
            cp = ConfigParser()
            # Do not lower case every key
            cp.optionxform = str
            for section, section_items in data.items():
                cp.add_section(section)
                for key, value in section_items.items():
                    cp.set(section, key, value)
            cp.write(fp)
        return pathname

    def mk_request(self, params={}, matchdict={}, locale_name='eng_GB'):
        request = testing.DummyRequest(params)
        request.matchdict = matchdict
        request.google_analytics = {}
        request.user = None

        if '_LOCALE_' not in params:
            request.locale_name = locale_name

        for client in ('commentclient', 'hubclient'):
            if getattr(request.registry, client, None) is None:
                setattr(request.registry, client, None)

        return request

    def mk_session(self, logged_in=True, user_data={}):
        session_id = uuid4().hex
        session = Session(
            testing.DummyRequest(), id=session_id, use_cookies=False)

        if logged_in:
            user_data = user_data or {
                'uuid': uuid4().hex,
                'username': 'foo',
                'app_data': {'display_name': 'foobar'}
            }
            session[USER_DATA_SESSION_KEY] = user_data
            session['auth.userid'] = user_data['uuid']

        session.save()
        # return the session and cookie header
        return session, {'Cookie': 'beaker.session.id=%s' % session_id}

    def create_categories(
            self, workspace, count=2, locale='eng_GB', **kwargs):
        categories = []
        for i in range(count):
            data = {}
            data.update({
                'title': u'Test Category %s' % (i,),
                'language': locale,
                'position': i
            })
            data.update(kwargs)
            data.update({
                'slug': slugify(data['title'])
            })

            category = Category(data)
            workspace.save(
                category, u'Added category %s.' % (i,))
            categories.append(category)

        workspace.refresh_index()
        return categories

    def create_pages(
            self, workspace, count=2, timestamp_cb=None, locale='eng_GB',
            **kwargs):
        timestamp_cb = (
            timestamp_cb or (lambda i: datetime.utcnow().isoformat()))
        pages = []
        for i in range(count):
            data = {}
            data.update({
                'title': u'Test Page %s' % (i,),
                'content': u'this is sample content for pg %s' % (i,),
                'modified_at': timestamp_cb(i),
                'language': locale,
                'position': i
            })
            data.update(kwargs)
            data.update({
                'slug': slugify(data['title'])
            })
            page = Page(data)
            workspace.save(page, message=u'Added page %s.' % (i,))
            pages.append(page)

        workspace.refresh_index()
        return pages

    def create_localisation(self, workspace, locale='eng_GB', **kwargs):
        data = {'locale': locale}
        data.update(kwargs)
        localisation = Localisation(data)
        workspace.save(
            localisation, message=u'Added localisation %s.' % locale)
        workspace.refresh_index()
        return localisation

    def get_settings(self, workspace, **overrides):
        settings = {
            'git.path': workspace.repo.working_dir,
            'es.index_prefix': workspace.index_prefix,
            'cache.enabled': 'false',
            'cache.regions': 'long_term, default_term',
            'cache.long_term.expire': '1',
            'cache.default_term.expire': '1',
            'available_languages': "[('eng_GB', 'English'),"
                                   " ('urd_IN', 'Urdu')]",
            'pyramid.default_locale_name': 'eng_GB',
            'thumbor.security_key': 'sample-security-key',
            'thumbor.server': 'http://some.site.com',
            'unicorehub.host': 'http://hub.unicore.io',
            'unicorehub.app_id': 'sample-app-id',
            'unicorehub.app_password': 'sample-password',
            'unicorehub.redirect_to_https': None,
        }
        settings.update(overrides)
        return settings
