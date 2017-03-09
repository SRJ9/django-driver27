import os
import sys


def import_driver27():
    try:
        import driver27
    except ImportError:
        sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), '../../')))
        import driver27