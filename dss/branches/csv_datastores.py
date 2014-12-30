from dss.branches.common import Students, Teachers
from dss.branches.branch import DataStoreBranches

class CSVDataStoreBranches(DataStoreBranches):
	pass

class CSVStudents(CSVDataStoreBranches, Students):
	klass = 'dss.models.users/Student'

class CSVTeachers(CSVDataStoreBranches, Teachers):
	klass = 'dss.models.users/Teacher'
