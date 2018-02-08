import sys
import os

import csv

import numpy as np
import pandas as pd
import matplotlib as mp
import matplotlib.pyplot as plt

import matplotlib.lines as mlines

import itertools

# Global defines:
ref_kernel          = 1.0
ref_slice_thickness = 1.0
ref_dose            = 100

doses             = [100,50,25,10]
kernels           = [1,2,3]
slice_thicknesses = [0.6,1.0,2.0]

markers=itertools.cycle(('o','^','s'))
colors=itertools.cycle(('b','g','r'))

kernel_label_dict={
    1.0:"Smooth",
    2.0:"Medium",
    3.0:"Sharp"}

label_dict={
    'dose':'% Clinical CTDIvol',
    'slice_thickness':'Slice Thickness',
    'kernel':'kernel',
    'RA950':'RA950',
    'RA920':'RA920',
    'RA910':'RA910',
    'RA970':'RA970',        
    'PERC15':'PERC15',
    'PERC10':'PERC10'}

def usage():
    print("""
          Usage: pooled_analysis_REDO.py /path/to/results_file.csv /path/to/reference_file.csv /path/to/output_directory/
          
          NOTE: This file is built for the analysis of John's dissertation data
                and should most likely not be used directly, without modification,
                for any other regression analysis.
          
          Copyright (c) John Hoffman 2018
          """)

def printf(s):
    # Helper function.  Prints to STDOUT without necessarily including
    # the newline (unless user specifies it).
    sys.stdout.write(s)
    sys.stdout.flush()

def newline(x,y,ax):
    # Helper function. Draws lines from point a to b
    # x y are tuples of form (x1,x2) (y1,y2).  End points of line are (x1,y1) (x2,y2)
    l = mlines.Line2D(x,y,color='0.75',linestyle='--')
    ax.add_line(l)
    return l    

