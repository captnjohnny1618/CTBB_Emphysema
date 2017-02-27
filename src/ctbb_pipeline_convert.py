# import everything that you need
import sys
import os
import yaml
import logging
from time import strftime

from subprocess import list2cmdline
from subprocess import call

paths={}

def parse_config(config_filepath):
    ### Function to parse the config file passed at the command line
    ### config_filepath is the path to the configuration file passed at the command line
    
    # Load the config file into a dictionary
    with open(config_filepath,'r') as f:
        config_dict=yaml.load(f)
    
    # Validate that we have any required configuration parameters
    if ('library' not in config_dict.keys()):
        logging.error('"library" is a required configuration parameter and was not found. Exiting.')
        config_dict={}
    # Check for optional fields and set defaults if needed
    else:
        pass

    return config_dict

def configure_pipeline():
    ### Function that loads any hard-coded paths for the library and/or job scripts

    logging.info('Configuring pipeline paths from paths.yml')
    
    # Make sure we modify the global var
    global paths
    
    # Load the paths.yml file
    with open('paths.yml','r') as f:
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
    
def create_job_list(recon_list):
    ### Function creates list of system calls (i.e. command line program calls)
    ### Each list item forms a separate job that will be sent to condor
    ### recon_list is loaded from the 'recons.csv' file contained in the library

    logging.info('Building job list')
    
    job_list=[]

    for l in recon_list:
        conversion_script_filepath=paths['conversion_script']
        series_filepath=l['img_series_filepath']
        series_prm_filepath=series_filepath.strip(".img")+".prm"
        
        job_list.append(list2cmdline([conversion_script_filepath,series_filepath,series_prm_filepath]))

    logging.info('Found {} reconstructions. Created {} jobs to be executed on Condor'.format(len(recon_list),len(job_list)))
    
    return job_list

def condor_submit(job_list,library):
    ### Function to take the job list and send to a condor cluster for individual execution
    ### The library object is needed to target condor logging info to the correct directory

    logging.info("Submitting job to condor")
    
    # Flush job list to a temporary file    
    tmp_fid=open('tmp_garbage.txt','a+')
    for job in job_list:
        tmp_fid.write(job+'\n')
    tmp_fid.seek(0)
    job_list_filepath=tmp_fid.name
    tmp_fid.close()

    # Call the Condor submit script (authored by pechin and configured for MedQIA/CVIB specific stuff)
    command='python {} {} -w {} -r CVIB==TRUE --limit25 --automountconf {}'.format(paths['submit_script'],job_list_filepath,library.log_dir,paths['automount_script'])
    logging.info(command)
    command=command.split(' ')
    exit_code=call(command,shell=False)
    #os.system('python {} {} -w {} -r CVIB==TRUE --limit25 --automountconf {}'.format(submit_script_filepath,job_list_filepath,library.log_dir,automount_script_filepath))

    if exit_code:
        logging.warning('Condor submit script returned non-zero exit code: {}'.format(exit_code))
        logging.warning('Jobs likely were not submitted to Condor')
    else:
        logging.info('Job list submitted to condor successfully')
        
    # Clean up the job list temporary file
    os.remove(tmp_fid.name)

def var_test():
    pass

if __name__=="__main__":
    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Set up paths to pipeline scripts
    configure_pipeline()
    
    # Read the configuration file passed at the command line
    if len(sys.argv)<2:
        print("No configuration file provided.") # note: cannot use logging yet since not configured
        sys.exit("Exiting.")
    else:            
        config_dict=parse_config(sys.argv[1])
        library=ctbb_plib(config_dict['library'])
        print(library.path)

    # Detailed logging setup
    # Writes to file in output library's log directory 
    # Also writes log messages to the command line
    log_file=os.path.join(library.log_dir,'{}_analysis_segmentation.log'.format(strftime('%y%m%d_%H%M%S')))
    
    log_formatter=logging.Formatter('%(asctime)s %(message)s')
    root_logger=logging.getLogger()
    
    file_handler=logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler=logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Build our job list using library's "recons.csv" file
    logging.info('Target study library: {}'.format(library.path))
    library.refresh_recon_list()
    recon_list=library.get_recon_list()
    print(recon_list)
    job_list=create_job_list(recon_list)

    print(job_list)

    # Submit the job list to condor
    condor_submit(job_list,library)
