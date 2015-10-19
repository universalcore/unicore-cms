import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

with open(os.path.join(here, 'requirements.txt')) as f:
    requires = filter(None, f.readlines())

with open(os.path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(name='unicore-cms',
      version=version,
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
      url='http://github.com/universalcore/unicore-cms',
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
