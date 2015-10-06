default_excluded_paths = ['/health/', '/api/notify/']


def excluded_path(path, excluded_paths):
    excl_paths = excluded_paths.split(',') + default_excluded_paths
    return (
        path and
        any([p for p in excl_paths if path.startswith(p)]))
