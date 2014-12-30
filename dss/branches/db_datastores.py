from dss.branches.common import Students, Teachers
from dss.branches.branch import DataStoreBranches

class DBDataStoreBranches(DataStoreBranches):
	pass

class DBStudents(Students, DBDataStoreBranches):
	klass = 'dss.models.users/Student'

class DBTeachers(Teachers, DBDataStoreBranches):
	klass = 'dss.models.users/Teacher'