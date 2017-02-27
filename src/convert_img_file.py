import sys
import os
import logging

import yaml

path_file='\\\skynet\cvib\PechinTest2\scripts\paths.yml'

def usage():
    print(
        "USAGE:\n"
        "python convert_img_file.py /path/to/image_file.img /path/to/parameter_file.prm\n"
        "    Paths, ideally, are absolute however they may be relative as well. This could\n"
        "    create challenges if using Condor.\n"
        )

def configure_pipeline():
    ### Function that loads any hard-coded paths for the library and/or job scripts

    logging.info('Configuring pipeline paths from paths.yml')
    
    # Make sure we modify the global var
    global paths

    print(os.getcwd())
    
    # Load the paths.yml file
    with open(path_file,'r') as f:
        logging.info('Using paths.yml from: '.format(f.name))
        paths=yaml.load(f)

    logging.info('Adding {} to python path'.format(paths['pipeline_library']))
    sys.path.append(paths['pipeline_library'])

    # Import library handling and module
    import pypeline as pype
    from ctbb_pipeline_library import ctbb_pipeline_library as ctbb_plib

    # Make stuff imported libraries global
    global pype
    global ctbb_plib

if __name__=="__main__":

    if len(sys.argv)<2:
        usage()
        logging.error("Not enough command line arguments")
        sys.exit("Exiting")

    # Set up our paths
    configure_pipeline()
        
    # Initialize our image stack (note, this does NOT load images into memory)
    print(sys.argv)
    logging.error(str(sys.argv))
    img_stack=pype.pipeline_img_series(sys.argv[1],sys.argv[2])

    output_filepath=img_stack.img_filepath.strip(".img")+".hr2"

    img_stack.to_hr2(output_filepath)
