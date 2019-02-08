from setuptools import setup, find_packages
from codecs import open
from os import path
import os
from subprocess import check_output
#Grab and write the gitVersion from 'git describe'.
gitVersion = ''
gitPath = ''

# get git describe if in git repository
print('Fetching most recent git tags')
if os.path.exists('./.git'):
	try:
		# if we are in a git repo, fetch most recent tags
		check_output(["git fetch --tags"], shell=True)
	except Exception as e:
		print(e)
		print('Unable to fetch most recent tags')

	try:
		ls_proc = check_output(["git describe --tags"], shell=True, universal_newlines=True)
		gitVersion = ls_proc
		print('Checking most recent version')
	except Exception as e:
		print('Unable to get git tag and hash')
# if not in git repo
else:
	print('Not in git repository')
	gitVersion = ''

# get current working directory to define git path
gitPath = os.getcwd()

# git untracked file to store version and path
fname = os.path.abspath(os.path.expanduser('./snowav/utils/gitinfo.py'))

with open(fname,'w') as f:
	nchars = len(gitVersion) - 1
	f.write("__gitPath__='{0}'\n".format(gitPath))
	f.write("__gitVersion__='{0}'\n".format(gitVersion[:nchars]))
	f.close()

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

setup_requirements = [
    # TODO(micahsandusky5): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='snowav',
    version='0.5.1',
    description="Snow and Water Model Analysis and Visualization ",
    long_description=readme + '\n\n' + history,
    author="Mark Robertson",
    author_email='mark.robertson@ars.usda.gov',
    url='https://github.com/roberton-mark/SNOWAV',
    packages=['snowav',
			  'scripts',
			  'snowav.framework',
			  'snowav.database',
              'snowav.plotting',
              'snowav.report',
              'snowav.methods',
              'snowav.utils'
			  ],

    include_package_data=True,
    package_data={'snowav':['./config/CoreConfig.ini', './config/recipes.ini']},
    scripts=['./scripts/snow.py'],
    install_requires=requirements,
    license="CC0 1.0",
    zip_safe=False,
    keywords='snowav',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    setup_requires=setup_requirements,

    entry_points={
       'console_scripts': ['snowav = scripts.snow:run',
	   					   'snowav_airflow = scripts.snowav_airflow:run'],
    }

)
