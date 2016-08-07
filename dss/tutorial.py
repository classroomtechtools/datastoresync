# First we need to define the trees, and then the branches as well. We do that by making a class and indicating in the 
# _branches class variable a dotted notation to the path of the class. 
# The tree will then pick up any subclass of this defined class, and "append" it to the tree as a branch

from dss.datastore.tree import DataStoreTree
from dss.datastore.branch import DataStoreBranches

class users_branch_mixin:
    """ Just define the name, i.e. source.users """
    _name = 'users'

class groups_branch_mixin:
    _name = 'groups'

class SourceBranches(DataStoreBranches):
    """ subclasses of this will be picked up by dss framework """
    pass

class Source(DataStoreTree):
    """ Our source tree """
    _branches = '__main__.SourceBranches'

from dss.models import Base

class SourceUser(Base):
    """ 
    Each object in source.users is an instance of this class

    No __init__ method is required, you can assume that the object has been augmented with
    self.properties where properties are the columns provided in the CSV.
    """

    @property
    def name(self):
        """
        The importer populates the objects, but the source data does not have a "name"
        just a "lastfirst", so we define the name property as a derivation of the lastfirst one.
        Note that this lastfirst property starts with an underscore which indicates that the framework
        should ignore it.
        """
        self.lastname, self.firstname = [s.strip(' ') for s in self._lastfirst.split(',')]
        return "{firstname} {lastname}".format(self)

class SourceUsersBranch(SourceBranches, users_branch_mixin):
    """ 
    The source.users branch uses the SourceImporter for the importer
    and the SourceUser class for the objects
    """
    _klass = '__main__.SourceUser'
    _importer = '__main__.SourceImporter'

from dss.importers import CSVImporter

class SourceImporter(CSVImporter):
    def get_path(self):
        return "/tmp/file.csv"   # or wherever

    # def readin(self):
    #      this function does not need to be defined because the imported class has code that handles it

# class Dest(DataStoreTree):
#     _branches = '__main__.DestBranches'

# class DestUser(DestBranches):
#     _name = ''


# class MyPGImporter(dss.importers.PostgressImporter):
#     def readin(self):
#         """
#         Importers that define a readin function need to provide a 
#         Code to use sqlalchemy is missing for simplicity's sake
#         """
#         with self.dbsession() as session:
#             yield from session.query(Users).all()

source = Source()
#dest = Dest()
