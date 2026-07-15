# -----------------------------------------------------------------------------
# PythonAnywhere WSGI reference.
#
# You do NOT run this file. PythonAnywhere generates its own WSGI file for your
# web app (Web tab -> "WSGI configuration file"). Open that file, DELETE its
# contents, and paste the three lines below — replacing YOURUSERNAME with your
# actual PythonAnywhere username. Then click the green Reload button.
# -----------------------------------------------------------------------------
import sys

project = "/home/YOURUSERNAME/baseball-training-hub"
if project not in sys.path:
    sys.path.insert(0, project)

from app import app as application  # noqa: E402
