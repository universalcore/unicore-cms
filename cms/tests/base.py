import os
from datetime import datetime

from unittest import TestCase

from elasticgit import EG

from slugify import slugify

from unicore.content.models import Category, Page, Localisation


class UnicoreTestCase(TestCase):

    destroy = 'KEEP_REPO' not in os.environ

    def mk_workspace(self, working_dir='.test_repos/',
                     name=None,
                     url='https://localhost',
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
