import sys
import os

import csv

import numpy as np
import matplotlib as mp
import matplotlib.pyplot as plt

import itertools

########################################
# Configuration data (hopefully so we don't actually have to edit the
# underlying code in the future)
########################################

# Reference condition
ref_kernel=2.0
ref_slice_thickness=1.0
ref_dose=100

# Plot info 
plot_style='error_bars' # choices are 'raw' or 'error_bars'
#plot_ylims='auto'       # 'auto' or tuple
plot_ylims= (-0.075,.35)       # 'auto' or tuple
markers=itertools.cycle(('o','^','s'))

# Output information
display_fig=True
save_fig=True
save_format='png'
outfile_name='950_ref_1.0_medium'
save_dpi=600

########################################

def gen_figure(data,var_y_axis,var_x_axis,var_series,var_plots,plot_type='raw'):

    label_dict={
        'dose':'% Clinical CTDIvol',
        'slice_thickness':'Slice Thickness',
        'kernel':'kernel',
        '950':'RA950',
        '920':'RA920',
        '910':'RA910'
        }

    kernel_label_dict={
        1.0:"Smooth",
        2.0:"Medium",
        3.0:"Sharp"
        }
    
    plot_vars=np.unique(data[var_plots])
    series_vars=np.unique(data[var_series])
    n_plots_per_figure=plot_vars.size
    n_series_per_plot=series_vars.size

    x_axis_vars=np.unique(data[var_x_axis])

    plot_count=1;
    f, ax =plt.subplots(1,n_plots_per_figure,sharey=True,figsize=(4*n_plots_per_figure,4))

    # Plot all available datapoints, no pooling within groups
    if plot_type=='raw':
        for p,a in zip(plot_vars,ax):
            print(plot_count,'/',n_plots_per_figure)
        
            # Extract only the data for this plot
            plot_data=data[data[var_plots]==p]
            
            for s in series_vars:
                # X values are the "var_x_axis"
                # Y values are the "var_y_axis"
                # Extract only the data for the first series
                series_data=plot_data[plot_data[var_series]==s]
                a.plot(series_data[var_x_axis],series_data[var_y_axis],'o',label=s)
                a.set_xlabel(var_x_axis)
                a.set_ylabel(var_y_axis)
                a.set_title('{}: {}'.format(var_plots,p))
                a.legend(fontsize=13.0)
                
            plot_count+=1
            
    # Average together within groups, and calculate error bars
    elif plot_type=='error_bars':
        for p,a in zip(plot_vars,ax):
            print(plot_count,'/',n_plots_per_figure)
        
            # Extract only the data for this plot
            plot_data=data[data[var_plots]==p]
            
            for s in series_vars:
                # X values are the "var_x_axis"
                # Y values are the "var_y_axis"
                # Extract only the data for the first series
                series_data=plot_data[plot_data[var_series]==s]

                x_data=[]
                y_data=[]
                y_err=[]
                
                for x in x_axis_vars:
                    group_data=series_data[series_data[var_x_axis]==x]
                    mean=np.mean(group_data[var_y_axis])
                    sd=np.std(group_data[var_y_axis])
                    print(mean, ':', sd)
                    sem=sd/np.sqrt(group_data.size)
                    x_data.append(x);
                    y_data.append(mean);
                    y_err.append(sem);

                #a.plot(series_data[var_x_axis],series_data[var_y_axis],'o',label=s)
                marker=next(markers);
                if var_series=='kernel':
                    a.errorbar(x_data,y_data,yerr=y_err,fmt=(marker+'-'),label='{} {}'.format(kernel_label_dict[s],label_dict[var_series]))
                else:
                    a.errorbar(x_data,y_data,yerr=y_err,fmt=(marker+'-'),label='{} {}'.format(label_dict[var_series],s))
                a.set_xlabel(label_dict[var_x_axis])
                a.set_ylabel('Difference {}'.format(label_dict[var_y_axis]))
                a.set_title('{}: {}'.format(label_dict[var_plots],p))

                if var_series=='kernel':
                    a.legend(fontsize=11.0)
                else:
                    a.legend(fontsize=13.0)

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
                    a.plot(x,y,'y*',markersize=13)

            plot_count+=1
        
    for a in ax:
        a.set_xlim(20,105)
        if plot_ylims!='auto':
            a.set_ylim(plot_ylims)

    if save_fig:
        plt.savefig('{}.{}'.format(outfile_name,save_format),bbox_inches='tight',dpi=save_dpi)
        
    if display_fig:
        plt.show()

if __name__=="__main__":
    # CL argument is the results files containing the emphysema data

    results_file=sys.argv[1]

    data=np.genfromtxt(results_file,dtype=float,delimiter=',',names=True)

    # Reference values are 100% dose, 5.0 mm slice thickness, smooth kernel reconstruction
    refs = data[data['kernel']==ref_kernel]
    refs = refs[refs['slice_thickness']==ref_slice_thickness]
    refs = refs[refs['dose']==ref_dose]

    diffs=np.copy(data)

    # Calculate our differences
    for l in np.nditer(diffs,op_flags=['readwrite']):
        # Find the reference for the current row
        curr_patient=l['id']
        curr_ref=refs[refs['id']==curr_patient] 

        # Calculate the differences and store back to the array
        l[...]['mean']   = l['mean']-curr_ref['mean']
        l[...]['median'] = l['median']-curr_ref['median']        
        l[...]['950']    = l['950']-curr_ref['950']
        l[...]['920']    = l['920']-curr_ref['920']
        l[...]['910']    = l['910']-curr_ref['910']
        l[...]['15']     = l['15']-curr_ref['15']
        l[...]['20']     = l['20']-curr_ref['20']                        
        l[...]['volume'] = l['volume']-curr_ref['volume']

    # For a fixed recon condition (s.t., kernel) plot the change in recon variable
    #gen_figure(data,var_y_axis,var_x_axis,var_series,var_plots,plot_type='raw'||'error_bars'):    
    gen_figure(diffs,'950','dose','kernel','slice_thickness',plot_type=plot_style)


