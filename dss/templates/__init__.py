debug = True

class DefaultTemplate:

	def __call__(self, action):
		debug and print(action.message)
		try:
			func_str = action.message[:action.message.index('(')]
		except ValueError:
			print("WRONG FORMAT")
			return
		try:
			func = getattr(self, func_str)
		except AttributeError:
			return
		func(action)

class CSV(DefaultTemplate):
	pass

class DB(DefaultTemplate):
	pass