import sys
import os
import platform

# Configure QIA paths
p=platform.system().lower()

if p == "linux":
    qia_path="/PechinTest2/scripts/qia_pipeline/src"
elif p == "windows":
    qia_path=r"\\skynet\PechinTest2\scripts\qia_pipeline\src"

sys.path.append(qia_path)
print("Added {} QIA path: {}".format(p,qia_path));

# QIA imports
#from qia.common.img import file as qfile
from qia.common.img import image as qimage





