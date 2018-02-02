import sys
import os

import numpy as np
import pandas as pd
import scipy.stats as scipystats
from matplotlib import pyplot as plt

import itertools
from itertools import chain, combinations

import statsmodels.api as sm
import statsmodels.stats as stats
import statsmodels.formula.api as smf
from   statsmodels.graphics.regressionplots import *

import seaborn as sns
import copy
import math
import time

__DEBUG__ = True

pd.set_option('expand_frame_rep',False)

# Key identifier variables for CSVs
# id
# dose
# kernel
# slice_thickness
# RA-950
# PERC15

def usage():
    print("""
          Usage: multiple_regression.py /path/to/results_file.csv /path/to/reference_file.csv
          
          NOTE: This file is built for the analysis of John's dissertation data
                and should most likely not be used directly, without modification,
                for any other regression analysis.
          
          Copyright (c) John Hoffman 2018
          """)

def main(argc,argv):
    results_csv = sys.argv[1]
    refs_csv    = sys.argv[2]

    save_flag=False
    if argc==4:
        output_dir = argv[3]
        if os.path.isdir(output_dir):
            save_flag=True
            stdout=sys.stdout
            sys.stdout=open(os.path.join(output_dir,'regression_results.txt'),'w')
        else:
            print('Cannot find requested output directory.  Exiting.')
            sys.exit(1)

    # Define the reference case
    ref_kernel          = 1.0
    ref_slice_thickness = 1.0
    ref_dose            = 100
    
    # Load the data from the CSV file into pandas dataframes
    # Note that the CSV files have headers, and therefor columns can be
    # addressed using commands like results['RA-950'] or results['id']
    printf('Loading data... ')
    results_org = pd.read_csv(results_csv,na_values='None')
    refs_org    = pd.read_csv(refs_csv,na_values='None')
    print('DONE')
    
    # Generate the reference array
    printf('Generating the reference array... ')
    refs = refs_org[refs_org['kernel']==ref_kernel]
    refs = refs[refs['slice_thickness']==ref_slice_thickness]    
    refs = refs[refs['dose']==ref_dose]
    print('DONE')

    print('================================================================================')
    print('Summary data for REFERENCE dataset')
    print('================================================================================')
    print('N: {}'.format(refs.shape))
    codebook(refs,'dose')
    codebook(refs,'kernel')
    codebook(refs,'slice_thickness')    
    codebook(refs,'RA-950')    
    codebook(refs,'PERC15')
    print('================================================================================')
    
    # Generate the difference array
    printf('Generating difference data... ')
    diffs=results_org.copy()
    for idx,l in diffs.iterrows():

        # Find the reference for the current row
        curr_patient=l['id']
        curr_ref=refs[refs['id']==curr_patient]

        diffs.at[idx,'mean'  ] = l['mean']  -curr_ref['mean'  ]
        diffs.at[idx,'median'] = l['median']-curr_ref['median']
        diffs.at[idx,'RA-950'] = l['RA-950']-curr_ref['RA-950']
        diffs.at[idx,'RA-920'] = l['RA-920']-curr_ref['RA-920']
        diffs.at[idx,'RA-910'] = l['RA-910']-curr_ref['RA-910']
        diffs.at[idx,'PERC10'] = l['PERC10']-curr_ref['PERC10']
        diffs.at[idx,'PERC15'] = l['PERC15']-curr_ref['PERC15']
        diffs.at[idx,'PERC20'] = l['PERC20']-curr_ref['PERC20']
        diffs.at[idx,'volume'] = l['volume']-curr_ref['volume']

    print('DONE')

    print('================================================================================')
    print('Summary data for RESULTS (difference) dataset')
    print('================================================================================')
    print('N: {}'.format(diffs.shape))
    codebook(diffs,'dose')
    codebook(diffs,'kernel')
    codebook(diffs,'slice_thickness')    
    codebook(diffs,'RA-950')    
    codebook(diffs,'PERC15')    
    print('================================================================================')

    # Rename some problematic columns (Pandas tolerates the "-" but statsmodels does not)
    diffs=diffs.rename({'RA-910':'RA910','RA-950':'RA950',}, axis='columns')

    ### NO INTERACTION TERMS ========================================
    # Simple, direct use of categorical variables (offers very little control)
    #lm = smf.ols('RA950 ~ C(kernel) + dose + slice_thickness', data = diffs).fit()
    #print(lm.summary())

    # Set up dummy variables for kernel. This approach allows us to
    # make more careful comparison, maybe? Results seem to be the
    # same, however at the very least, the naming scheme makes the
    # coefficient reporting easier to interpret.
    diffs['kernel_smooth'] = np.where(diffs.kernel == 1, 2.0 / 3, -1.0 / 3)
    diffs['kernel_medium'] = np.where(diffs.kernel == 2, 2.0 / 3, -1.0 / 3)
    diffs['kernel_sharp']  = np.where(diffs.kernel == 3, 2.0 / 3, -1.0 / 3)
    #diffs['kernel_smooth'] = np.where(diffs.kernel == 1, 1, 0)
    #diffs['kernel_medium'] = np.where(diffs.kernel == 2, 1, 0)
    #diffs['kernel_sharp']  = np.where(diffs.kernel == 3, 1, 0)
    #print(diffs.groupby(["kernel","kernel_smooth","kernel_medium","kernel_sharp"]).size())    
    
    lm = smf.ols('RA950 ~ kernel_medium + kernel_sharp + dose + slice_thickness', data = diffs).fit()
    print(lm.summary())

    ### Models with interaction terms ========================================
    diffs["dosexslice_thickness"] = diffs.dose * diffs.slice_thickness
    diffs["dosexkernel_medium"]   = diffs.dose * diffs.kernel_medium
    diffs["dosexkernel_sharp"]    = diffs.dose * diffs.kernel_sharp

    diffs["slice_thicknessxkernel_medium"]      = diffs.slice_thickness * diffs.kernel_medium
    diffs["slice_thicknessxkernel_sharp"]       = diffs.slice_thickness * diffs.kernel_sharp

    diffs["slice_thicknessxkernel_mediumxdose"] = diffs.slice_thickness * diffs.kernel_medium * diffs.dose
    diffs["slice_thicknessxkernel_sharpxdose"]  = diffs.slice_thickness * diffs.kernel_sharp  * diffs.dose    

    # This model includes all interaction terms and has collinearity problems
    lm = smf.ols('RA950 ~ kernel_medium + kernel_sharp + dose + slice_thickness + dosexslice_thickness + dosexkernel_medium + dosexkernel_sharp + slice_thicknessxkernel_medium + slice_thicknessxkernel_sharp + slice_thicknessxkernel_mediumxdose + slice_thicknessxkernel_sharpxdose', data = diffs).fit()
    print(lm.summary())
    
    # This model includes all two-variable interaction terms however
    # omits the higher-order terms.  This does not throw collinearity
    # warnings.
    lm = smf.ols('RA950 ~ kernel_medium + kernel_sharp + dose + slice_thickness + dosexslice_thickness + dosexkernel_medium + dosexkernel_sharp + slice_thicknessxkernel_medium + slice_thicknessxkernel_sharp', data = diffs).fit()    
    print(lm.summary())

    if save_flag:
        sys.stdout=stdout
    
    pass

def codebook(df, var):
    # Helper function. Gives quick summary of a column in a pandas datafram
    #     df is the data frame
    #     var is the name of the column you want to analyze
    
    print('CODEBOOK for {}'.format(str(var)))    
    unique_values = len(df[var].unique())
    max_v = df[var].max()
    min_v = df[var].min()
    n_miss = sum(pd.isnull(df[var]))
    mean = df[var].mean()
    stdev = df[var].std()
    print('{}'.format(pd.DataFrame({'unique values': unique_values, 'max value' : max_v, 'min value': min_v, 'num of missing' : n_miss, 'mean' : mean, 'stdev' : stdev}, index = [0])))
    print('********************************************************************************')
    return

def printf(s):
    # Helper function.  Prints to STDOUT without necessarily including
    # the newline (unless user specifies it).
    sys.stdout.write(s)
    sys.stdout.flush()

if __name__=="__main__":

    argc=len(sys.argv)
    argv=sys.argv
    
    if argc<3:
        usage()
        sys.exit()

    main(len(sys.argv),sys.argv)
