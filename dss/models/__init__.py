from dss.utils import define_action
from collections import OrderedDict

class Base:
	"""
	REMIND: Everything defined here has to begin (or end) with an underscore to avoid collisions in the framework.
	"""

	# Classes in the model need to have idnumber for syncing to be meaningful
	def __init__(self, idnumber, **kwargs):
		self.idnumber = idnumber
		for key in kwargs:
			setattr(self, '_'+ key, kwargs[key])

	def _get_all_properties(self):
		ret = OrderedDict()
		for key in [k for k in sorted(dir(self)) if k == k.strip('_')]:
			ret[key] = getattr(self, key)
		return ret

	def _define_action(self, other, attribute, message, error=None):
		return define_action(self, other, attribute, message, error)

	def __sub__(self, other):
		"""
		Go through each variable/property that isn't a callable and check them out
		"""

		# Limitation: We don't process (yet?) for exact equivalencies across both objects
		#             So you could have something defined as 'x' as a callable on this side
		#             but as a callable on other side, and you won't pick up any changes.

		if not other:
			# This will be picked up in the key comparisons, so skip it
			return

		for attribute in [a for a in dir(self) if a == a.lstrip('_') and not callable(getattr(self, a))]:
			try:
				this_attr = getattr(self, attribute)
			except AttributeError:
				yield self._define_action(other, attribute, "err_no_attr(attribute={},which='left')".format(attribute))
				continue
			try:
				that_attr = getattr(other, attribute)
			except AttributeError:
				yield self._define_action(other, attribute, "err_no_attr(attribute={},which='right')".format(attribute))
				continue

			if this_attr != that_attr:
				yield self._define_action(other, attribute, "different_{}(idnumber={}, left_value={}, right_value={})".format(attribute, self.idnumber, getattr(other, attribute), getattr(self, attribute)))

if __name__ == "__main__":

	b = Base('1234')
	b.test = 4
	c = Base('5678')
	c.test = 5

	for item in b - c:
		print(item.message)  # prints out "different_attr (idnumber) @1234: 1234 != 5678\ndifferent_attr (test) @1234: 4 != 5"