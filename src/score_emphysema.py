import sys
import os
import logging

import yaml

path_file='\\\skynet\cvib\PechinTest2\scripts\paths.yml'

def usage():
    print(
        "USAGE:\n"
        "python score_emphysema.py /path/to/hr2file.hr2 /path/to/seg/dir\n"
        "    Paths, ideally, are absolute however they may be relative as well. This could\n"
        "    create challenges if using Condor.\n"
        "    ***Note that seg/dir should NOT end with a slash***"
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

def get_ra(histogram, threshold):
    total = 0
    laa = 0
    for k,v in histogram.items():
        if k<threshold:
            laa += v
        total += v
    return laa/total

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv)<2:
        usage()
        logging.error("Not enough command line arguments")
        sys.exit("Exiting")

    # Set up our paths
    configure_pipeline()
    hr2_filepath       = sys.argv[1]
    seg_dirpath        = sys.argv[2]
    print(hr2_filepath)
    print(seg_dirpath)
    qa_path            = os.path.join(os.path.dirname(seg_dirpath),"qa")
    qi_raw_dirpath     = os.path.join(os.path.dirname(seg_dirpath),"qi_raw")
    histogram_filepath = os.path.join(qi_raw_dirpath,"histogram_lung.yml")    
    output_filepath    = os.path.join(qi_raw_dirpath,"results_emphysema.yml")

    # Load some paths
    path1 = r'\\skynet\cvib\PechinTest2\scripts\ipp33\src'
    sys.path.append(path1) 
    import ipp.img.image as ippimg
    from ipp.img.utils import get_casted_roi
    import ipp.img.overlay as ippovr
    import ipp.img.element as ippelem    

    # Helper function def for generating visualization
    def get_border(mask):
        elem = ippelem.new_connect6_element(skip_origin=False)
        temp = mask.get_binary_dilation(elem)
        temp -= mask>0
        return temp

    # Load the image to get the percentile calculator (computationally inefficient, but better code)
    image = ippimg.read(hr2_filepath)
    image = ippimg.cast(image, copy=True, type=ippimg.Type.short)
    left  = get_casted_roi(os.path.join(seg_dirpath, "left_lung.roi"), template=image)
    right = get_casted_roi(os.path.join(seg_dirpath, "right_lung.roi"), template=image)
    lung  = left + right

    perc = image.get_percentile_calculator(lung)

    # Load the histogram and tally our results
    with open(histogram_filepath,'r') as f:
        histogram=yaml.load(f)

    # Relative area/volume (RA) Scoring
    results={}
    results["RA-856"] = get_ra(histogram,-856)
    results["RA-900"] = get_ra(histogram,-900)
    results["RA-910"] = get_ra(histogram,-910)
    results["RA-920"] = get_ra(histogram,-920)
    results["RA-930"] = get_ra(histogram,-930)
    results["RA-940"] = get_ra(histogram,-940)
    results["RA-950"] = get_ra(histogram,-950)
    results["RA-960"] = get_ra(histogram,-960)
    results["RA-970"] = get_ra(histogram,-970)
    results["RA-980"] = get_ra(histogram,-980)

    # Range calculations (for COPD studies)
    results["Range-950-856"] = get_ra(histogram,-856)-get_ra(histogram,-950)
    
    # Percentile calculations
    results["PERC10"] = perc.percentile(0.10)    
    results["PERC15"] = perc.percentile(0.15)
    results["PERC20"] = perc.percentile(0.20)    
    
    # Other metrics
    spacing=image.get_spacing()
    results["median"] = perc.percentile(0.50)
    results["mean"]   = image.get_statistics_calculator(lung).mean()
    results["volume"] = perc.num()*(spacing[0]*spacing[1]*spacing[2])

    # Kurtosis
    import numpy as np
    names=['voxel_val','count']
    formats=['float64','float64']
    dtype=dict(names=names,formats=formats)
    hist_array=np.array(list(histogram.items()),dtype=dtype)
    counts=np.sum(hist_array['count'])
    raw=np.array([])
    for element in hist_array:
        vals=element[0]*np.ones((int(element[1])),dtype='float64')
        raw=np.concatenate((raw,vals),axis=0)

    from scipy.stats import kurtosis,kurtosistest
    kurt=kurtosis(raw)
    print(kurt,kurtosistest(raw))
    results["kurtosis"] = kurt
                    
    # Save the results to disk
    with open(output_filepath,'w') as f:
        yaml.dump(results,f,default_flow_style=False)
    
    # Generate a visualization for QA purposes
    WINDOW_WIDTH=1600
    WINDOW_LEVEL=-600

    red=(255,0,0)
    green=(0,255,0)

    lung_rgn = lung.find_region(1, None)
    pos = [i+(j-i)/2 for i,j in zip(lung_rgn[0], lung_rgn[1])]
    pos = lung.to_physical_coordinates(pos)
    screen_shot_filename = os.path.join(qa_path,"RA-950")
    gen = ippovr.auto(pos, image=image, crsstype=ippovr.CrossSection.custom, xaxis=(1,0,0), yaxis=(0,0,-1))
    gen.set(image, WINDOW_LEVEL-(WINDOW_WIDTH/2), WINDOW_LEVEL+(WINDOW_WIDTH/2))
    gen.add(get_border(lung), green, 0.7, boundval=0)
    gen.add((image<-950)*lung, red, 0.4, boundval=0)
    gen.write("%s.png" % screen_shot_filename)
