
from dss.utils import define_action
from collections import OrderedDict
import json

class Base:
    """
    REMIND: Everything defined here has to begin (or end) with an underscore to avoid collisions in the framework.
    """

    # Classes in the model need to have idnumber for syncing to be meaningful
    def __init__(self, idnumber, **kwargs):
        self.idnumber = idnumber
        for key in kwargs:
            try:
                setattr(self, key, kwargs[key])
            except AttributeError:
                print("Cannot set {} {}".format(key, self))  # should be a log instead of a print


    # def _jsonencoder(self, obj):
    #     """
    #     The value for the "kind" (or any enum found in a branch)
    #     becomes {"kind": value}
    #     """
    #     if isinstance(obj, set):
    #         # Sets have to be sorted lists, in order to ensure the character sequence is correct
    #         return sorted(list(obj))
    #     raise TypeError("Property of {} of type {} cannot be converted to json; please provide _jsonencoder method.".format(obj, type(obj)))

    def _kwargs(self):
        """
        Responsible for providing the kwargs that will be passed onto the importer
        Returns a tuple: (global_idnumber, kwargs_dict)
        """
        all_properties = self._get_all_properties()
        if hasattr(self, '_jsonencoder'):
            this = self
            # FIXME: Let's declare this class outside of this local scope...
            class json_encoder(json.JSONEncoder):
                def default(self, obj):
                    return this._jsonencoder(obj)
            global_idnumber = json.dumps( (self.idnumber, all_properties), cls=json_encoder)
        else:
            global_idnumber = json.dumps( (self.idnumber, all_properties))

        return global_idnumber, all_properties

    def _get_all_properties(self):
        ret = OrderedDict()
        keys = self.__class__._keys if hasattr(self.__class__, '_keys') else [k for k in sorted(dir(self)) if k == k.strip('_')]
        for key in keys:
            attr = getattr(self, key)
            # lists need to be sorted to be meaningful
            ret[key] = getattr(self, key) if not isinstance(attr, list) else sorted(attr)
        if not hasattr(self.__class__, '_keys'):
            # Cache it forevermore
            self.__class__._keys = keys
        return ret

    # TODO: Delete me: No reason
    # def _get_from_branch_attr(self, specifier):
    #     branch, attr = specifier.split('/')
    #     b = getattr(self._tree, branch)
    #     a = getattr(self, attr)
    #     if b is None:
    #         raise AttributeError("{} doesn't have {} branch".format(self, branch))
    #     return b.get(a)

    # def _get_from_branch_attrs(self, *specifiers):
    #     l = []
    #     for spec in specifiers:
    #         branch, attr = spec.split('/')
    #         b = getattr(self._tree, branch)
    #         a = getattr(self, attr)
    #         if b is None:
    #             raise AttributeError("{} doesn't have {} branch".format(self, branch))
    #         l.append( b.get(a) )
    #     return l

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
                yield define_action(self.idnumber, self, other, attribute, "err_no_attr(idnumber={},attribute={}, which='{}.{}')".format(self.idnumber, attribute, self._origtreename, self._branchname), True)
                continue
            try:
                that_attr = getattr(other, attribute)
            except AttributeError:
                yield define_action(self.idnumber, self, other, attribute, "err_no_attr(idnumber={}, attribute={}, which='{}.{}')".format(self.idnumber, attribute, other._origtreename, self._branchname), True)
                continue

            if type(this_attr) != type(that_attr):
                yield define_action(self.idnumber, self, other, attribute, "err_integrity(attribute={}, left_type='{}', right_type='{}', which='{}.{}')".format(attribute, type(this_attr), type(that_attr), self._origtreename, self._branchname), True)

            if isinstance(this_attr, list):  # both are lists
                for to_add in set(this_attr) - set(that_attr):
                    yield define_action(other.idnumber, self, other, to_add, "add_{attribute}_to_{branch}(idnumber={idnumber}, to={to_}, attribute={attribute}, which='{which}')".format(idnumber=other.idnumber, attribute=attribute, to_=to_add, branch=other._branchname, which='{}.{}'.format(other._origtreename, other._branchname)), None)
                for to_remove in set(that_attr) - set(this_attr):
                    yield define_action(other.idnumber, self, other, to_remove, "remove_{attribute}_from_{branch}(idnumber={idnumber}, to={to_}, attribute={attribute}, which='{which}')".format(idnumber=other.idnumber, attribute=attribute, to_=to_remove, branch=other._branchname, which='{}.{}'.format(self._origtreename, self._branchname)), None)

            elif isinstance(this_attr, set):  # both are sets
                for to_add in this_attr - that_attr:
                    yield define_action(other.idnumber, self, other, to_add, "add_{attribute}_to_{branch}(idnumber={idnumber}, to={to_}, attribute={attribute}, which='{which}')".format(idnumber=other.idnumber, attribute=attribute, to_=to_add, branch=other._branchname, which='{}.{}'.format(other._origtreename, other._branchname)), None)
                for to_remove in that_attr - this_attr:
                    yield define_action(other.idnumber, self, other, to_remove, "remove_{attribute}_from_{branch}(idnumber={idnumber}, to={to_}, attribute={attribute}, which='{which}')".format(idnumber=other.idnumber, attribute=attribute, to_=to_remove, branch=other._branchname, which='{}.{}'.format(self._origtreename, self._branchname)), None)

            elif this_attr != that_attr:
                yield define_action(self.idnumber, self, other, this_attr, "update_{}(idnumber={}, left_value={}, right_value={})".format(attribute, self.idnumber, getattr(self, attribute), getattr(other, attribute)), None)

    def __repr__(self):
        """
        Only output fields that are guaranteed to be there to avoid attribute errors
        Outputs the branchname because classname would be ambiguous
        """
        return "<{}: {}>".format(self._branchname, self.idnumber)

if __name__ == "__main__":

    b = Base('1234')
    b.test = 4
    c = Base('5678')
    c.test = 5

    for item in b - c:
        print(item.message)  # prints out "different_attr (idnumber) @1234: 1234 != 5678\ndifferent_attr (test) @1234: 4 != 5"