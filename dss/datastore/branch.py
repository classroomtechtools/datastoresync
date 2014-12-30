from dss.utils import string_to_module_class
import importlib

class DataStoreBranchMeta(type):
	def __init__(cls, name, bases, attrs):
		klass = attrs.get('klass')
		if klass:
			mod, clss = string_to_module_class(klass)
			mod = importlib.import_module(mod)
			cls.klass = getattr(mod, clss)

class DataStoreBranches(metaclass=DataStoreBranchMeta):
	"""
	"""
	__set_outerclass__ = True

	def __init__(self, idnumber):
		pass

	@classmethod
	def datastore(cls):
		return cls.__datastore__

	@classmethod
	def outer_store(cls):
		return cls.__datastore__.__store__

	@classmethod
	def store(cls):
		return cls.__datastore__.__store__[cls.fullname()]

	@classmethod
	def fullname(cls):
		if hasattr(cls, '__treename__') and hasattr(cls, '__qualname__'):
			return cls.__treename__ + '.' + cls.__qualname__
		else:
			return cls.__name__

	@classmethod
	def name(cls):
		return cls.__qualname__

	@classmethod
	def is_new(cls, idnumber):
		return not idnumber in cls.keys()

	@classmethod
	def keys(cls):
		return cls.store().keys()

	@classmethod
	def keys_startswith(cls, startswith):
		return [key for key in cls.store().keys() if key.startswith(startswith)]

	@classmethod
	def items(cls):
		yield from cls.store().items()

	@classmethod
	def del_key(cls, key):
		del cls.store()[key]

	@classmethod
	def del_all_keys(cls, key):
		for key in cls.keys():
			cls.del_key(key)

	@classmethod
	def iter(cls):
		for key, value in cls.store().items():
			yield value

	@classmethod
	def iter_items(cls):
		yield from cls.store().items()

	@classmethod
	def get_objects(cls):
		return cls.store().values()

	@classmethod
	def get_object_n(cls, n):
		list(cls.get_objects())[n]

	@classmethod
	def get(cls, key):
		return cls.store().get(key)

	@classmethod
	def get_from_attribute(cls, attr, value):
		for item in cls.get_objects():
			if getattr(item, attr) == value:
				return item
		return None

	@classmethod
	def get_from_username(cls, value):
		return get_from_attribute(cls, 'username', value)

	@classmethod
	def get_all_from_attribute(cls, attr, value):
		l = []
		for item in cls.get_objects():
			if getattr(item, attr) == value:
				l.append(item)
		return l

	@classmethod
	def find_one_with_callback(cls, callback):
		for item in cls.get_objects():
			if callback(item):
				return item

	@classmethod
	def set_key(cls, key, value):
		cls.outer_store()[cls.fullname()][key] = value

	@classmethod
	def will_make_new(cls, new, *args, **kwargs):
		pass

	@classmethod
	def did_make_new(cls, new, *args, **kwargs):
		"""
		HOOK METHOD CALLED AFTER `make` MAKES A NEW ONE
		"""
		pass

	@classmethod
	def will_return_old(self, old, *args, **kwargs):
		pass

	@classmethod
	def make(cls, idnumber, *args, **kwargs):
		"""
		Returns the object if already created, otherwise makes a new one
		Can be overridden if desired
		idnumber should the identifying idnumber, otherwise a callable to derive it
		"""
		if callable(idnumber):
			# FIX: Can't remember why I made this!
			# Nothing seems to use it!
			idnumber = idnumber(*args, **kwargs)
		if cls.is_new(idnumber):
			# Instantiate the instance
			new = cls.klass(idnumber, *args, **kwargs)
			cls.will_make_new(new, *args, **kwargs)
			cls.set_key(idnumber, new)
			cls.did_make_new(new, *args, **kwargs)
			return new
		else:
			old = cls.get(idnumber)
			cls.will_return_old(old, *args, **kwargs)
			return old

