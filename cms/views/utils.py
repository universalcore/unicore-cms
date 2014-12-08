import math


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
