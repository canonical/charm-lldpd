import os
import pathlib
import sys


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)


built_charm = "lldpd"
