from dss.models.base import Base

# First define the model

class User(Base):
	pass

class StudentInModel(User):
	pass

class TeacherInModel(User):
	pass

class StudentBranch:
	__branchname__ = 'students'

class TeacherBranch:
	__branchname__ = 'teachers'


# Now define the branches

from dss.datastore.branch import DataStoreBranches

class CSVDataStoreBranches(DataStoreBranches):
	pass

class CSVStudents(CSVDataStoreBranches, StudentBranch):
	klass = '__main__/StudentInModel'

class CSVTeachers(CSVDataStoreBranches, TeacherBranch):
	klass = '__main__/TeacherInModel'

class DBDataStoreBranches(DataStoreBranches):
	pass

class DBStudents(DBDataStoreBranches, StudentBranch):
	klass = '__main__/StudentInModel'

class DBTeachers(DBDataStoreBranches, TeacherBranch):
	klass = '__main__/TeacherInModel'


# Now define the Importers

from dss.importers import DefaultImporter
import csv

class CSVImporter(DefaultImporter):

	def __init__(self, tree):
		self.tree = tree

	def readin_branch(self, branch):
		with open('/tmp/{}'.format(branch.fullname())) as csvfile:
			reader = csv.reader(csvfile)
			for line in reader:
				branch.make(*line)


# Now define the templates

from dss.templates import DefaultTemplate

class CSVTemplate(DefaultTemplate):
	pass

from dss.datastore.tree import DataStoreTree

class CSVTree(DataStoreTree):
	__branches__ = '__main__/CSVDataStoreBranches'
	__importer__ = '__main__/CSVImporter'
	__template__ = '__main__/CSVTemplate'

class DatabaseTree(DataStoreTree):
	__branches__ = '__main__/DBDataStoreBranches'
	__importer__ = '__main__/CSVImporter'
	__template__ = '__main__/CSVTemplate'


# Ready to rock'n'roll

if __name__ == "__main__":

	from IPython import embed
	embed()

	#Initialize the branches
	left = CSVTree()
	right = DatabaseTree()

	#Use the importers to populate the data
	+left
	+right

	#Loop through the differences and print/output
	for action in left - right:
		print(action.message)

	#Use the template to sync
	left >> right

