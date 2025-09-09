import sys
import os

INTERP = os.path.expanduser("/usr/local/bin/python3.9")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from requestHandler import app as application

# Configure for production
application.config['PROPAGATE_EXCEPTIONS'] = True