def main(argc,argv):
    # Command line arguments
    results_csv = argv[1]
    reference_csv = argv[2]
    output_dir = argv[3]

    # Flags
    ref_overlay_flag=False
    ref_marker_flag=False
    
    # Load the data from the CSV file into pandas dataframes
    # Note that the CSV files have headers, and therefor columns can be
    # addressed using commands like results['RA-950'] or results['id']
    printf('Loading data... ')
    results_org = pd.read_csv(results_csv,na_values='None')
    refs_org    = pd.read_csv(reference_csv,na_values='None')
    print('DONE')

    refs = refs_org[ (refs_org.kernel == ref_kernel) &
                     (refs_org.slice_thickness == ref_slice_thickness) &
                     (refs_org.dose == ref_dose)]

    diffs_reference_dataset=refs_org.copy()
    diffs_results_dataset=results_org.copy()


    # Generate difference data for both 
    printf('Generating difference data... ')    
    for idx,l in diffs_reference_dataset.iterrows():
        # Find the reference for the current row
        curr_patient=l['id']
        curr_ref=refs[refs['id']==curr_patient]
        diffs_reference_dataset.at[idx,'RA-950'] = l['RA-950']-curr_ref['RA-950']
        diffs_reference_dataset.at[idx,'PERC15'] = l['PERC15']-curr_ref['PERC15']

    for idx,l in diffs_results_dataset.iterrows():
        # Find the reference for the current row
        curr_patient=l['id']
        curr_ref=refs[refs['id']==curr_patient]
        diffs_results_dataset.at[idx,'RA-950'] = l['RA-950']-curr_ref['RA-950']
        diffs_results_dataset.at[idx,'PERC15'] = l['PERC15']-curr_ref['PERC15']

    if results_csv!=reference_csv:
        ref_overlay_flag==True

    if results_csv.find('wfbp')!=-1 and results_csv.find('bilateral')==-1:
        ref_marker_flag=True

    # Generate our figures
    # Everyone
    printf('Generating pooled plot: full dataset...')    
    if sys.argv[1].find('wfbp')!=-1 and sys.argv[1].find('bilateral')==-1:
        diffs_results=diffs_results_dataset
        diffs_reference=diffs_reference_dataset
        gen_figure(diffs_results_dataset,diffs_reference_dataset,False,ref_marker_flag,'RA-950',output_dir)
        gen_figure(diffs_results_dataset,diffs_reference_dataset,False,ref_marker_flag,'PERC15',output_dir)
    else:
        diffs_results=diffs_results_dataset
        diffs_reference=diffs_reference_dataset
        gen_figure(diffs_results_dataset,diffs_reference_dataset,True,ref_marker_flag,'RA-950',output_dir)
        gen_figure(diffs_results_dataset,diffs_reference_dataset,True,ref_marker_flag,'PERC15',output_dir)
    print('DONE')

    # No emphysema
    printf('Generating pooled plot: no emphysema...')    
    clean_refs=refs.copy()
    data=diffs_results_dataset.copy()
    for idx,r in refs.iterrows():    
        if r['RA-950']>=0.05:
            pipe_id    = r['id'];
            data       = data[data['id']!=pipe_id]
            clean_refs = clean_refs[clean_refs['id']!=pipe_id]
    gen_figure(data,diffs_reference_dataset,True,ref_marker_flag,'RA-950',output_dir,name_modifier='_none')
    gen_figure(data,diffs_reference_dataset,True,ref_marker_flag,'PERC15',output_dir,name_modifier='_none')
    print('DONE')
    
    # Mild emphysema
    printf('Generating pooled plot: mild emphysema...')        
    clean_refs=refs.copy()
    data=diffs_results_dataset.copy()
    for idx,r in refs.iterrows():
        if r['RA-950']<0.05:
            pipe_id    = r['id'];
            data       = data[data['id']!=pipe_id]
            clean_refs = clean_refs[clean_refs['id']!=pipe_id]
    gen_figure(data,diffs_reference_dataset,True,ref_marker_flag,'RA-950',output_dir,name_modifier='_mild')
    gen_figure(data,diffs_reference_dataset,True,ref_marker_flag,'PERC15',output_dir,name_modifier='_mild')
    print('DONE')

    # Moderate emphysema
    printf('Generating pooled plot: moderate emphysema...')        
    clean_refs=refs.copy()
    data=diffs_results_dataset.copy()
    for idx,r in refs.iterrows():    
        if r['RA-950']<0.10:
            pipe_id    = r['id'];
            data       = data[data['id']!=pipe_id]
            clean_refs = clean_refs[clean_refs['id']!=pipe_id]
    gen_figure(data,diffs_reference_dataset,True,ref_marker_flag,'RA-950',output_dir,name_modifier='_moderate')
    gen_figure(data,diffs_reference_dataset,True,ref_marker_flag,'PERC15',output_dir,name_modifier='_moderate')
    print('DONE')

