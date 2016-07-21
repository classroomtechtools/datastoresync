from dss.importers import DefaultImporter
import csv
from contextlib import contextmanager
from collections import defaultdict

verbose = False

class CSVImporter(DefaultImporter):

    def init(self):
        if self.get_setting('delimiter') == '\\t':
            self.update_setting('delimiter', '\t')

    def get_path(self):
        return self.get_setting('path')

    @contextmanager
    def reader(self):
        """
        Return the reader iterable object
        """
        resolved_path = self.get_path()

        fieldnames = self.get_setting('{}_columns'.format(self._branch.name), None)

        if not fieldnames:
            pass
            # Then it must be in the file itself, yes? TODO: Check for this, raise exception if not
            # It's doubtful that tools would export with the equivelent names that the syncing needs
            # so this probably needs to be fixed
        else:
            fieldnames = fieldnames.split(' ')

        with open(resolved_path) as f:
            reader = csv.DictReader(f, 
                fieldnames=fieldnames,
                delimiter=self.get_setting('delimiter'))
            yield reader

class TranslatedCSVImporter:
    """
    Make-shift 
    """
    csv_importers = defaultdict(list)
    reader = None  # tells tree to use generator instead of a contextmanager

    def __init__(self, tree, branch):
        """
        Mimick the DefaultImporter's __init__, passed onto TranslatedCSVImporter.__init__
        """
        self._tree = tree
        self._branch = branch
        for key in self.translate:
            for value in self.translate[key]:
                inst = self.klass(tree, branch)
                assert inst._branch.fullname == branch.fullname
                verbose and print("\tInside {} made instance of {} which has {}".format(self._branch.fullname, self.klass.__name__, inst._branch.fullname))

                # Verbose way of ensuring that value changes to the value at the time this is run
                # otherwise we would always return the same thing
                inst.file_hook = (lambda v: lambda p : p.replace(key, v))(value)
                # 

                self.csv_importers[self.__class__.__name__].append(inst)

    def readin(self):
        verbose and print("Reading in with {} importers".format(len(self.csv_importers)))
        for csv_importer in self.csv_importers[self.__class__.__name__]:
            verbose and print("{} using importer {}...".format(self._branch.fullname, csv_importer))
            # TODO: Use the tree's procedure for this
            reader = csv_importer.reader
            filter_callable = getattr(csv_importer, 'filter_out', None)
            kwargs_preprocessor = getattr(csv_importer, 'kwargs_preprocessor', None)

            assert self._branch.fullname == csv_importer._branch.fullname
            if reader is None:
                verbose and print("\t...Reading in using generator for {}".format(csv_importer._branch.fullname))
                for kwargs_in in csv_importer.readin():
                    if kwargs_preprocessor:
                        kwargs = kwargs_preprocessor(kwargs_in)
                    else:
                        kwargs = kwargs_in
                    if filter_callable:
                        if not filter_callable(**kwargs):
                            yield kwargs
                    else:
                        yield kwargs
            else:
                verbose and print("\t...Reading in using context manager for {}".format(csv_importer._branch.fullname))
                with csv_importer.reader() as reader:
                    for kwargs_in in reader:
                        if kwargs_preprocessor:
                            kwargs = kwargs_preprocessor(kwargs_in)
                        else:
                            kwargs = kwargs_in

                        if filter_callable:
                            if not filter_callable(**kwargs):
                                yield kwargs
                        else:
                            yield kwargs

