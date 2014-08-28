import re
import unicodedata

RE_NUMERICAL_SUFFIX = re.compile(r'^[\w-]*-(\d+)+$')

from gitmodel import fields, models


class FilterMixin(object):

    @classmethod
    def filter(cls, **fields):
        items = list(cls.all())
        for field, value in fields.items():
            if hasattr(cls, field):
                items = [a for a in items if getattr(a, field) == value]
            else:
                raise Exception('invalid field %s' % field)
        return items


class SlugifyMixin(object):

    def slugify(self, value):
        """
        Normalizes string, converts to lowercase, removes non-alpha characters,
        and converts spaces to hyphens.
        """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
        return re.sub('[-\s]+', '-', value)

    def generate_slug(self):
        if hasattr(self, 'title') and self.title:
            if hasattr(self, 'slug') and not self.slug:
                self.slug = self.slugify(unicode(self.title))[:40]

    def save(self, *args, **kwargs):
        self.generate_slug()
        return super(SlugifyMixin, self).save(*args, **kwargs)


class Category(FilterMixin, SlugifyMixin, models.GitModel):
    slug = fields.SlugField(required=True)
    title = fields.CharField(required=True)

    def __eq__(self, other):
        if not other:
            return False

        if isinstance(other, dict):
            return self.slug == other['slug']
        return self.slug == other.slug

    def __ne__(self, other):
        if not other:
            return True

        if isinstance(other, dict):
            return self.slug != other['slug']
        return self.slug != other.slug

    def to_dict(self):
        return {
            'uuid': self.id,
            'slug': self.slug,
            'title': self.title,
        }


class Page(FilterMixin, SlugifyMixin, models.GitModel):
    slug = fields.SlugField(required=True)
    title = fields.CharField(required=True)
    content = fields.CharField(required=False)
    published = fields.BooleanField(default=True)
    primary_category = fields.RelatedField(Category, required=False)

    def to_dict(self):
        primary_category = self.primary_category.to_dict()\
            if self.primary_category else None

        return {
            'uuid': self.id,
            'slug': self.slug,
            'title': self.title,
            'content': self.content,
            'published': self.published,
            'primary_category': primary_category,
        }
