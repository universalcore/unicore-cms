import os

from pyramid import testing

from mock import patch

from cms.tests.base import UnicoreTestCase
from cms.tasks import pull


class TestTasks(UnicoreTestCase):

    def setUp(self):
        self.config = testing.setUp()
        celery_config = self.mk_configfile({
            'celery': {
                'celery_always_eager': 'true'}
            })
        self.config.include('pyramid_celery')
        self.config.configure_celery(celery_config)

    def tearDown(self):
        testing.tearDown()

    @patch('cms.tasks.RemoteStorageManager')
    @patch('cms.tasks.EG.workspace')
    def test_pull(self, mocked_workspace, mocked_rsm):
        local_repo_url = os.path.abspath('foo')
        remote_repo_url = 'http://localhost/repos/foo.json'
        es = {'urls': ['http://host:port']}

        pull.delay(local_repo_url, index_prefix='foo', es=es)
        mocked_workspace.assert_called_once_with(
            local_repo_url,
            index_prefix='foo',
            es=es)
        mocked_workspace.pull.assert_called_once()
        mocked_rsm.assert_not_called()

        mocked_workspace.reset_mock()
        pull.delay(remote_repo_url, index_prefix='foo', es=es)
        mocked_rsm.assert_called_once_with(remote_repo_url)
        mocked_rsm.pull.assert_called_once()
        mocked_workspace.assert_not_called()
