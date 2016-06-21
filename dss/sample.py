import re

# DATA

# First define the basic user properties applicable to all users, we'll implement the kind field as an enum

from enum import Enum
class Kind(Enum):
	student = 0
	teacher = 1
	administrator = 2
	undefined = -1

from dss.models import Base

class BaseUser(Base):
	"""
	All the tracked properties should not begin with an underscore
	Tracked properties will include those passed to __init__ as kwarg args (as long as they don't begin with underscore)

	Programmer can define properties on the class that are derived from tracked properties
	If they don't begin with an underscore, they also will be tracked.

	Being "tracked" refers to noticing differences and syncing them across, as defined by the - and >> operators.

	user = BaseUser(firstname='Adam', lastname="Apple")
	user.name  # "Adam Apple"

	Remember to call super().__init__ if you override init!

	No __init__ method needed, as this is taken care of in Base
	"""

	# properties that do not have underscore are also tracked
	kind = Kind.undefined

	@property
	def name(self):
		return self.firstname + ' ' + self.lastname

	def __repr__(self):
		return "<User {}:{}>".format(self.idnumber, self.name)

# Now define properties of students and teachers that apply to them all
class BaseStudent(BaseUser):
	"""
	Every Student has a homeroom, and we decide instead of getting the grade from the information system, 
	to derive the grade from the homeroom...
	...this decision will cause a bug if there are any student who doesn't have a homeroom but does have a grade
	"""
	kind = Kind.student

	@property
	def grade(self):
		"""
		Remove anything from the homerooom string that isn't numerical
		"""
		return re.sub('[^0-9]', '', self.homeroom)

	def __repr__(self):
		return "<Student {}:{}, homeroom {} at {}>".format(self.idnumber, self.name, self.homeroom, hex(id(self)))

class BaseTeacher(BaseUser):
	kind = Kind.teacher

	def __repr__(self):
		return "<Teacher {}:{}>".format(self.idnumber, self.name)


class LeftStudent(BaseStudent):
	"""
	Students in our information system don't have a username yet, so we derive it ourselves
	And, for us, usernames are defined as:
	firstname + lastname + year of graduation
	Which is a calculation
	"""
	@property
	def username(self):
		return (self.firstname + self.lastname + self._year_of_graduation()).lower().replace(' ', '')

	# The following methods are not tracked:
	def _year_of_graduation(self):
		"""
		Do the math, and then remove the '20' from the year
		Underscore, because this is not information we are tracking
		"""
		return str((12 - int(self.grade)) + self._this_year())[:2]

	def _this_year(self):
		# Very rudimentary, better to use calendar to check the current year
		# But reminds us that an underscore is needed here because this isn't information we are tracking
		return 2016

class RightStudent(BaseStudent):
	pass

class LeftTeacher(BaseTeacher):
	pass

class RightTeacher(BaseTeacher):
	pass




# BRANCHES

from dss.datastore.branch import DataStoreBranches

# First define a few that we can use to ensure the branches have the same names throughout
class StudentBranch:
	__branchname__ = 'students'

class TeacherBranch:
	__branchname__ = 'teachers'

# We can override anything in the defined DataStoreBranches if necessary
class OurBranches(DataStoreBranches):
	"""
	Since we use an enum above, we have to define how to serialize it
	which we can do by defining the __jsonencoder__ method
	DataStoreBranches will wrap this with json.JSONEncoder
	and the method body will be used for the json.JSONEncoder.default method
	"""
	def __jsonencoder__(obj):
		"""
		The value for the "kind" (or any enum found in a branch)
		becomes {"kind": value}
		"""
		if isinstance(obj, Enum):
			return obj.name

# Define LeftBranches, which will take different classes from the model
# This is essential, because they will likely have different beahviours when it comes to which side
# of the branch they are on, because information might be on the left but not on right

class LeftBranches(OurBranches):
	pass

class RightBranches(OurBranches):
	pass

class LeftStudents(LeftBranches, StudentBranch):
	klass = '__main__/LeftStudent'

class LeftTeachers(LeftBranches, TeacherBranch):
	klass = '__main__/LeftTeacher'

class RightStudents(RightBranches, StudentBranch):
	klass = '__main__/RightStudent'

class RightTeachers(RightBranches, TeacherBranch):
	klass = '__main__/RightTeacher'





# IMPORTERS

# Our case is simple, we'll just make them programmatically
# Importers are responsible for yielding a dictionary of the information

from dss.importers import DefaultImporter

class LeftImporter(DefaultImporter):

	def readin_branch(self, branch):
		if branch.name() == 'students':
			yield dict(idnumber='newstudent', firstname='Joe', lastname='Shmoe', homeroom='5A')
			yield dict(idnumber='12345', firstname='Flow', lastname='Maiden', homeroom='10B')
			yield dict(idnumber='67890', firstname='Apple', lastname='Daisy', homeroom='2M')
		elif branch.name() == 'teachers':
			yield dict(idnumber='newteacher', firstname='Fred', lastname='Maiden')
			yield dict(idnumber='1111', firstname='Pretty', lastname='in Pink')
			yield dict(idnumber='2222', firstname='Joeanne', lastname='Shmoe')

class RightImporter(DefaultImporter):

	def filter_out(self, **info):
		"""
		You can define a function that inspects the information looking for stuff to filter out
		"""
		if info.get('idnumber') == '0000':
			return True
		return False

	def readin_branch(self, branch):
		if branch.name() == 'students':
			yield dict(idnumber='12345', firstname="Flow", lastname='Maiden', homeroom='10B', username="wrong")
			yield dict(idnumber='67890', firstname='Apple', lastname='Daisy', homeroom='2M', username="appledaisy20")
			yield dict(idnumber='oldstudent', firstname="Goodbye", lastname="Everyone", homeroom="1A", username="goodbyeeveryone16")
		elif branch.name() == 'teachers':
			yield dict(idnumber='0000', firstname="Teacher", lastname="Filtered Out")
			yield dict(idnumber='1111', firstname="Pretty", lastname="in Pink")
			yield dict(idnumber='2222', firstname="Joeanne", lastname="Shmoe")
			yield dict(idnumber='oldteacher', firstname="no", lastname="yes")

# Now define the templates

from dss.templates import DefaultTemplate

class RightTemplate(DefaultTemplate):
	
	def new_students(self, action):
		student = action.left
		print("New student! Hurray... name is {} in homeroom {}".format(student.name, student.homeroom))

	def new_teachers(self, action):
		teacher = action.left
		print("New teacher! ID is {}".format(teacher.idnumber))

	def different_username(self, action):
		_from = action.right.username
		_to = action.left.username
		if action.right.kind == Kind.student:
			print("Change {}'s {} from {} to {}".format(action.right, action.attribute, _from, _to))
		elif action.right.kind == Kind.teacher:
			print("Cannot change teacher usernames so easily!")





# TREES
# Define the trees, which ties it altogether
# All we do is write the strings for the import paths and classes to use

from dss.datastore.tree import DataStoreTree

class LeftTree(DataStoreTree):
	__branches__ = '__main__/LeftBranches'
	__importer__ = '__main__/LeftImporter'
	# No template required on left side

class RightTree(DataStoreTree):
	__branches__ = '__main__/RightBranches'
	__importer__ = '__main__/RightImporter'
	__template__ = '__main__/RightTemplate'

if __name__ == "__main__":
	# ROCK N ROLL

	#Initialize the branches
	#Sets up all the magic, will automatically import the data (if an importer is defined)
	left = LeftTree()
	right = RightTree()

	+left
	+right

	left > right

	#Syncs by finding the differences, and then calling the template
	left >> right

