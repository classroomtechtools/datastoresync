"""
Branches, in concept, are part of the tree that is one level down from the root
Root is never accessed, just the branch
and then, in the branch, you have sub-branches, which represent data that is to be synced

The data is stored as represented by an object in the model
It is stored in a private construct and is shadowed in the branches
Every object should have an 'idnumber', and every object is 
"""

from dss.utils import split_import_specifier
import importlib
import json

class DataStoreBranchMeta(type):
    displaynum = 3

    def __init__(cls, name, bases, attrs):
        klass = attrs.get('_klass')
        if klass:
            # Doing this at this level means that it cannot be changed,
            # only delcarative methods are possible
            mod, clss = split_import_specifier(klass)
            mod = importlib.import_module(mod)
            cls.klass = getattr(mod, clss)
        else:
            cls.klass = None

    @property
    def name(self):
        return self._qualname

    @property
    def fullname(self):
        if hasattr(self, '_treename') and hasattr(self, '_qualname'):
            return self._treename + '.' + self._qualname
        else:
            return self.__name__

    @property
    def is_new(self, idnumber):
        return not idnumber in self.keys()

    @property
    def store(self):
        return self.datastore[self.fullname]

    @property
    def datastore(self):
        return self._datastore._store
    
    def __repr__(cls):
        return "<{} branch of {} tree, having {} members: {}>".format(cls._branchname, cls._treename, len(cls.keys()), (", ".join(list(cls.keys())[:cls.displaynum])) + ('...' if len(cls.keys()) > cls.displaynum else ""))

class DataStoreBranches(metaclass=DataStoreBranchMeta):
    """
    Branches are reponsible for making the instances, which by default does so by calling DataStoreBranches.make
    """
    order = 10000

    def __init__(self, idnumber):
        pass

    # @classmethod
    # def datastore(cls):
    #     return cls._datastore._store

    # @classmethod
    # def store(cls):
    #     return cls.datastore()[cls.fullname]


    @classmethod
    def keys(cls):
        return cls.store.keys()

    @classmethod
    def values(cls):
        return cls.store.values()

    @classmethod
    def keys_startswith(cls, startswith):
        return [key for key in cls.store.keys() if key.startswith(startswith)]

    @classmethod
    def items(cls):
        yield from cls.store.items()

    @classmethod
    def del_key(cls, key):
        del cls.store[key]

    @classmethod
    def del_all_keys(cls, key):
        for key in cls.keys():
            cls.del_key(key)

    @classmethod
    def iter(cls):
        for key, value in cls.store.items():
            yield value

    @classmethod
    def iter_items(cls):
        yield from cls.store.items()

    @classmethod
    def get_objects(cls):
        return cls.store.values()

    @classmethod
    def get_object_n(cls, n):
        list(cls.get_objects())[n]

    @classmethod
    def get(cls, key):
        return cls.store.get(key)

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
    def find_many_with_callback(cls, callback):
        ret = []
        for item in cls.get_objects():
            if callback(item):
                ret.append(item)
        return ret

    @classmethod
    def set_key(cls, key, value):
        if not hasattr(value, '_branchname'):
            value._branchname = cls._branchname
        if not hasattr(value, '_origtreename'):
            value._origtreename = cls._treename
        cls.datastore[cls.fullname][key] = value

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
    def make(cls, idnumber, **kwargs):
        """
        This is the method that ensures our objects are in the datastore

        Returns the object if already created, otherwise makes a new one
        Hooks: 
        idnumber can be a callable
        will_make_new, did_make_new: if new object
        will_return_old: if not new object
        """
        if callable(idnumber):
            # No parameters, if developer needs that they can make a partial
            idnumber = idnumber()   

        # preprocess special case when making a derivative branch
        if cls.klass is None:
            if len(kwargs.keys()) == 1 and 'object' in kwargs:
                obj = kwargs['object']
                cls.set_key(idnumber, obj)
                return obj
            else:
                input("What happens here?")
                pass

        # First, let's make the object, which we have to do no matter we use it or not
        # (we might not use it if it has already been stored)
        # because we get the global_idnumber by calling calling _get_all_properties
        # thereby getting the internal index number used to store it
        new = cls.klass(idnumber, **kwargs)
        new._tree = cls._tree
        global_idnumber = new._derive_global_idnumber()
        all_properties = new._get_all_properties()

        if not global_idnumber in cls._datastore._storeobjects:
            # Instantiate the instance, store it, call the hooks, return the new one
            cls._datastore._storeobjects[global_idnumber] = new
            cls.will_make_new(new, **all_properties)
            cls.set_key(idnumber, new)
            cls.did_make_new(new, **all_properties)
            return new
        else:
            # We'll not use 'new'
            old = cls._datastore._storeobjects[global_idnumber]
            
            # Call to `set_key` needed because it adds it to the branch that hasn't seen yet
            cls.set_key(idnumber, old)

            cls.will_return_old(old, **all_properties)
            return old

