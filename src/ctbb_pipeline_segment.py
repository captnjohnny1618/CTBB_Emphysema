import sys
import os
import yaml
from time import strftime
from subprocess import list2cmdline
import numpy as np

import logging

def configure_pipeline_specifics():
    # Add the base pipeline libary directory
    paths=yaml.load(open('paths.yml','r'))
    sys.path.append(paths['pipeline_library'])
    segmentation_script_filepath=paths['segmentation_script']

    # Import library handling and module
    import pypeline as pype
    from ctbb_pipeline_library import ctbb_pipeline_library as ctbb_plib

    global pype
    global ctbb_plib
    global segmentation_script_filepath
    
def create_job_list(recon_list):

    job_list = []

    for l in recon_list:
        series_filepath=l['img_series_filepath']
        series_dirpath=os.path.dirname(l['img_series_filepath'])
        series_output_path=os.path.join(series_dirpath.strip('img'),'seg')
        job_list.append(list2cmdline([segmentation_script_filepath,series_filepath,series_output_path]))
        
    return job_list

def condor_submit():    
    pass

if __name__=="__main__":

    # TMP: Set our logging level to be a little verbose
    logging.basicConfig(level=logging.INFO)

    # Configure necessary paths and modules for integration with exists framework
    configure_pipeline_specifics()

    # Parse command line arguments
    if len(sys.argv)<2:
        print('Must provide a target library path for processing')
    else:
        library=ctbb_plib(sys.argv[1])
    
    if not library.is_valid():
        logging.warning("Library returning invalid status. Analysis may be unsuccessful.")

    # Configure final logging information (writes to file and stdout)
    log_file=os.path.join(library.log_dir,'{}_analysis_segmentation.log'.format(strftime('%y%m%d_%H%M%S')))
    
    log_formatter=logging.Formatter('%(asctime)s %(message)s')
    root_logger=logging.getLogger()
    
    file_handler=logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler=logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Build our job list
    library.refresh_recon_list()
    recon_list=library.get_recon_list()

    print(create_job_list(recon_list))


    logging.info("Program is finishing")
