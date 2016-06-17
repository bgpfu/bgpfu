import os

here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, '../facsimile/VERSION'))
__version__ = f.read().strip()
f.close()
