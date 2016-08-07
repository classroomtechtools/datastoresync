"""
Defines DataStoreTree mechanism for core functionality of datastoresync
It is responsible for keeping the store
"""

import inspect, sys
from collections import defaultdict, OrderedDict
import importlib
import logging
from dss.utils import split_import_specifier, define_action
log = logging.getLogger(__name__)
import re
import os, pickle

verbose = False

class DataStoreTreeMeta(type):

    # The store is the actual instances that holds the data
    _store = defaultdict(OrderedDict)

    # A single place for the 
    _storeobjects = {}

    def __init__(cls, name, bases, attrs):
        """
        Augments the tree to have branches
        """
        # Give each class a reference to me
        # which makes this metaclass a kind of singleton, only one of them per application
        # And thus the objects are actually stored in this metaclass, but made available in the trees and branches
        cls._metastore = cls.__class__

        branches = attrs.get('_branches')
        verbose and print("branches in {} started off as {}...".format(cls.__name__, branches))
        if branches:
            # Migrate the _branches attribute from string to a tuple:
            # (module, class)
            migrate_to = []
            if not isinstance(branches, list):
                branches = [branches]
            for branch in branches:
                # At this point, branch is a string,
                # split it into the module to be imported, and the class in that imported module
                module_to_import, class_to_import = split_import_specifier(branch)
                mod = importlib.import_module(module_to_import)
                clss = getattr(mod, class_to_import)

                # Provide references to the class, and append
                clss._datastore = cls.__class__
                migrate_to.append( (mod, clss) )

            # Make the change
            cls._branches = migrate_to
            verbose and print("\t....changed to {}".format([(m.__name__, c.__name__) for m, c in migrate_to]))

            # Now that we have the raw information, we can go about making our branches,
            # Which we do by picking up subclasses of the classes that the developer indicated

            # Cycle through all the classes that have been declared in this module, so we can augment
            # LIMITATION: Classes have to be declared in the same module as the string name
            for mod, clss in cls._branches:
                get_all_module_classes = inspect.getmembers(mod, inspect.isclass)
                # Now go through all classes in this particular module
                for class_name, class_reference in get_all_module_classes:
                    branch_name = getattr(class_reference, '_branchname', class_reference.__name__)

                    if class_reference is not clss:  # check to ensure our heuristic doesn't detect itself
                        if issubclass(class_reference, clss): # now see if this object is subclass of class represented by `pickup`
                            class_reference._treename = cls.__name__
                            class_reference._tree = cls
                            class_reference._qualname = branch_name
                            setattr(cls, branch_name, class_reference)
                            verbose and print("Setting attribute {} on {} to {}".format(branch_name, cls.__name__, class_reference.__name__))
                        else:
                            pass
                    else:
                        # detected itself, which will happen once per each branch
                        # this is by design incorrect, because branch classes are declared and then subclasses are picked up
                        pass
        # THIS IS NEW
        super().__init__(name, bases, attrs)

