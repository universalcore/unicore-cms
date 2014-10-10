import shutil
import unittest

from cms.utils import CmsRepo


class RepoHelper(CmsRepo):

    @classmethod
    def create(cls, repo_path, name='Test Kees', email='kees@example.org',
               bare=False, commit_message='Initialising Repository.'):
        return cls.init(repo_path=repo_path, name=name, email=email,
                        bare=bare, commit_message=commit_message)

    @property
    def path(self):
        return self.repo.path

    @property
    def workdir(self):
        return self.repo.workdir

    def destroy(self):
        CmsRepo.expire(self)
        try:
            shutil.rmtree(self.workdir)
        except:
            pass

    def create_categories(
            self, names=[u'Diarrhoea', u'Hygiene'], locale='eng_UK',
            featured_in_navbar=False):
        models = self.get_models()
        categories = []
        for name in names:
            category = models.GitCategoryModel(title=name, language=locale)
            category.featured_in_navbar = featured_in_navbar
            category.slug = category.slugify(name)
            category.save(True, message=u'added %s Category' % (name,))
            categories.append(
                models.GitCategoryModel().get(category.uuid))

        return categories

    def create_pages(self, count=2, timestamp_cb=None, locale='eng_UK'):
        timestamp_cb = timestamp_cb or (lambda i: None)
        models = self.get_models()
        pages = []
        for i in range(count):
            page = models.GitPageModel(
                title=u'Test Page %s' % (i,),
                content=u'this is sample content for pg %s' % (i,),
                modified_at=timestamp_cb(i),
                language=locale)
            page.save(True, message=u'added page %s' % (i,))
            pages.append(models.GitPageModel().get(page.uuid))

        return pages


class BaseTestCase(unittest.TestCase):
    pass
