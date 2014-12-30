datastoresync
=============

This is narrative introduction to the concepts and general practice with this framework. A more comprehensive, code-only introduction can be found in the main_example.py file contained in this repository.

CONTEXT
=======

You have two databases, maybe one of them is a School Information System, the other is Virtual Learning Environment. You need a framework for syncing those two databases. There's also an LDAP that needs the information as well.

REAL-WORLD EXAMPLE
==================

datastoresync was invented for schools, so we'll use an example common in schools. For our school, PowerSchool (SIS) is the singple point of truth, and Moodle (VLE) is used for daily teacher-student interactions, we operate a Google Apps for Education (GAFE) domain, and LDAP is used for authentication and account management between both.

PROBLEM STATEMENT
=================

How can we keep these various tools and their databases integrated in a systematic way, that allows us to define exactly what information is carried over to where? What would the tool used to do exactly that look like, and how would it work? For example, how would we get the SIS information, which is stored as a CSV file, into the Moodle database?

SOLUTION
========

A datastore here is a structure that has symmetrical trees and branches. They are symmetrical in that they hold the same kind of information based on the same model, but with different content. Differences between these two branches represent operations that must take place in order to sync. For example, when a new student arrives, the tree 'csv_tree' will contain information about the new student in the "student" branch, but 'db_tree' will not have that info. When a currently enrolled student changes courses, both contain the student, but has different course information.

Our framework should make this process straight-forward to program such syncing procedures.

DATASTORE TREES
===============

We don't create the datastore itself, it is a magical structure residing in the background; we just define trees by subclassing from DataStoreTree, thereby inheriting mechanisms that allow us to define our branches and model structure. 

	class CSVTree(DataStoreTree):
		__branches__ = 'branches/CSVBranches'

	class DBTree(DataStoreTree):
		__branches__ = 'branches/DBBranches'

	csv_tree = CSVTree()

The first part of the __branches__ string (before the slash) defines the import path, after the slash is the class name. What this does is tell datastoresync which classes will be added NewClass. In the file located in branches.py:

	# First some generic class definitions:
	class Students:
		__branchname__ = "students"	

	class Teachers:
		__branchname__ = "teachers"

	# Now the meat of it
	class CSVBranches(DataStoreBranch): pass

	class CSVStudents(Students, CSVBranches): pass

	class CSVTeachers(Teachers, CSVBranches): pass

	class DBBranches(DataStoreBranch): pass

	class DBStudents(Students, DBBranches): pass

	class DBTeachers(Teachers, DBBranches): pass

With this configuration, then we have the following behaviour:

	csv_tree = CSVTree()
	db_tree = DBTree()

	csv_tree.students   # the class 'dss.branches.students'
	db_tree.teachers    # the class 'dss.branches.teachers'

	csv_tree.branches   # [dss.branches.students, dss.branches.teachers]

(Note: 'dss' = 'datastoresync')

In this way, we have a single object, a magical class in the background which is our "datastore", that has two trees, one for each kind of database we have, each of which has a 'students' and 'teachers' branch. We access them through instances of DataStoreTree.

DATASTORE MODEL
===============

The idea is that each of these branches need to hold dictionaries for our model. So how do we define the object that represents these items?

	class CSVStudents(Students, CSVBranches): 
		klass = 'models.users/Student'

	class DBStudents(Students, DBBranches): 
		klass = 'models.users/Student'

The string before the slash represents the import path while after is the name of the class. To make a student, we have access to the make method, and what it does is makes an instance of the class defined by klass:

	csv_tree.students.klass            # returns class 'Student' defined in models.users
	csv_tree.students.make(idnumber)   # returns a new student with idnumber, eg. '12345'
	csv_tree.students.get(idnumber)    # returns the student with idnumber, or None if it doesn't exist

If you change the Student class __init__ method with additional parameters, you'll likewise have to add parameters to the make method. Our mechanisms requires an idnumber, however, because these idnumbers are keys in a dictionary, and have to be unique. Common practice is that these idnumbers are primary IDs.

You can access the populated items via the branch's store method.

	csv_tree.students.store()         # {'CSVTree.students': OrderedDict([('12345': <models.users.Student object>)])}

