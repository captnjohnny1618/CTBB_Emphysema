import sys
import os

# Necessary for Mac
import matplotlib
matplotlib.use('TkAgg')

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

from texttable import Texttable

__DEBUG__ = False

pd.set_option('expand_frame_rep',False)

# Key identifier variables for CSVs
# id
# dose
# kernel
# slice_thickness
# RA-950
# PERC15
    
# Goal of this script is to produce a table like this, with 95% confidence
# intervals in each box.  We'll "heat map" the values to create a nice visual
#
#################################################################################
#
#     ---------------------------------------------------------------------
#     | Dose  | Slice 0.6           |    Slice 1.0     |    Slice 2.0     |
#     -       -------------------------------------------------------------
#     |       |  k1  |  k2   | k3   | k1  |  k2  | k3  | k1  |  k2  | k3  |
#     ---------------------------------------------------------------------
#     | 100   |      |       |      |     |      |     |     |      |     |
#     ---------------------------------------------------------------------    
#     | 50    |      |       |      |     |      |     |     |      |     |
#     ---------------------------------------------------------------------    
#     | 25    |      |       |      |     |      |     |     |      |     |
#     ---------------------------------------------------------------------    
#     | 10    |      |       |      |     |      |     |     |      |     |
#     ---------------------------------------------------------------------
#
#################################################################################

def usage():
    print("""
          Usage: paired_t_test2.py /path/to/results_file.csv /path/to/reference_file.csv

                 Generates a fixed-width table of 95% confidence intervals and a
                 heat map of "acceptable" configurations.
          
          NOTE: This file is built for the analysis of John's dissertation data
                and should most likely not be used directly, without modification,
                for any other regression analysis.
          
          Copyright (c) John Hoffman 2018
          """)

