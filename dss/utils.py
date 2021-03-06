import re, importlib
from collections import namedtuple

ActionItem = namedtuple("ActionItem", ['idnumber', 'source', 'dest', 'attribute', 'message', 'func_name', 'error'])

def define_action(idnumber, source, dest, attribute, message, error):
    func_name = message[:message.index('(')]
    return ActionItem(idnumber, source, dest, attribute, message, func_name, error)

def split_import_specifier(the_string):
    """
    Eg) 'module.submodule.Class' string return tuple 'module.submodule', 'Class'
    """
    split = the_string.split('.')
    return (".".join(split[:-1]), split[-1])
