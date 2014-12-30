import imp
from dss.tree import DataStoreTree

class CSVTree(DataStoreTree):
	__branches__ = 'dss.branches.csv_datastores/CSVDataStoreBranches'
	__importer__ = 'importers.csv/CSV'
	__template__ = 'templates/CSV'

class DatabaseTree(DataStoreTree):
	__branches__ = 'dss.branches.db_datastores/DBDataStoreBranches'
	__importer__ = 'importers.csv/CSV'
	__template__ = 'templates/DB'

if __name__ == "__main__":

	#Initialize the branches
	csv_side = CSVTree()
	db_side = DatabaseTree()

	#Use the importers to populate the data
	+csv_side
	+db_side

	#Loop through the differences and print/output
	for action in csv_side - db_side:
		print(action.message)

	from IPython import embed
	embed()

	#Use the template to sync
	csv_side >> db_side

