
class DefaultImporter:
	__settings__ = None

	def __init__(self, tree):
		self.tree = tree
		self.init()

	def get_setting(self, key, default=None):
		return self.__settings__.get(key, default)

	def update_setting(self, key, value):
		self.__settings__[key] = value

	def init(self):
		"""
		Inspect settings variables if needed
		"""
		pass

	def readin_branch(self, branch):
		pass
