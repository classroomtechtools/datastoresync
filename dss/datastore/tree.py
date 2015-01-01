"""
Defines DataStoreTree mechanism for core functionality of datastoresync
"""


import inspect, sys
from collections import defaultdict, OrderedDict
import importlib
import logging
from dss.utils import string_to_module_class, define_action
log = logging.getLogger(__name__)
import re

class DataStoreTreeMeta(type):

    # The store is the actual instances that holds the data
    __store__ = defaultdict(OrderedDict)
    __storeobjects__ = {}

    def __init__(cls, name, bases, attrs):
        # Give each class a reference to myself
        cls.__datastore__ = cls.__class__

        branches = attrs.get('__branches__')
        if branches:
            # Adjust the branches attribute from string(s) to a tuple
            # with the module and the class inside the module
            change_to = []
            if not isinstance(branches, list):
                branches = [branches]
            for branch in branches:
                module_to_import, class_to_import = string_to_module_class(branch)
                mod = importlib.import_module(module_to_import)
                clss = getattr(mod, class_to_import)
                clss.__datastore__ = cls.__class__
                change_to.append( (mod, clss) )
            cls.__branches__ = change_to
            

            # Cycle through all the classes that have been declared in this module, so we can augment this class with those ones
            # Limitation: You have to declare your branches in the same place as this module
            # TODO: Get around above limitation by passing a string and importing that way

            for mod, clss in cls.__branches__:
                get_all_module_classes = inspect.getmembers(mod, inspect.isclass)

                # Now go through all classes in this particular module
                for class_name, class_reference in get_all_module_classes:
                    branch_name = getattr(class_reference, '__branchname__', class_reference.__name__)

                    # if class_name in attrs.keys():   # ensure something with same name wasn't passed to attrs
                    #     print('in attrs keys')
                    #     declared_class = attrs[class_name]  # this is now whatever the programmer declared
                    #     if inspect.isclass(declared_class) and issubclass(declared_class, clss):
                    #         # If we're here, we need to adjust some augment, to match what we would do automatically (like below)
                    #         setattr(declared_class, '__qualname__', branch_name)
                    #         setattr(declared_class, '__datastore__', cls)
                    if class_reference is not clss:  # check to ensure our heuristic doesn't detect itself
                        if issubclass(class_reference, clss): # now see if this object is subclass of class represented by `pickup`
                            class_reference.__treename__ = cls.__name__
                            class_reference.__qualname__ = branch_name
                            setattr(cls, branch_name, class_reference)
                    else:
                        pass # ?


class DataStoreTree(metaclass=DataStoreTreeMeta):

    def __init__(self, do_import=False):
        # Must follow the convention of lowercase representing modules
        # and Uppercase representing actual classes 

        if hasattr(self, '__importer__'):
            # Re-assign the string in klass to the actual class
            # Imports the module on the way, which is used in __init__
            mod_name, clss = string_to_module_class(self.__importer__)
            module = importlib.import_module(mod_name)
            self.__importer__ = getattr(module, clss)

        if hasattr(self, '__template__'):
            mod_name, clss = string_to_module_class(self.__template__)
            module = importlib.import_module(mod_name)
            self.__template__ = getattr(module, clss)

        if do_import:
            +self

        return super().__init__()

    def __repr__(self):
        return "<{} tree of datastore, with {} branches>".format(self.__class__.__name__, len(self.branches))

    # @property
    # def trees(self):
    #     """
    #     Returns the branches in this store collection, defined as any objects in the __dict__ that are classes
    #     """
    #     return [t for t in self.store.keys() if c == c.lstrip('_') and isinstance(self.__dict__[c], type)]

    # @classmethod
    # def tree_names(cls):
    #     return [c.__name__ for c in cls.trees()]

    @property
    def datastore(self):
        return self.__class__.__datastore__

    @classmethod
    def branch_classes(cls):
        return [b[1] for b in cls.__branches__]

    @property
    def branches(self):
        ret = []
        # Loop through anything that might be a branch...
        # We're using dir(), so have to filter out 'branches' and 'store' properies to avoid infinite recursion
        # TODO: Better is to filter out any properties and just look at classes
        for attr in [a for a in dir(self) if a == a.lstrip('_') and not a.startswith('branch') and not a.startswith('store')]:
            attribute = getattr(self, attr)
            for branch_class in self.branch_classes():
                try:
                    if attribute is not branch_class and issubclass(attribute, branch_class):
                        ret.append(attribute)
                except TypeError:
                    # TypeError raised when issubclass is passed a non-class obj in the first argument
                    pass
        return ret

    @property
    def branch_fullnames(self):
        return [s.fullname() for s in self.branches]

    @property
    def branch_names(self):
        return [s.name() for s in self.branches]

    @property
    def store(self):
        return {k: v for k, v in self.__class__.__datastore__.__store__.items() if k in self.branch_fullnames}

    @classmethod
    def branch(cls, name):
        return getattr(cls, name)

    def output(self, other, stream=None):
        if stream is None:
            import sys
            stream = sys.stdout
        self.wheel(other, template=lambda x: stream(x.message))

    def wheel(self, other, template=None):
        if template is None:
            template = self.__template__

        for action in self - other:
            template(action)

    def __rshift__(self, other):   # >>
        template = other.__template__()

        for action in self - other:
            template(action)        

    def __gt__(self, other):   # >
        self.wheel(other, template=lambda action: print(action.message))

    def __pos__(self):
        """
        User the defined importer template and run it
        """
        template = getattr(self, '__importer__', None)
        template_inst = template(self)
        has_template_filter = getattr(template_inst, 'filter_out', False)
        for branch in self.branches:
            for info in template_inst.readin_branch(branch):
                if has_template_filter:
                    if not template_inst.filter_out(**info):
                        branch.make(**info)
                else:
                    branch.make(**info)

    def __neg__(self):
        for key in self.branch_names():
            if key in self.__datastore__.__store__:
                del self.__datastore__.__store__[key]            

    def __sub__(self, other):
        """
        Executes the syncing operations
        """

        # Import information using the defined templates, if any
        # TODO: Leave out?
        +self
        +other

        # Here is where the wheel turns

        for branch in self.branch_names:
            this_branch = self.branch(branch)
            that_branch = other.branch(branch)

            for key in this_branch.keys() - that_branch.keys():
                left = this_branch.get(key)
                right = that_branch.get(key)
                yield define_action(left, right, key, "new_{}(idnumber={})".format(branch, key), None)

        for branch in self.branch_names:
            this_branch = self.branch(branch)
            that_branch = other.branch(branch)

            for item_key in this_branch.keys():
                this_item = this_branch.get(item_key)
                that_item = that_branch.get(item_key)

                yield from this_item - that_item

        for branch in self.branch_names:
            this_branch = self.branch(branch)
            that_branch = other.branch(branch)

            for key in that_branch.keys() - this_branch.keys():
                left = this_branch.get(key)
                right = that_branch.get(key)
                yield define_action(left, right, key, "old_{}(idnumber={})".format(branch, key), None)
