import os
import math
from functools import wraps
from urlparse import urlparse

from pyramid.i18n import TranslationStringFactory

from elasticgit.search import RepoHelper


translation_string_factory = TranslationStringFactory(None)


class Paginator(object):

    """A thing that helps us page through result sets"""

    def __init__(self, results, page, results_per_page=10, slider_value=5):
        self.results = results
        self.page = page
        self.results_per_page = results_per_page
        self.slider_value = slider_value
        self.buffer_value = self.slider_value / 2

    def total_count(self):
        return len(self.results)

    def get_page(self):
        return self.results[self.page * self.results_per_page:
                            (self.page + 1) * self.results_per_page]

    def has_next_page(self):
        return ((self.page + 1) * self.results_per_page) < self.total_count()

    def has_previous_page(self):
        return self.page

    def total_pages(self):
        return int(
            math.ceil(
                float(self.total_count()) / float(self.results_per_page)))

    def page_numbers(self):
        if (self.page - self.buffer_value) < 0:
            return [page_number
                    for page_number in range(
                        0, min([self.slider_value, self.total_pages()]))]
        elif (self.page + self.buffer_value) >= self.total_pages():
            return [page_number
                    for page_number in range(
                        max((self.total_pages() - self.slider_value), 0),
                        self.total_pages())
                    ]
        else:
            return range(self.page - self.buffer_value,
                         self.page + self.buffer_value + 1)

    def page_numbers_left(self):
        page_numbers = self.page_numbers()
        if not any(page_numbers):
            return False
        return page_numbers[:page_numbers.index(self.page)]

    def page_numbers_right(self):
        page_numbers = self.page_numbers()
        if not any(page_numbers):
            return False
        return page_numbers[page_numbers.index(self.page) + 1:]

    def needs_start_ellipsis(self):
        page_numbers = self.page_numbers()
        if not any(page_numbers):
            return False
        return page_numbers[0] > 1

    def needs_end_ellipsis(self):
        page_numbers = self.page_numbers()
        if not any(page_numbers):
            return False
        return page_numbers[-1] < (self.total_pages() - 2)

    def show_start(self):
        page_numbers = self.page_numbers()
        if not any(page_numbers):
            return False
        return page_numbers[0] > 0

    def show_end(self):
        page_numbers = self.page_numbers()
        if not any(page_numbers):
            return False
        return page_numbers[-1] < self.total_pages() - 1


class EGPaginator(Paginator):

    def total_count(self):
        return self.results.count()

    def get_page(self):
        return to_eg_objects(super(EGPaginator, self).get_page())


class ResultGenerator(object):

    def __init__(self, es_results):
        self.es_results = es_results

    def __iter__(self):
        return (obj.to_object() for obj in self.es_results)

    def __len__(self):
        return self.es_results.__len__()

    def __getitem__(self, k):
        if isinstance(k, slice):
            return ResultGenerator(self.es_results.__getitem__(k))
        return self.es_results.__getitem__(k).to_object()


def to_eg_objects(es_results):
    return ResultGenerator(es_results)


def ga_context(context_func):
    """
    A decorator for Cornice views that allows one to set extra parameters
    for Google Analytics tracking::
        @ga_context(lambda context: {'dt': context['category'].title, })
        @view_config(route_name='page')
        def view(request):
            return {
                'category': self.workspace.S(Category).filter(title='foo')[0],
            }
    :param func context_func:
        A function which takes one argument, a context dictionary made
        available to the template.
    :returns:
        A dict containing the extra variables for Google Analytics
        tracking.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            context = func(self, *args, **kwargs)
            self.request.google_analytics.update(context_func(context))
            return context
        return wrapper
    return decorator


def parse_repo_name(repo_url):
    pr = urlparse(repo_url)
    _, _, repo_name_dot_ext = pr.path.rpartition('/')
    if any([
            repo_name_dot_ext.endswith('.git'),
            repo_name_dot_ext.endswith('.json')]):
        repo_name, _, _ = repo_name_dot_ext.partition('.')
        return repo_name
    return repo_name_dot_ext


def is_remote_repo_url(repo_url):
    return any([
        repo_url.startswith('http://'),
        repo_url.startswith('https://')])


def repo_url(repo_dir, repo_location):
    # If repo_location is an http URL we leave it as is and
    # assume it specifies a unicore.distribute repo endpoint.
    # If repo_location is not an http URL, we assume it specifies
    # a local repo in repo_dir.
    if is_remote_repo_url(repo_location):
        return repo_location
    return os.path.abspath(os.path.join(repo_dir, repo_location))


class CachingRepoHelper(RepoHelper):
    """
    A subclass of RepoHelper that caches the repo's active
    branch name to avoid remote calls to get the repo branch.
    """

    def active_branch_name(self):
        if not hasattr(self, '_active_branch_name'):
            self._active_branch_name = super(
                CachingRepoHelper, self).active_branch_name()
        return self._active_branch_name
