CHANGELOG
=========
1.10.1
------
- Add endpoint for retreiving repo names

1.10.0
------
- Add marathon version info to health check

1.9.8
-----
- Fix parsing of result_per_page configuration option (it's passed in as a
  string and needed to be parsed into an integer).

1.9.7
-----
- Fix bug that prevented the results_per_page configuration option
  from having an effect on the number of pages displayed in a
  category listing.

1.9.6
-----
- Add pagination to category listings

1.9.5
-----
- use latest version of elastic-git (pins elasticsearch==1.7.0)

1.9.4
-----
- Exclude health checks from GA analytics

1.9.3
-----
- Add uswgi to dependencies

1.9.0
-----
- Support remote repos via unicore.distribute.
- Remove auto-cloning of repo on startup.

1.8.1
-----
- Add fallbacks for unsupported languages
- Ensure GA Titles are specified for static pages

1.8.0
-----
- Add comments using unicore.comments.client
- Handle non-existent category in page and category views
- Add page/category title context to GA

1.7.1
-----
- pin cornice to 1.0.0

1.7.0
-----
- Add auth using unicore.hub.client
- pin cornice to 0.18.1

1.6.6
-----
- Remove cornice version pinning

1.6.5
-----
- Consistently convert ES objects to `elastic-git` model objects

1.6.4
-----
- Add localised logo support

1.6.3
-----
- Ensure detail page doesn't break for flat pages

1.6.2
-----
- Use latest changes of EG (Changes to Avro schema)

1.6.1
-----
- provide es host in fastforward

1.6.0
-----
- Add branded 404 page
- Allow reading of `es.host` from config

1.5.2
-----
- Refactor Search templates

1.5.1
-----
- Ensure list of languages in change page is sorted

1.5.0
-----
- Change language selector to allow featured languages

1.4.2
-----
- Allow querystring-less locale url

1.4.1
-----
- Fix tests breaking because of latest elasticsearch

1.4.0
-----
- Add support for Google Analytics tracking
- Add backend support for search.

1.3.1
-----
- Ensure localisation is fastforwarded

1.3.0
-----
- Add localisation support to schema

1.2.2
-----
- Change order of get_image_url params

1.2.1
-----
- Use `image_host` from json

1.2.0
-----
- Add image support to view

1.1.1
-----
- Use custom locale negotiator

1.1.0
-----
- Added image field to model
- Add fallback for Swahili and English UK

1.0.13
-----
- Use not_analyzed for language field

1.0.12
-----
- Ensure `get_page` returns None instead of 404

1.0.11
-----
- Ensure sensible default for ordering pages (default: position)

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
