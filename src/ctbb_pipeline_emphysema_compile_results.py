import sys
import os

import logging
import yaml
from time import strftime

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

    # Detailed logging setup
    # Writes to file in output library's log directory 
    # Also writes log messages to the command line
    log_file=os.path.join(library.log_dir,'{}_analysis_score_emphysema.log'.format(strftime('%y%m%d_%H%M%S')))
    
    log_formatter=logging.Formatter('%(asctime)s %(message)s')
    root_logger=logging.getLogger()
    
    file_handler=logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler=logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Grab the list of all recontstructions that were performed
    logging.info('Target study library: {}'.format(library.path))
    library.refresh_recon_list()
    logging.info("Loading reconstruction list from target library...")
    recon_list=library.get_recon_list()

    # Results are in a dictionary.  This list specifies all of the keys to the results.
    keys=["RA-900",
          "RA-910",
          "RA-920",
          "RA-930",
          "RA-940",
          "RA-950",
          "RA-960",
          "RA-970",
          "RA-980",
          "PERC10",
          "PERC15",
          "PERC20",
          "median",
          "mean",
          "volume"]

    # Open the final output file
    output_file=os.path.join(library.path,"eval","results_emphysema.csv")
    logging.info("Opening the final results file {}".format(output_file))
    with open(output_file,'w') as out_fid:
        # Write the header string
        header_string="{},{},{},{},{},{}".format('pipeline_id',
                                        'dose',
                                        'kernel',
                                        'slice_thickness',
                                        ",".join([str(k) for k in keys]),
                                        'org_raw_filepath')
        out_fid.write(header_string+"\n")
        
        # Iterate through each reconstruction. Send the emphysema results to final output file.
        logging.info("Processing results files into CSV format")
        for recon in recon_list:
            img_filepath=recon['img_series_filepath']
            img_dirpath=os.path.dirname(img_filepath) #/path/to/study/img/
            qi_raw_dirpath=os.path.join(os.path.dirname(img_dirpath),"qi_raw")
            emphysema_result_filepath=os.path.join(qi_raw_dirpath,"results_emphysema.yml")

            # Open the results file for the particular parameter configuration
            print(emphysema_result_filepath)
            if os.path.exists(emphysema_result_filepath):
                with open(emphysema_result_filepath,'r') as fid:
                    # Generate the results string for the parameter configuration
                    # (i.e. dict -> csv format) and write to disk
                
                    results_dict=yaml.load(fid)                
            else:
                results_dict=dict.fromkeys(keys)

            #print(results_dict)
                
            results_string="{},{},{},{},{},{}".format(recon['pipeline_id'],
                                    recon['dose'],
                                    recon['kernel'],
                                    recon['slice_thickness'],
                                    ",".join([str(results_dict[k]) for k in keys]),
                                    recon['org_raw_filepath'])
            out_fid.write(results_string+"\n")

    logging.info("Results compilation complete.")
