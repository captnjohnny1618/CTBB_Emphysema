import sys
import os
import numpy as np
import pandas as pd
from texttable import Texttable

import matplotlib.pyplot as plt

pd.set_option('expand_frame_rep',False)

def usage():
    print("""
          Usage: summary_statistics.py /path/to/results_file_1.csv [/path/to/results_file_2.csv] (/path/to/output_file.csv)

                 Generates a command line table or output CSV file of descriptive data
          
          NOTE: This file is built for the analysis of John's dissertation data
                and should most likely not be used directly, without modification,
                for any other regression analysis.
          
          Copyright (c) John Hoffman 2018
          """)

def main(argc,argv):

    # Declarations
    save_flag=False
    results_filepath=[]
    for i in range(1,argc):
        results_filepath.append(argv[i])
    output_filepath = []
    col_widths=[7,7,7]
    t=Texttable()
    csv_strings=[]

    test_metric='RA-950'
    test_metric='PERC15'
    
    # Define the reference case
    ref_kernel          = 1.0
    ref_slice_thickness = 1.0
    ref_dose            = 100

    # Configure the conditions that we have
    doses = [ 100, 50, 25, 10 ]
    kernels = [ 1, 2, 3 ]
    slice_thicknesses = [ 0.6, 1.0, 2.0 ]

    kernel_dict={1:'Smooth',2:'Medium',3:'Sharp'}

    # Load the data from the CSV file into pandas dataframes
    # Note that the CSV files have headers, and therefore columns can be
    # addressed using commands like results['RA-950'] or results['id']
    printf('Loading data... ')
    results_org=[]
    for i in range(len(results_filepath)):
        results_org.append(pd.read_csv(results_filepath[i],na_values='None'))
        col_widths.append(21)
    print('DONE')

    # TABLE 1: Summarize the mean values and min/max data for loaded CSVs
    print('')
    print('TABLE 1: Summary data for:')
    [printf(i+'\n') for i in results_filepath]
    print('')
    
    t.set_cols_width(col_widths)
    
    for i in range(len(doses)):
        for j in range(len(slice_thicknesses)):
            for k in range(len(kernels)):
                
                curr_dose            = doses[i]
                curr_slice_thickness = slice_thicknesses[j]
                curr_kernel          = kernels[k]

                row=[str(curr_dose),'{0:.1f}'.format(curr_slice_thickness),kernel_dict[curr_kernel]]
                
                for ii in range(len(results_filepath)):

                    curr_results_file=results_org[ii]

                    curr_data=curr_results_file[(curr_results_file['dose']==curr_dose) &
                                          (curr_results_file['slice_thickness']==curr_slice_thickness) &
                                          (curr_results_file['kernel']==curr_kernel)]
    
                    m,sd,min_v,max_v=summary(curr_data,test_metric)
                    data_string=u'"{0:.3f} \u00B1 {1:.3f}\n[{2:.3f},{3:.3f}]"'.format(m,sd,min_v,max_v)
                    row.append(data_string)
    
                t.add_row(row)
                csv_strings.append(','.join(elem.encode('utf-8') for elem in row))

    print(t.draw())

    # See if user wants to save to file, handle request
    if True:
        while True:        
            ans=raw_input('Save to file? [y/N] ')
            if not ans:
                ans='n'
                
            if ans.lower()[0]=='y':
                output_filepath=raw_input('Save as (full file path): ')
                with open(output_filepath,'w') as f:
                    for row in csv_strings:
                        f.write(row+'\n')            
                break;
            elif ans.lower()[0]=='n':
                break;
            else:
                continue


    # TABLE 2: Summarize the number of patients with different levels of emphysema
    # Assumes the first set of results is the reference reconstruction dataset (i.e. WFBP)
    print('')
    print('TABLE 2: Number of patients with different levels of emphysema at reference')
    print('')    
    t=Texttable()

    ref_results=results_org[0]

    refs=ref_results[(ref_results['dose']==ref_dose) &
                     (ref_results['kernel']==ref_kernel) &
                     (ref_results['slice_thickness']==ref_slice_thickness)]

    refs_lt_5 = refs[refs[test_metric]<.05]
    refs_5_10 = refs[(refs[test_metric]>=.05) & (refs['RA-950']<.1)]    
    refs_gt_10 = refs[refs[test_metric]>=.1]
    
    header=[u'RA950 < 0.05',u'0.05 \u2264 RA950 < 0.10',u'RA950 \u2265 0.10','Total']
    row   =[refs_lt_5.shape[0],refs_5_10.shape[0],refs_gt_10.shape[0],refs.shape[0]]
    
    t.add_row(header)
    t.add_row(row)
    t.set_cols_align(['c','c','c','c'])

    print(t.draw())

    # Generate a histogram of the Emphysema scores at reference
    from numpy import linspace
    plt.figure(figsize=(5,5))
    if test_metric=='RA-950':
        ax=refs[test_metric].plot.hist(bins=linspace(0,0.45,10),color='r')
    elif test_metric=='PERC15':
        ax=refs[test_metric].plot.hist(color='r')        
    ax.set_xlabel('{}'.format(test_metric))
    plt.savefig(os.path.join('/Users/johnhoffman/Study_Data/dissertation/summary_hist.png'),dpi=600,bbox_inches='tight')
    plt.show()

def summary(df,var):

    max_v = df[var].max()
    min_v = df[var].min()
    mean = df[var].mean(skipna=True)
    stdev = df[var].std(skipna=True)

    return (mean,stdev,min_v,max_v)

def printf(s):
    # Helper function.  Prints to STDOUT without necessarily including
    # the newline (unless user specifies it).
    sys.stdout.write(s)
    sys.stdout.flush()
        
        
if __name__=='__main__':

    argc=len(sys.argv)
    argv=sys.argv

    if argc<2:
        usage()
        sys.exit()

    main(argc,argv)
