import sys
from distutils.core import setup
import py2exe
sys.path.append('C:\\WINDOWS\\WinSxS\\x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.4148_none_5090ab56bcba71c2')
setup(windows=[{"script":"gui.py"}], options={"py2exe":{"includes":["sip"]}})
