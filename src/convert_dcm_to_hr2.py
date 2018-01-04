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
from qia.common.img import image as qimage

def main(argc,argv):
    
    input_dirpath=argv[1]
    output_filepath=argv[2]
    
    print('Loading DICOM stack...')
    dcm_stack=qimage.read(input_dirpath)

    print('Saving DICOM stack as HR2...')
    dcm_stack.write(output_filepath)

    print('DONE')

if __name__=="__main__":
    main(len(sys.argv),sys.argv)






