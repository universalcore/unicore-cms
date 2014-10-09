from cms.utils import CmsRepo


class ApiBase(object):

    def __init__(self, request):
        self.request = request
        self.repo_path = self.request.registry.settings['git.path']
        self.repo = CmsRepo.read(self.repo_path)

    def get_registered_ws(self):
        return self.repo.get_workspace()

    def get_repo_models(self):
        return self.repo.get_models()