class DataStoreTree(metaclass=DataStoreTreeMeta):

    def __init__(self, do_import=False, read_from_disk=None, write_to_disk=None, filter_=None):
        """
        Detects the sets up the declared template
        """
        if hasattr(self, '_template'):
            self.set_template(self._template)

        # if do_import:
        #     +self

        self.read_from_disk = read_from_disk
        self.write_to_disk = write_to_disk
        self.set_filter(filter_)

        return super().__init__()

    def __repr__(self):
        return "<Datastore Tree '{}', with {} branches: [{}]>".format(self.__class__.__name__, len(self.branches), ",".join(b.name for b in self.branches))

    def set_filter(self, filter_):
        """
        filter_ should be a dict
        """
        self._filter = filter_

    def set_template(self, template_import_specifier):
        """
        Converts the template_import_specifier into the class
        (it is initialized lazily)
        """
        mod_name, clss = split_import_specifier(template_import_specifier)
        module = importlib.import_module(mod_name)
        self._template = getattr(module, clss)

    @property
    def metastore(self):
        return self.__class__._metastore

    @classmethod
    def branch_classes(cls):
        return [b[1] for b in cls._branches]

    @property
    def branches(self):
        """
        Returns list of branch objects
        """
        ret = []
        # Loop through anything that might be a branch...
        # We're using dir(), so have to filter out 'branches' and 'store' properies to avoid infinite recursion
        # TODO: Better is to filter out any properties and just look at classes
        for attr in [a for a in dir(self) if a == a.lstrip('_') and not a.startswith('branch') and not a.startswith('store') and not a in self.exclude]:
            attribute = getattr(self, attr)
            for branch_class in self.branch_classes():
                try:
                    if attribute is not branch_class and issubclass(attribute, branch_class):
                        ret.append(attribute)
                except TypeError:
                    # TypeError raised when issubclass is passed a non-class obj in the first argument
                    # TODO: When debugging, this is annoying
                    pass
        return ret

    @property
    def branch_fullnames(self):
        return [s.fullname for s in self.branches]

    @property
    def branch_names(self):
        return [s.name for s in self.branches]

    @property
    def store(self):
        return {k: v for k, v in self.__class__._metastore._store.items() if k in self.branch_fullnames}

    @property
    def datastore(self):
        return self.__class__._metastore._store

    @classmethod
    def branch(cls, name):
        """
        Take a name string and convert it to the branch
        """
        return getattr(cls, name, None)

    def output(self, other, stream=None):
        if stream is None:
            import sys
            stream = sys.stdout
        self.wheel(other, template=lambda x: stream(x.message))

    def wheel(self, other, template=None):
        if template is None:
            template = self._template

        for action in self - other:
            template(action)

    def test_model(self, other):
        #self.set_template('dss.templates.DefaultTemplate')
        for action in self - other:
            if action.error:
                print(action.message)
        print("test of model is complete. no news is good news.")

    exclude = ['output', 'wheel', 'exclude']

    def __rshift__(self, other):   # >>
        if not hasattr(other, '_template'):
            print("No template defined for me")
            return
        template = other._template()

        not_implemented = set()
        for action in self - other:
            if other._filter and len([1 for k in other._filter.keys() if getattr(action, k) == other._filter[k]]) == len(list(other._filter.keys())):
                result = template(action)
            else:
                result = template(action)
            if result is None:
                not_implemented.add(action.func_name)
            elif template.result_bool(result) is True:
                template.success(action, result)
            else:
                template.fail(action, result)
        print("Not implemented:\n{}".format(", ".join(list(not_implemented))))


    def __gt__(self, other):   # >
        self.wheel(other, template=lambda action: print(action.message))

    def __pos__(self):         # +
        """
        Cycles through the branches, discovering importers as we go:
        Importers are used to read in the data, and also provides optional hooks
        such as 'filter_out'
        """
        if self.read_from_disk:
            # We can check to see if it has already been in by looking at the keys
            if len(list(self.__class__._metastore._store.keys())) == 0:
                self.__class__._metastore._store = pickle.load(self.read_from_disk)
            else:
                pass # already read in, no need, and results in segment fault if attempted again
            return

        # Sort by order in order to ensure properties can be brought in
        branches = self.branches[:]
        branches = [b for b in branches if b.fullname.startswith(self.__class__.__name__)]
        branches.sort(key=lambda o: o.order)
        #

        for branch in branches:
            importer_string = getattr(branch, '_importer', None)
            verbose and print('Declared importer for {} branch of {} is "{}"'.format(branch.fullname, self.__class__.__name__, importer_string))
            if importer_string is None:
                # ensure we don't fail if there is no importer defined, just print a message for the moment
                print('No importer?')
                return
            importer_mod_string, class_string = split_import_specifier(importer_string)
            try:
                importer_mod = importlib.import_module(importer_mod_string)
            except ImportError:
                raise ImportError("Datastore tried to import via string {} given by {} but failed.".format(importer_mod_string, class_string))
            importer = getattr(importer_mod, class_string, None)
            if not importer:
                print("Importing defined by {} could not be imported".format(importer_string))
                Returns
            importer_inst = importer(self, branch)
            verbose and print("Importer instance for {} branch of {}: {}...".format(branch.fullname, self.__class__.__name__, importer_inst._branch.fullname))
            importer_inst._branchname = branch._branchname
            importer_filter = getattr(importer_inst, 'filter_out', None)
            kwargs_preprocessor = getattr(importer_inst, 'kwargs_preprocessor', None)
            verbose and importer_filter and print("Detected importer filter")
            verbose and kwargs_preprocessor and print("Detected kwargs preprocessor")

            # Readin from the importer, and 'make' the data objects as we go
            # the built-in make method is smart about storing things correctly

            reader = importer_inst.reader
            temp = defaultdict(list)

            if reader is None:
                verbose and print("\t...No context manager, using generator instead")
                i = 0

                for kwargs_in in importer_inst.readin():
                    if kwargs_preprocessor:
                        kwargs = kwargs_preprocessor(kwargs_in)
                    else:
                        kwargs = kwargs_in

                    has_list_value = len([1 for k in kwargs.keys() if isinstance(kwargs[k], (list,set))]) > 0
                    if not 'idnumber' in kwargs:
                        kwargs['idnumber'] = str(i)
                        i += 1
                    if has_list_value:
                        temp[kwargs['idnumber']].append(kwargs)
                    else:
                        self.make_them(branch, importer_filter, **kwargs)
            else:
                verbose and print("\t...Using context manager")
                with importer_inst.reader() as reader:
                    i = 0
                    for kwargs_in in reader:
                        if kwargs_preprocessor:
                            kwargs = kwargs_preprocessor(kwargs_in)
                        else:
                            kwargs = kwargs_in
                        has_list_value = len([1 for k in kwargs.keys() if isinstance(kwargs[k], (list,set))]) > 0
                        if not 'idnumber' in kwargs:
                            kwargs['idnumber'] = i
                            i += 1
                        if has_list_value:
                            temp[kwargs['idnumber']].append(kwargs)
                        else:
                            self.make_them(branch, importer_filter, **kwargs)

            if len(temp.keys()) > 0:
                for idnumber in temp.keys():
                    prepared = {}
                    kwargs_list = temp[idnumber]
                    for item in kwargs_list:
                        for list_key in [k for k in item.keys() if isinstance(item[k], list)]:
                            if list_key not in prepared:
                                prepared[list_key] = []
                            prepared[list_key].extend(item[list_key])
                            del item[list_key]
                        for set_key in [k for k in item.keys() if isinstance(item[k], set)]:
                            if set_key not in prepared:
                                prepared[set_key] = set()
                            try:
                                prepared[set_key].update(item[set_key])
                            except AttributeError:
                                from IPython import embed;embed();exit()
                            del item[set_key]
 
                        # Add the additional ones, too
                        prepared.update(item)

                        self.make_them(branch, importer_filter, **prepared)

    def make_them(self, branch, filter_callable, **kwargs):
        # Remove any kwargs and leave only those static ones

        if filter_callable is not None:
            if not filter_callable(**kwargs):
                obj = branch.make(**kwargs)
        else:
            obj = branch.make(**kwargs)

        # # Now augment these objects with _underline properties passed in kwargs
        # for key,value in list_kwargs.items():
        #     if not hasattr(obj, key):
        #         setattr(obj, key, [])
        #     getattr(obj, key).extend(value)

    def __neg__(self):
        """
        Removes the branches from the store
        """
        for branch in self.branches:
            key = branch.fullname
            del self._metastore._store[key]

    def __sub__(self, other):
        """
        Mimicks syncing, yields objects
        """

        # Import information using the defined templates, if any
        # TODO: Leave out?
        # +self
        # +other

        branches = [b for b in self.branch_names if not b.startswith('_')]

        # filter out any branches that have been augmented to skip
        branches = [b for b in branches if not (hasattr(self.branch(b), '_sub') and not self.branch(b)._sub)]
        branches.sort(key=lambda b: self.branch(b).order)
        #

        for branch in branches:
            this_branch = self.branch(branch)
            that_branch = other.branch(branch)

            for key in this_branch.keys() - that_branch.keys():
                left = this_branch.get(key)
                right = that_branch.get(key)
                yield define_action(key, left, right, 'idnumber', "new_{}(idnumber={})".format(branch, key), None)

        for branch in branches:
            this_branch = self.branch(branch)
            that_branch = other.branch(branch)

            for item_key in this_branch.keys():
                this_item = this_branch.get(item_key)
                that_item = that_branch.get(item_key)

                if this_item and that_item and this_item is that_item:
                    # The objects on both sides are one and the same (and not None)
                    # because the datastore only creates significant unique items once
                    # so it's guaranteed that there are no differences to explore, therefore, short circuit any comparisons
                    continue
                else:
                    # Have the objects themselves compare to each other
                    yield from this_item - that_item

        for branch in branches:
            this_branch = self.branch(branch)
            that_branch = other.branch(branch)

            for key in that_branch.keys() - this_branch.keys():
                left = this_branch.get(key)
                right = that_branch.get(key)
                yield define_action(key, left, right, key, "old_{}(idnumber={})".format(branch, key), None)
