import re, importlib
from collections import namedtuple

ActionItem = namedtuple("ActionItem", ['this', 'that', 'attribute', 'message', 'error'])

def define_action(this, that, attribute, message, error):
	return ActionItem(this, that, attribute, message, error)

def string_to_module_class(the_string):
	"""
	Eg) 'module.submodule.Class' string return tuple 'module.submodule', 'Class'
	"""
	return the_string.split('/')