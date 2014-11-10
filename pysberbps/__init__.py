import sys
if sys.version.startswith('2'):
    from pysberbps import *
else:
    from .pysberbps import *