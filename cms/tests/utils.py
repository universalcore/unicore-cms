import pygit2
import shutil
import unittest

from unicore_gitmodels import models
from cms import utils


class RepoHelper(object):

    @classmethod
    def create(cls, repo_path, name='Test Kees', email='test@example.org',
               bare=True, commit_message='initialize repository'):
        repo = pygit2.init_repository(repo_path, bare)
        author = pygit2.Signature(name, email)
        committer = author
        tree = repo.TreeBuilder().write()
        repo.create_commit(
            'refs/heads/master',
            author, committer, commit_message, tree, [])
        return cls(repo)

    @classmethod
    def read(cls, repo_path):
        return cls(pygit2.Repository(repo_path))

    def __init__(self, repo):
        self.repo = repo
        self.ws = utils.get_workspace(self.repo)
        self.ws.register_model(models.GitPageModel)
        self.ws.register_model(models.GitCategoryModel)

    @property
    def path(self):
        return self.repo.path

    def destroy(self):
        shutil.rmtree(self.path)

    def get_models(self):
        return self.ws.import_models(models)

    def create_categories(self, names=[u'Diarrhoea', u'Hygiene']):
        models = self.get_models()

        for name in names:
            category = models.GitCategoryModel(title=name)
            category.slug = category.slugify(name)
            category.save(True, message=u'added %s Category' % (name,))

    def create_pages(self, count=2):
        models = self.get_models()
        for i in range(count):
            models.GitPageModel(
                title=u'Test Page %s' % (i,),
                content=u'this is sample content for pg %s' % (i,)
            ).save(True, message=u'added page %s' % (i,))


class BaseTestCase(unittest.TestCase):
    pass
