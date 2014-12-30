from dss.importers import DefaultImporter
import csv

class CSV(DefaultImporter):

	def __init__(self, tree):
		self.tree = tree

	def readin_branch(self, branch):
		with open('/tmp/{}'.format(branch.fullname())) as csvfile:
			reader = csv.reader(csvfile)
			for line in reader:
				branch.make(*line)