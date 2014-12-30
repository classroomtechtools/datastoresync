from distutils.core import setup
setup(
    name = "datastoresync",
    packages = ['dss'],
    version = "1.0",
    description = "Framework for defining syncing operations for databases",
    author = "Adam Morris",
    author_email = "amorris@mistermorris.com",
    #keywords = ["moodle"],
    #install_requires = ['click', 'pexpect', 'sqlalchemy', 'psycopg2'],
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        ],
    # entry_points='''
    #     [console_scripts]
    #     sync=cli.main:main
    # ''',
    long_description = """\
TODO: DESCRIBE THIS!

This version requires Python 3 or later.
"""
)
