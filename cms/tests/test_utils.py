from cms.views.utils import Paginator
from cms.tests.base import UnicoreTestCase


class TestPaginator(UnicoreTestCase):

    def test_first_page(self):
        paginator = Paginator(range(100), 0)
        self.assertTrue(paginator.has_next_page())
        self.assertFalse(paginator.has_previous_page())
        self.assertEqual(paginator.total_pages(), 10)
        self.assertEqual(paginator.page_numbers(),  [0, 1, 2, 3, 4])
        self.assertFalse(paginator.needs_start_ellipsis())
        self.assertTrue(paginator.needs_end_ellipsis())

    def test_last_page(self):
        paginator = Paginator(range(100), 9)
        self.assertFalse(paginator.has_next_page())
        self.assertTrue(paginator.has_previous_page())
        self.assertEqual(paginator.total_pages(), 10)
        self.assertEqual(paginator.page_numbers(),  [5, 6, 7, 8, 9])
        self.assertTrue(paginator.needs_start_ellipsis())
        self.assertFalse(paginator.needs_end_ellipsis())

    def test_middle_page(self):
        paginator = Paginator(range(100), 4)
        self.assertTrue(paginator.has_next_page())
        self.assertTrue(paginator.has_previous_page())
        self.assertEqual(paginator.total_pages(), 10)
        self.assertEqual(paginator.page_numbers(),  [2, 3, 4, 5, 6])
        self.assertTrue(paginator.needs_start_ellipsis())
        self.assertTrue(paginator.needs_end_ellipsis())

    def test_show_start(self):
        paginator = Paginator(range(100), 3)
        self.assertTrue(paginator.show_start())
        self.assertFalse(paginator.needs_start_ellipsis())

    def test_show_end(self):
        paginator = Paginator(range(100), 7)
        self.assertTrue(paginator.show_start())
        self.assertTrue(paginator.needs_start_ellipsis())
        self.assertTrue(paginator.show_end())
        self.assertFalse(paginator.needs_end_ellipsis())
