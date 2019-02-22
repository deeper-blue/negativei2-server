import sys, os
pwd_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pwd_path)

from .server import app