For some insight on how this is actually stored, the magical datastore itself keeps a hash table (actually a defaultdict) which you can inspect like this:

	csv_tree.datastore.__tree__      
	# defaultdict(..., {'CSVTree.students': OrderedDict([('12345': <models.users.Student object>)])})

The store magically keeps info with keys like "<treename>.<branchname>". At the branch level, only the keys relevant to that particular branch are accessible with the 'store' method.

DISCOVERING DIFFERENCES IN THE MODEL
====================================

The datastore trees mechanism also provides a way to easily detect differences between any two trees. All one has to do is use the minus operator to generate the differences:

	csv_tree - db_tree     # returns a generator that outputs dss.utils.action objects with differences described

This operation (defined in the tree's '__sub__' method) will compare the keys that are in each branch, detect which ones are "new" (exists in the left side but not in the right) and which are "old" (exists in the right side but not the left), and additionally any properties in each object and if there is any change in content.

The idiom is thus:

	left ("what we need") - right ("what we have")

So the single point of truth "database" (which for us is just a CSV file) is on the left and the target of the syncing procedures is on the right.

This mechanism requires to adequately compare properties of objects in the model. When defining the model, for example the "Student" class above, you can overload the subtraction operator, __sub__, if you need more specific behavior, but the default behaviour is to look through each non-callable property and check to see if they are equal. Inequality will result in an action objecting being generated.

HANDLER TEMPLATES
=================

In order to define what happens when certain differences are detected, we can define templates that are called for each action. To that end, consider this:

	for action in csv_tree - db_tree:
		print(action)

That will just print a bunch of dss.utils.action objects, which have 'left', 'right', 'attribute', 'message', and 'error' properties. But to be useful, instead of printing we should send it to an instance of a template class, and we can define the template class at the tree-level, like this:

	class DBTree(DataStoreTree):
		__branches__ = 'branches/DBBranches'
		__template__ = 'templates/DBTemplate'	

and whose template can be evoked for each action detected, with the "rshift" operator:

	csv_tree >> db_tree

which essentially uses the subtraction operator to get the differences as an action object, and passes that on to an instance of the template defined with the "what we have" template. The "rshift" operator was chosen because visually it is doing what the handler is supposed to, bringing over, like an arrow, information from the left to the right. In this case, you'll want to use a template handler class that is sophisticated enough to look at the action objects created and automatically call methods that are defined within. So the idea is to write a template handler like this:

	class DBTemplate(dss.templates.DefaultTemplate):   # uses provided DefaultTemplate class

		# methods are called when certain actions need to take place
		def new_students(self, action):
			new_student = action.right   # the object is passed to the action.right property
			print("New student, whose name is " + new_student.name)

Note that the "what we have" template is used, because that is the template that should know what operations to commence in order for the syncing to complete.

Note that the trees can be evoked as such:

	csv_tree > db_tree

which simply outputs the found differences in a human-readable format, useful for debugging.

IMPORTERS
=========

So how are the datastores populated with information? The programmer can define importer classes whose job it is to call the 'make' method on each relevant branch. The importer is defined on the tree in the same way branches and templates are:

	class CSVDataStores(DataStoreTree):
		__branches__ = 'dss.branches.csv_datastores/CSVDataStoreBranches'
		__importer__ = 'importers.csv/CSV'

and the template is evoked with the following idiom:

	+csv_tree

This will cycle through each branch and call the template's 'readin_branch' method, passing the branch object as the first parameter. It's up to the importer class on what happens next.

To clear the populated info:

	-csv_tree

WRAPPING IT UP
==============

This following summarizes with code the above:

	from dss.tree import DataStoreTree

	class CSVTree(DataStoreTree):
		__branches__ = 'branches/CSVBranches'
		__importer__ = 'importers/CSV'
		__template__ = 'templates/CSV'

	class DatabaseTree(DataStoreTree):
		__branches__ = 'branches/DBBranches'
		__importer__ = 'importers/CSV'
		__template__ = 'templates/DB'

	if __name__ == "__main__":

		#Initialize the branches
		csv_tree = CSVTree()
		db_tree = DatabaseTree()

		#Use the importers to populate the data
		+csv_tree
		+db_tree

		#Loop through the differences and print/output
		#Equivelent to csv_tree > db_tree
		for action in csv_tree - db_tree:
			print(action.message)

		#Use the template to sync
		csv_tree >> db_tree