def gen_figure(data_results,data_reference,ref_overlay_flag,ref_marker_flag,metric,output_dir,name_modifier=''):

    plot_vars          = slice_thicknesses    
    series_vars        = kernels
    n_plots_per_figure = len(plot_vars)
    n_series_per_plot  = len(kernels)

    x_axis_vars=doses
    f, ax =plt.subplots(1,n_plots_per_figure,sharey=True,figsize=(4*n_plots_per_figure,4))

    for p,a in zip(plot_vars,ax):
        # Isolate slice thickness data for current slice thickness/plot
        plot_data=data_results[data_results['slice_thickness']==p]
        
        for s in series_vars:
            # Isolate kernel data for current series (i.e. line plot)
            series_data=plot_data[plot_data['kernel']==s]
            x_data=[]
            y_data=[]
            y_err=[]

            for x in x_axis_vars:
                group_data=series_data[series_data['dose']==x]
                #mean=np.mean(group_data[metric])
                #sd=np.std(group_data[metric])
                #sem=sd/np.sqrt(group_data.size)
                mean=group_data[metric].mean()
                sd=group_data[metric].std()
                sem=sd/np.sqrt(group_data[metric].size)
                x_data.append(x);
                y_data.append(mean);
                y_err.append(sem);
            
            marker=next(markers);
            color=next(colors);

            if sys.argv[1].find('safire')==-1:
                kernel_label_dict={
                    1.0:"Smooth",
                    2.0:"Medium",
                    3.0:"Sharp"}                
                a.errorbar(x_data,y_data,yerr=y_err,color=color,fmt=(marker+'-'),label='{} {}'.format(kernel_label_dict[s],label_dict['kernel']))            
            else:
                kernel_label_dict={
                    1.0:"I26",
                    2.0:"I44",
                    3.0:"I50"}
                a.errorbar(x_data,y_data,yerr=y_err,color=color,fmt=(marker+'-'),label='{}'.format(kernel_label_dict[s]))

            kernel_label_dict={
                1.0:"Smooth",
                2.0:"Medium",
                3.0:"Sharp"}                

            a.legend(fontsize=11.0)

            a.set_xlabel(label_dict['dose'])
            a.set_ylabel('Difference {}'.format(metric))
            a.set_title('{}: {}'.format('Slice thickness',p))

            var_series='kernel'
            var_plots='slice_thickness'
            var_x_axis='dose'
            
            # Check for and mark reference (if necessary)
            if (((var_series=='kernel' and s==ref_kernel) or (var_series=='dose' and s==ref_dose) or (var_series=='slice_thickness' and s==ref_slice_thickness)) and
                ((var_plots=='kernel' and p==ref_kernel) or (var_plots=='dose' and p==ref_dose) or (var_plots=='slice_thickness' and p==ref_slice_thickness))):

                x=np.array(x_data)
                y=np.array(y_data)

                if var_x_axis=='kernel':
                    ref=ref_kernel;
                elif var_x_axis=='slice_thickness':
                    ref=ref_slice_thickness
                elif var_x_axis=='dose':
                    ref=ref_dose
                else:
                    print('Something went wrong')
                y=y[x==ref]
                x=x[x==ref]

                if ref_marker_flag:
                    a.plot(x,y,'y*',markersize=13)

    if ref_overlay_flag:
        for p,a in zip(plot_vars,ax):
            # Isolate slice thickness data for current slice thickness/plot
            plot_data=data_reference[data_reference['slice_thickness']==p]
            
            for s in series_vars:
                # Isolate kernel data for current series (i.e. line plot)
                series_data=plot_data[plot_data['kernel']==s]
                x_data=[]
                y_data=[]
                y_err=[]
    
                for x in x_axis_vars:
                    group_data=series_data[series_data['dose']==x]
                    #mean=np.mean(group_data[metric])
                    #sd=np.std(group_data[metric])
                    #sem=sd/np.sqrt(group_data.size)
                    mean=group_data[metric].mean()
                    sd=group_data[metric].std()
                    sem=sd/np.sqrt(group_data.size)
                    x_data.append(x);
                    y_data.append(mean);
                    y_err.append(sem);
                
                marker=next(markers);
                color=next(colors);                
                a.errorbar(x_data,y_data,alpha=0.1,color=color,yerr=y_err,fmt=(marker+'-'),label='{} {}'.format(kernel_label_dict[s],label_dict['kernel']))

    for a in ax:
        a.set_xlim(0,105)
        if metric=='RA-950':
            newline((0,105),(0.05,0.05),a)
            newline((0,105),(-0.05,-0.05),a)
            a.set_ylim((-0.1,.6))
            
        elif metric=='PERC15':
            newline((0,105),(10,10),a)
            newline((0,105),(-10,-10),a)
            a.set_ylim((-150,80))                

        else:
            sys.exit('')

    outfile_name='{}_ref_1.0_{}'.format(metric,kernel_label_dict[ref_kernel])
    plt.savefig(os.path.join(output_dir,'{}{}.{}'.format(outfile_name,name_modifier,'png')),bbox_inches='tight',dpi=600)
    

if __name__=="__main__":

    argc=len(sys.argv)
    argv=sys.argv

    if argc<4:
        usage()
        sys.exit(1)

    main(argc,argv)


    
