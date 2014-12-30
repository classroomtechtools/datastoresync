from dss.utils import define_action

class Base:

	# Classes in the model need to have idnumber for syncing to be meaningful
	def __init__(self, idnumber):
		self.idnumber = idnumber

	def define_action(self, other, attribute, message, error=None):
		return define_action(self, other, attribute, message, error)

	def __sub__(self, other):
		"""
		Go through each variable/property that isn't a callable and check them out
		"""

		# Limitation: We don't process (yet?) for exact equivalencies across both objects
		#             So you could have something defined as 'x' as a callable on this side
		#             but as a callable on other side, and you won't pick up any changes.

		if not other:
			yield self.define_action(other, None, "err_no_other_obj(idnumber={})".format(self.idnumber))
			return

		for attribute in [a for a in dir(self) if a == a.lstrip('_') and not callable(getattr(self, a))]:
			try:
				this_attr = getattr(self, attribute)
			except AttributeError:
				yield self.define_action(other, attribute, "err_no_attr(attribute={},which='this')".format(attribute))
				continue
			try:
				that_attr = getattr(other, attribute)
			except AttributeError:
				yield self.define_action(other, attribute, "err_no_attr(attribute={},which='that'".format(attribute))
				continue

			if this_attr != that_attr:
				yield self.define_action(other, attribute, "different_attr(idnumber={},attribute={})".format(attribute, self.idnumber))

if __name__ == "__main__":

	b = Base('1234')
	b.test = 4
	c = Base('5678')
	c.test = 5

	for item in b - c:
		print(item.message)  # prints out "different_attr (idnumber) @1234: 1234 != 5678\ndifferent_attr (test) @1234: 4 != 5"