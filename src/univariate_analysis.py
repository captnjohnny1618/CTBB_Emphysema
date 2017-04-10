import sys
import os

import csv

import numpy as np
import matplotlib as mp
import matplotlib.pyplot as plt

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
plot_ylims= (-0.075,0.2)#'auto'       # 'auto' or tuple

# Output information
display_fig=True
save_fig=True
save_format='png'
outfile_name='950_ref_1.0_medium'
save_dpi=600

########################################

def means_and_sds(data,var_y_axis,var_x_axis):

    x_axis_vars=np.unique(data[var_x_axis])
    x_data=[]
    y_data=[]
    y_err=[]
    
    for x in x_axis_vars:
        group_data=data[data[var_x_axis]==x]
        mean=np.mean(group_data[var_y_axis])
        sd=np.std(group_data[var_y_axis]) # Standard Deviation
        sem=sd/np.sqrt(group_data.size)   # Standard error of the means
        print(np.sqrt(group_data.size))
        x_data.append(x);
        y_data.append(mean);
        y_err.append(sem);

    return (x_data,y_data,y_err)

def gen_figure(data,var_y_axis,plot_type='raw'):

    # We want three, "dumbed-down" plots:
    # (1) Emphysema score vs. dose
    # (2) Emphysema score vs. slice-thickness
    # (3) Emphysema score vs. kernel

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
    
    # Set up the figure
    n_plots=3;
    f, ax =plt.subplots(1,n_plots,sharey=True,figsize=(4*n_plots,4))

    if plot_type=='raw':
        # Make plot (1)
        sub_data=data[data['kernel']==1.0]
        sub_data=sub_data[sub_data['slice_thickness']==5.0]
        ax[0].plot(sub_data['dose'],sub_data[var_y_axis],'o')
        
        # Make plot (2)
        sub_data=data[data['kernel']==1.0]
        sub_data=sub_data[sub_data['dose']==100]
        ax[1].plot(sub_data['slice_thickness'],sub_data[var_y_axis],'o')
        
        # Make plot (3)
        sub_data=data[data['slice_thickness']==5.0]
        sub_data=sub_data[sub_data['dose']==100]
        ax[2].plot(sub_data['slice_thickness'],sub_data[var_y_axis],'o')
        
    elif plot_type=='error_bars':
        # Make plot (1)
        sub_data=data[data['kernel']==ref_kernel]
        sub_data=sub_data[sub_data['slice_thickness']==ref_slice_thickness]
        x_data,y_data,y_err=means_and_sds(sub_data,'950','dose')
        ax[0].errorbar(x_data,y_data,yerr=y_err,fmt='ko-')
        # Mark reference
        x=np.array(x_data)
        y=np.array(y_data)
        y=y[x==ref_dose]
        x=x[x==ref_dose]
        ax[0].plot(x,y,'y*',markersize=13)
        
        # Make plot (2)
        sub_data=data[data['kernel']==ref_kernel]
        sub_data=sub_data[sub_data['dose']==ref_dose]
        x_data,y_data,y_err=means_and_sds(sub_data,'950','slice_thickness')
        ax[1].errorbar(x_data,y_data,yerr=y_err,fmt='ko-')
        # Mark reference
        x=np.array(x_data)
        y=np.array(y_data)
        y=y[x==ref_slice_thickness]
        x=x[x==ref_slice_thickness]
        ax[1].plot(x,y,'y*',markersize=13)
        
        # Make plot (3)
        sub_data=data[data['slice_thickness']==ref_slice_thickness]
        sub_data=sub_data[sub_data['dose']==ref_dose]
        x_data,y_data,y_err=means_and_sds(sub_data,'950','kernel')
        ax[2].errorbar(x_data,y_data,yerr=y_err,fmt='ko-')
        # Relabel kernel sharpness
        #ax[2].set_xticklabels([1.0,2.0,3.0],['Smooth','Medium','Sharp'],rotation='vertical')
        ax[2].set_xticks([1.0,2.0,3.0]);
        ax[2].set_xticklabels(['Smooth','Medium','Sharp'],rotation=45.0)

        
        # Mark reference
        x=np.array(x_data)
        y=np.array(y_data)
        y=y[x==ref_kernel]
        x=x[x==ref_kernel]
        ax[2].plot(x,y,'y*',markersize=13)
        

    # Set titles and labels
    ax[0].set_xlabel('% Clinical CTDIvol')
    ax[0].set_ylabel('Difference RA950')
    ax[0].set_title('Medium Kernel, 1.0 mm slices')
    ax[0].set_xlim(20,105)

    ax[1].set_xlabel('Slice Thickness (mm)')
    #ax[1].set_ylabel('Difference RA950')
    ax[1].set_title('100% CTDIvol, Medium Kernel')
    ax[1].set_xlim(0.5,5.5)

    ax[2].set_xlabel('Kernel Sharpness')
    #ax[2].set_ylabel('Difference RA950')
    ax[2].set_title('100% CTDIvol, 1.0mm slices')
    ax[2].set_xlim(0.9,3.1)

    if plot_ylims!='auto':
        ax[0].set_ylim(plot_ylims)

    if save_fig:
        f.savefig('{}_univariate.{}'.format(outfile_name,save_format),bbox_inches='tight',dpi=save_dpi)
        
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
    gen_figure(diffs,'950',plot_type=plot_style)


