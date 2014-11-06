CHANGELOG
=========

1.0.10
-----
- Ensure featured pages in category on homepage are ordered by position (ascending)

1.0.9
-----
- Ensure featured pages in category on homepage are ordered by position

1.0.8
-----
- Autodeployment with travis - attempt 2

1.0.7
-----
- Autodeployment with travis - attempt 1

1.0.6
-----
- Enforce ordering for pages and categories using `position`

1.0.5
-----
- Added date formatting helper

0.6.3
-----
- Redirect to homepage after changing language

0.6.2
-----

- Better wrapper around repos & workspaces to make moving away from
  pygit2 easier.

0.6.1
-----

- Fix for workspace caching

0.6.0
-----

- Cache workspace to reduce number of open files

0.5.0
-----

- Views now return actual objects instead of dictionaries
  to the template contexts.

0.4.3
-----
-  Fixed bug when filtering multiple language pages by slug

0.4.2
-----
-  Pages now render markdown

0.4.1
-----
-  Change default cache duration to 10mins

0.4.0
-----
-  Allow content to be featured on homepage

0.3.2
-----
-  Ensure setting locale always redirects

0.3.1
-----
-  Fix error when checking language for cached category/page

0.3.0
-----
-  Allow content to be filtered by language selection

0.2.8
-----
-  Add support for flat pages

0.2.7
-----
-  Add caching to `get_featured_category_pages`

0.2.6
-----
-  Added sensible default for available_languages

0.2.5
-----
-  Added support for translations

0.2.4
-----
-  Allow top nav to be global variable

0.2.2
-----
-  Use `utils.get_workspace()` to avoid duplication

0.2.2
-----
-  Fix development.ini file

0.2.1
-----
-  Bump required version for praekelt-python-gitmodel

0.2
---
-  Added `git.content_repo_url` for cloning when app starts

0.1
---
-  Initial version
