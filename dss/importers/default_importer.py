"""
An abstract importer, can be used as is, but does nothing
"""

class DefaultImporter:
    reader = None
    _settings = None

    def __init__(self, tree, branch):
        self._tree = tree
        self._branch = branch
        self.init()

    def get_setting(self, key, default=None):
        return self._settings.get(key, default)

    def update_setting(self, key, value):
        self._settings[key] = value

    def init(self):
        """
        Inspect settings variables if needed
        """
        pass

    def readin(self, branch):
        return []
