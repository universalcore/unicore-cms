import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'waitress',
    'pyramid_beaker',
    'python-memcached',
    'webtest',
    'cornice',
    'praekelt_pyramid_celery',
    'pyramid_redis',
    'unicore-gitmodels',
    'praekelt-python-gitmodel>=0.1.2'
]

setup(name='unicore-cms',
      version='0.2.2',
      description='JSON based CMS for Universal Core',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
      "Programming Language :: Python",
      "Framework :: Pyramid",
      "Topic :: Internet :: WWW/HTTP",
      "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Praekelt Foundation',
      author_email='dev@praekelt.com',
      url='http://github.com/praekelt/unicore-cms',
      license='BSD',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="cms",
      entry_points="""\
      [paste.app_factory]
      main = cms:main
      """,
      )
