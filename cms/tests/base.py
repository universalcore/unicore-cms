import os
from datetime import datetime

from unittest import TestCase

from elasticgit import EG

from slugify import slugify

from unicore.content.models import Category, Page


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
            self, workspace, names=[u'Diarrhoea', u'Hygiene'], locale='eng_UK',
            featured_in_navbar=False):
        categories = []
        for name in names:
            category = Category({
                'title': name,
                'language': locale,
                'featured': featured_in_navbar,
                'slug': slugify(name)})

            workspace.save(
                category, u'Added %s Category' % (name,))
            categories.append(category)

        workspace.refresh_index()
        return categories

    def create_pages(
            self, workspace, count=2, timestamp_cb=None, locale='eng_UK',
            **kwargs):
        timestamp_cb = (
            timestamp_cb or (lambda i: datetime.utcnow().isoformat()))
        pages = []
        for i in range(count):
            data = {}
            data.update(kwargs)
            data.update({
                'title': u'Test Page %s' % (i,),
                'content': u'this is sample content for pg %s' % (i,),
                'modified_at': timestamp_cb(i),
                'language': locale
            })
            page = Page(data)
            workspace.save(page, message=u'added page %s' % (i,))
            pages.append(page)

        workspace.refresh_index()
        return pages
