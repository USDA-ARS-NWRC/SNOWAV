import os
__version__ = '0.8.4'
__core_config__ = os.path.abspath(os.path.dirname(__file__) + '/config/CoreConfig.ini')
__recipes__ = os.path.abspath(os.path.dirname(__file__) + '/config/recipes.ini')
__config_titles__ = {'snowav':'Overview',
                     'database':'Database connection',
                     'run':'Process directory and report period',
                     'validate':'Snow pillow validation figure',
                     'plots':'Figures',
                     'report':'Report',
                     'forecast':'WRF forecast',
                     'query':'Query existing database records'}

from . import framework
from . import database
from . import plotting
from . import report
from . import utils

__config_header__ = utils.utilities.get_config_header()
