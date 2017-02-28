import sys
import os
import logging

import yaml

path_file='\\\skynet\cvib\PechinTest2\scripts\paths.yml'

def usage():
    print(
        "USAGE:\n"
        "python calculate_histogram.py /path/to/image_file.hr2 /path/to/segmentation/directory/\n"
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

def except_critical():
    sys.exit("Critical fail. Exiting.")

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
    qa_path=os.path.join(os.path.dirname(seg_dirpath),"qa")
    output_filepath=os.path.join(os.path.dirname(seg_dirpath),"qi_raw","histogram_lung.yml")

    # Load some paths
    path1 = r'\\skynet\cvib\PechinTest2\scripts\ipp33\src'
    sys.path.append(path1) 
    import ipp.img.image as ippimg
    from ipp.img.utils import get_casted_roi
    import ipp.img.overlay as ippovr

    # Load the image from disk
    logging.info("Loading image file: {}".format(hr2_filepath))
    try:
        image = ippimg.read(hr2_filepath)
        image = ippimg.cast(image, copy=True, type=ippimg.Type.short)
    except Exception as e:
        logging.error("Unable to load image file.")
        except_critical()

    # Load the segmentations
    logging.info("Loading segmentation files from '{}'".format(seg_dirpath))
    try:
        left  = get_casted_roi(os.path.join(seg_dirpath, "left_lung.roi"), template=image)
        right = get_casted_roi(os.path.join(seg_dirpath, "right_lung.roi"), template=image)
        lung  = left+right
    except Exception as e:
        logging.error("Unable to load segmentation(s) from '{}'".format(seg_dirpath))
        except_critical()

    # Calculate the histogram
    logging.info("Calculating histogram from image and segmentation")
    try:
        perc  = image.get_percentile_calculator(lung)
        hist  = perc.histogram()
    except:
        logging.error("Error while processing histogram")
        except_critical()        

    # Save histogram to disk
    logging.info("Writing histogram to disk: {}".format(output_filepath))
    try:
        with open(output_filepath, 'w') as f:
            yaml.dump(hist, f, default_flow_style=False)
    except:
        logging.error("Unable to save histogram to disk")
        except_critical()

    logging.info("Histogram generation complete.")

