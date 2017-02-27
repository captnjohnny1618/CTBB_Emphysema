import sys
import os
import logging

import yaml

path_file='\\\skynet\cvib\PechinTest2\scripts\paths.yml'

MODEL_OLD_FILEPATH = r"M:\DEVELOPMENT\LUNG_SEGMENTATION\dev\config\lung_model.10\lung_model"
MODEL_NEW_FILEPATH = r"M:\DEVELOPMENT\MIU\dev\config\org\lung_nod_model\lung_nod_model.23\lung_nod_model"
MODEL_FILEPATH=MODEL_OLD_FILEPATH

OLD_CAD_EXEPATH = r"M:\apps\personal\pechin\miu-framework\bin\commons\miu_nod.exe"
SCRIPTS_CAD_EXEPATH = r"\\skynet\cvib\PechinTest2\scripts\miu-framework\bin\commons\miu_nod.exe"
CAD_EXEPATH = SCRIPTS_CAD_EXEPATH

__BLOCKING__=True

def usage():
    print(
        "USAGE:\n"
        "python segment_hr2_file.py /path/to/image_file.hr2 /path/to/segmentation/directory/\n"
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

def run_segmentation(hr2_filepath,model_filepath,seg_dirpath):

    # Run the segmentation
    basic_command = [CAD_EXEPATH, hr2_filepath, model_filepath, seg_dirpath]
    import subprocess

    if __BLOCKING__:
        subprocess.call(basic_command,stdout=sys.stdout,stderr=sys.stderr)
    else:
        subprocess.Popen(basic_command,stdout=sys.stdout,stderr=sys.stderr)

def fetch_parent_segmentation(hr2_filepath,seg_dirpath,patient_id,parent_dose,parent_kernel,parent_st):
    logging.info("Fetching parent segmentation...")
    from shutil import copy

    # Build our path to our parent segmentation
    # Get the full path to our "recon" directory inside of our library
    path_delimiter=os.path.join("library","recon")
    recon_dirpath=os.path.join(hr2_filepath.split(path_delimiter)[0],path_delimiter)
    # Assemble the stripped path with our parent information to create path to parent hr2
    recon_dir_id='{}_k{}_st{}'.format(patient_id,parent_kernel,parent_st)
    recon_file_id='{}_d{}_k{}_st{}.hr2'.format(patient_id,parent_dose,parent_kernel,parent_st)
    parent_hr2_filepath=os.path.join(recon_dirpath,str(parent_dose),recon_dir_id,'img',recon_file_id)
    parent_seg_dirpath= os.path.join(recon_dirpath,str(parent_dose),recon_dir_id,'seg')

    logging.info("Parent hr2 file: {}".format(parent_hr2_filepath))
    logging.info("Does it exist?: {}".format(os.path.exists(parent_hr2_filepath)))
    logging.info("Parent segmentation directory: {}".format(parent_seg_dirpath))
    logging.info("Is a real directory?: {}".format(os.path.isdir(parent_seg_dirpath)))

    # Check for right and left lung segmentations
    right_lung_filepath=os.path.join(parent_seg_dirpath,"right_lung.roi")
    left_lung_filepath=os.path.join(parent_seg_dirpath,"left_lung.roi")

    # Check if files exist, copy if found
    # Make 6 attempts, separated by 30 seconds (i.e. wait a total of 3 minutes)
    # This buys us time while another node may be segmenting.
    import time
    successful_copy=False
#    for i in range(6):
    for i in range(1):
        logging.info("Attempt ({}) to copy parent segmentations".format(i))
        if (os.path.exists(right_lung_filepath) and os.path.exists(left_lung_filepath)):
            copy(right_lung_filepath,seg_dirpath)
            copy(left_lung_filepath,seg_dirpath)
            if (os.path.exists(os.path.join(seg_dirpath,'right_lung.roi')) and os.path.exists(os.path.join(seg_dirpath,'left_lung.roi'))):
                logging.info('Parent segmentations successfully retrieved')
                successful_copy=True
                break
            else:
                logging.error('DETECTED PARENT SEGMENTATIONS BUT FAILED TO SUCCESSFULLY COPY THEM')

        time.sleep(30)

    # If segmentations never appears, generate the parent segmenations targeting the PARENT directory.
    # After segmentations are generated, copy them to the current study.
    if not successful_copy:
        logging.info('Timed out waiting for parent segmentations to generate. Running from current job.')
        run_segmentation(parent_hr2_filepath,MODEL_FILEPATH,parent_seg_dirpath)
        copy(right_lung_filepath,seg_dirpath)
        copy(left_lung_filepath,seg_dirpath)
        if (os.path.exists(os.path.join(seg_dirpath,'right_lung.roi')) and os.path.exists(os.path.join(seg_dirpath,'left_lung.roi'))):
            logging.info('Parent segmentations successfully retrieved')
            successful_copy=True
        else:
            logging.error('DETECTED PARENT SEGMENTATIONS BUT FAILED TO SUCCESSFULLY COPY THEM')

    return successful_copy

if __name__=="__main__":

    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv)<2:
        usage()
        logging.error("Not enough command line arguments")
        sys.exit("Exiting")

    # Set up our paths
    configure_pipeline()
    hr2_filepath=sys.argv[1]
    seg_dirpath=sys.argv[2]
    parent_seg=sys.argv[3]
    qa_path=os.path.join(os.path.dirname(seg_dirpath),"qa")
    model_filepath=MODEL_FILEPATH

    # Three cases to handle:
    # (1) Parent config unspecified:
    #     ---> run the segmentation
    # (2) Parent config specified, current case is parent config
    #     ---> run the segmentation
    # (3) Parent config specified, current case is NOT the parent config
    #     ---> Copy the segmentation from the parent

    # Configure the variables we'll need to test
    exec('(parent_dose,parent_kernel,parent_st)={}'.format(parent_seg)) # Convert our parent_seg string to a list
    (patient_id,dose,kernel,st)=os.path.splitext(os.path.basename(hr2_filepath))[0].split('_') # Extract case info from filename
    (curr_case_dose,curr_case_kernel,curr_case_st)=[int(dose.strip('d')),int(kernel.strip('k')),float(st.strip('st'))]

    # Determine if current case is a parent case
    curr_case_is_parent=True

    if parent_dose:
        curr_case_is_parent=((parent_dose==curr_case_dose) and curr_case_is_parent)
    else:
        parent_dose=curr_case_dose
        
    if parent_kernel:
        curr_case_is_parent=((parent_kernel==curr_case_kernel) and curr_case_is_parent)
    else:
        parent_kernel=curr_case_kernel
        
    if parent_st:
        curr_case_is_parent=((parent_st==curr_case_st) and curr_case_is_parent)
    else:
        parent_st=curr_case_st

    # Case (1) (no parent specified) and Case (2) (parent specified and current case IS parent)
    # If true, run segmentation on the current case
    if parent_seg=='[[],[],[]]' or curr_case_is_parent:
        logging.info('PARENT NOT SPECIFIED OR CURRENT CASE IS PARENT ({})'.format(curr_case_is_parent))
        run_segmentation(hr2_filepath,model_filepath,seg_dirpath)
        
    # Case (3) (parent specified, current case is NOT parent config)
    # If true, fetch the segmentation from the parent
    else:
        logging.info('PARENT SPECIFIED, CURRENT CASE IS NOT PARENT ({})'.format(curr_case_is_parent))
        success=fetch_parent_segmentation(hr2_filepath,seg_dirpath,patient_id,parent_dose,parent_kernel,parent_st)
        if not success:
            logging.info("Timed out waiting for segmentations to generate. Running manually.")

    # Generate a visualization (for sanity checking)
    path1 = r'\\skynet\cvib\PechinTest2\scripts\ipp33\src'
    sys.path.append(path1) 
    import ipp.img.image as ippimg
    from ipp.img.utils import get_casted_roi
    import ipp.img.overlay as ippovr
   
    image = ippimg.read(hr2_filepath)
    image = ippimg.cast(image, copy=True, type=ippimg.Type.short)
    left = get_casted_roi(os.path.join(seg_dirpath, "left_lung.roi"), template=image)
    right = get_casted_roi(os.path.join(seg_dirpath, "right_lung.roi"), template=image)

    WINDOW_WIDTH=1600
    WINDOW_LEVEL=-600
    
    pos = [minp + (maxp-minp)/2 for minp, maxp in zip(*image.get_region())]
    pos = image.to_physical_coordinates(pos)
    gen = ippovr.auto(pos, image=image, crsstype=ippovr.CrossSection.custom, xaxis=(1,0,0), yaxis=(0,0,-1))
    gen.set(image, WINDOW_LEVEL-(WINDOW_WIDTH/2), WINDOW_LEVEL+(WINDOW_WIDTH/2))
 
    gen.write(os.path.join(qa_path, "image.png"))
    red=(255,0,0)
    green=(0,255,0)
    gen.add(left, green, 0.5, boundval=0)
    gen.add(right, red, 0.5, boundval=0)
    gen.write(os.path.join(qa_path, "overlay.png"))