def main(argc,argv):
    results_csv = sys.argv[1]
    refs_csv    = sys.argv[2]

    if argc==4:
        output_dir = argv[3]
        if os.path.isdir(output_dir):
            save_flag=True
        else:
            print('Cannot find requested output directory.  Exiting.')
            sys.exit(1)

    # Define the reference case
    ref_kernel          = 1.0
    ref_slice_thickness = 1.0
    ref_dose            = 100
    
    # Load the data from the CSV file into pandas dataframes
    # Note that the CSV files have headers, and therefore columns can be
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
    diffs.fillna(value=np.nan,inplace=True)
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
    refs = refs.rename({'RA-910':'RA910','RA-950':'RA950',}, axis='columns')

    # Configure the conditions that we have to test
    doses = [ 100, 50, 25, 10 ]
    kernels = [ 1, 2, 3 ]
    slice_thicknesses = [ 0.6, 1.0, 2.0 ]

    # Configure stuff for our text output
    t=Texttable()
    t.add_row(['','Slice 0.6','','','Slice 1.0','','','Slice 2.0','',''])
    t.add_row(['Dose','k1','k2','k3','k1','k2','k3','k1','k2','k3'])
    t.set_cols_width([7,10,10,10,10,10,10,10,10,10])

    # Configure our dataframe that we'll use to generate our heatmap
    row_annotations=[]
    final_results=pd.DataFrame()

    for i in range(len(doses)):
        row=[str(doses[i])]
        df_row=pd.DataFrame()
        for j in range(len(slice_thicknesses)):
            for k in range(len(kernels)):

                curr_dose            = doses[i]
                curr_slice_thickness = slice_thicknesses[j]
                curr_kernel          = kernels[k]

                if __DEBUG__:
                    print('D: {} K: {} ST: {}'.format(curr_dose,curr_kernel,curr_slice_thickness))

                if curr_dose==ref_dose and curr_slice_thickness==ref_slice_thickness and curr_kernel==ref_kernel and results_csv==refs_csv:
                    row.append('N/A\nN/A ')
                    continue
                
                curr_data=diffs[diffs['dose']==curr_dose]
                curr_data=curr_data[curr_data['kernel']==curr_kernel]
                curr_data=curr_data[curr_data['slice_thickness']==curr_slice_thickness]

                curr_results_org=results_org[results_org['dose']==curr_dose]
                curr_results_org=curr_results_org[curr_results_org['kernel']==curr_kernel]
                curr_results_org=curr_results_org[curr_results_org['slice_thickness']==curr_slice_thickness]

                refs=refs.sort_values('id')
                curr_data=curr_data.sort_values('id')
                curr_results_org=curr_results_org.sort_values('id')

                refs_PERC15=refs['PERC15']
                curr_PERC15=curr_data['PERC15']
                curr_results_org_PERC15=curr_results_org['PERC15']

                ### Test if the difference bewteen mean of reference and
                ### test samples is significant.
                # These two tests should produce the same results
                
                # Calculate 1 sample, using the difference
                # These are not really necessary, however I have included them here
                # to make sure that I understood what was I doing.
                if __DEBUG__:
                    result_1_sample=scipystats.ttest_1samp(curr_PERC15,0)
                    print('1 Sample: {}'.format(result_1_sample))
                    
                    # Calculate 2 sample, using the original data
                    result_2_sample=scipystats.ttest_rel(curr_results_org_PERC15,refs_PERC15)
                    print('Paired: {}'.format(result_2_sample))

                ### Test whether difference is significantly different
                ### than 0.05 (for PERC15). Present 95% confidence interval.
                nan_flag=False
                result_1_sample=scipystats.ttest_1samp(curr_PERC15,0.05)
                if np.isnan(result_1_sample[0]):
                    nan_flag=True
                    result_1_sample=scipystats.ttest_1samp(curr_PERC15,0.05,nan_policy='omit')

                conf=scipystats.t.interval(.95,len(curr_PERC15)-1,loc=curr_PERC15.mean(skipna=True),scale=scipystats.sem(curr_PERC15,nan_policy='omit'))
                if __DEBUG__:
                    print('1 Sample, difference, ==0.05: {}'.format(result_1_sample))
                    print('95% confidence interval:     {}'.format(conf))

                # Update our text table
                if not nan_flag:
                    row.append('{0:.2f}\n{1:.2f}'.format(conf[0],conf[1]))
                else:
                    row.append('{0:.2f}*\n{1:.2f} '.format(conf[0],conf[1]))

                # Update our Pandas dataframe
                # Save current information to our results dataframe row
                # Also determine "unique" indices based on slice thickness and kernel
                # Also determine the color that will be assigned to the box
                res_dict={ 
                    'dose'            : curr_dose,
                    'slice_thickness' : curr_slice_thickness,
                    'kernel'          : curr_kernel,
                    'conf_low'        : conf[0],
                    'conf_high'       : conf[1],
                    'un_idx'          : j*len(kernels)+k
                }

                conf=[math.fabs(conf[0]),math.fabs(conf[1])]
                m=np.mean(conf)

                #res_dict['color']=m

                # Categorical
                if m<=10:
                    res_dict['color']=2 #'g'
                elif m<=12:
                    res_dict['color']=8 #'y'
                elif m<=14:
                    res_dict['color']=10 #'y'
                elif m<=16:
                    res_dict['color']=12 #'y'                                        
                else:
                    res_dict['color']=20 #'r'

                print(curr_dose,curr_slice_thickness,curr_kernel,m,res_dict['color'])

                #if conf[1]<10:
                #    res_dict['color']=3 #'g'
                #elif conf[1]>=10 and conf[0]<=10:
                #    res_dict['color']=2.1 #'y'
                #elif conf[1]>=12 and conf[0]<=12:
                #    res_dict['color']=1.66 #'y'
                #elif conf[1]>=14 and conf[0]<=14:
                #    res_dict['color']=1.33 #'y'                                        
                #else:
                #    res_dict['color']=1 #'r'
                    
                    
                df_row=df_row.append(res_dict,ignore_index=True)

        # Push complete rows into final results tables
        t.add_row(row);
        row_annotations.append(row[1:])
        final_results=final_results.append(df_row,ignore_index=True)

    row_annotations=row_annotations[::-1]
    row_annotations=pd.DataFrame(row_annotations)
    table_plaintext=t.draw()
    print(table_plaintext)

    # Prep heatmap
    from matplotlib.colors import LinearSegmentedColormap
               # green                                       # yellow                # Lighter orange
    #colors=[(239.0/255, 155.0/255, 140.0/255) , (255.0/255, 230.0/255, 73.0/255), (244.0/255, 183.0/255, 41.0/255),(244.0/255, 163.0/255, 41.0/255),(237.0/255, 112.0/255, 35.0/255)]
    #colors=[(1,0,0),(0,1,0),(0,0,1)]

    good       = '#e4ff7a'
    goodmiddle = '#ffe81a'
    middle     = '#ffbd00'
    middlebad  = '#ffa000'
    bad        = '#fc7f00'
    colors=[good,goodmiddle,middle,middlebad,bad]
    colors.reverse()
    cmap_name = 'dissertation'
    cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=5)

    if sys.argv[1].find('safire')==-1:
        tick_labels=['\n\nSmooth','Slice 0.6\n\nMedium','\n\nSharp','\n\nSmooth','Slice 1.0\n\nMedium','\n\nSharp','\n\nSmooth','Slice 2.0\n\nMedium','\n\nSharp']
    else:
        tick_labels=['\n\nI26','Slice 0.6\n\nI44','\n\nI50','\n\nI26','Slice 1.0\n\nI44','\n\nI50','\n\nI26','Slice 2.0\n\nI44','\n\nI50']    

    final_results=final_results.sort_values('dose',ascending=False)
    final_results=final_results.pivot(index='dose',columns='un_idx',values='color')

    # Generate the heatmap
    f = plt.figure(figsize=(12,5))
    cm='GnBu'
    clim=(-1,16)
    ax=sns.heatmap(final_results,cmap=cm,linewidths=0.5,xticklabels=tick_labels,annot=row_annotations,cbar=False,vmin=clim[0],vmax=clim[1])
    cax=ax.get_children()[0]
    cbar = f.colorbar(cax) 
    cbar.ax.invert_yaxis()
    cbar.set_ticks([clim[0],10,clim[1]])
    cbar.ax.set_yticklabels(['Excellent','Acceptable','Bad'])

    ax.set_xticklabels(tick_labels)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    ax.set_xlabel('')

    # Show the heatmap
    if save_flag:
        plt.savefig(os.path.join(output_dir,'heat_map.png'),bbox_inches='tight',dpi=600)

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
    mean = df[var].mean(skipna=True)
    stdev = df[var].std(skipna=True)
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
