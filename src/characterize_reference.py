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

metric='NA'

# Reference condition
ref_kernel=2.0
ref_slice_thickness=1.0
ref_dose=100

# Plot info 
plot_style='error_bars' # choices are 'raw' or 'error_bars'
markers=itertools.cycle(('o','^','s'))
if metric=='PERC15':
    #plot_ylims=(-120,65)
    plot_ylims=(-150,80)    
elif metric=='RA950':
    #plot_ylims= (-0.075,.45)        # 'auto' or tuple RA-950: (-0.075,.45) PERC15:(-120,65)
    plot_ylims= (-0.1,.6)
else:
    plot_ylims='auto'       # 'auto' or tuple

# Output information
display_fig=False
save_fig=True
save_format='png'
kernels={2.0:'medium',1.0:'smooth',3.0:'sharp'}
outfile_name='{}_ref_1.0_{}_emphy_only_10'.format(metric,kernels[ref_kernel])
save_dpi=600

print("Metric:    {}".format(metric))
print("Outfile:   {}".format(outfile_name))
print("Reference: k{},s{},d{}".format(ref_kernel,ref_slice_thickness,ref_dose))

########################################

def gen_figure(data,var_y_axis,var_x_axis,var_series,var_plots,plot_type='raw'):

    label_dict={
        'dose':'% Clinical CTDIvol',
        'slice_thickness':'Slice Thickness',
        'kernel':'kernel',
        'RA950':'RA950',
        'RA920':'RA920',
        'RA910':'RA910',
        'RA970':'RA970',        
        'PERC15':'PERC15',
        'PERC10':'PERC10'
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
            #print(plot_count,'/',n_plots_per_figure)
        
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
            #print(plot_count,'/',n_plots_per_figure)
        
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
                    #print(mean, ':', sd)
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
        a.set_xlim(0,105)
        if plot_ylims!='auto':
            a.set_ylim(plot_ylims)

    if save_fig:
        plt.savefig('{}.{}'.format(outfile_name,save_format),bbox_inches='tight',dpi=save_dpi)
        
    if display_fig:
        plt.show()

if __name__=="__main__":
    # CL argument is the results files containing the emphysema data

    results_file=sys.argv[1]
    reference_file=sys.argv[2]

    ndtype=[('pipeline_id',str),('id',str),('dose',float),('kernel',float),('slice_thickness',float),
            ('RA-900',float),('RA-910',float),('RA-920',float),('RA-930',float),('RA-940',float),
            ('RA-950',float),('RA-960',float),('RA-970',float),('RA-980',float),('PERC10',float),
            ('PERC15',float),('PERC20',float),('median',float),('mean',float),('volume',float)]
    
    data=np.genfromtxt(results_file,dtype=None,delimiter=',',names=True)
    data_reference=np.genfromtxt(reference_file,dtype=None,delimiter=',',names=True)
    #data_string=np.genfromtxt(results_file,dtype=None,delimiter=',',names=True)

    # Reference values are 100% dose, 5.0 mm slice thickness, smooth kernel reconstruction
    refs = data_reference[data_reference['kernel']==ref_kernel]
    refs = refs[refs['slice_thickness']==ref_slice_thickness]
    refs = refs[refs['dose']==ref_dose]

    np.savetxt('reference_ref_1.0_{}.csv'.format(kernels[ref_kernel]),refs,'%s',delimiter=',',header='id,dose,kernel,slice_thickness,RA900,RA910,RA920,RA930,RA940,RA950,RA960,RA970,RA980,PERC10,PERC15,PERC20,median,mean,volume,org_filepath')

    # Save key info about dataset to disk
    with open('summary_data_ref_1.0_{}.yaml'.format(kernels[ref_kernel]),'w') as f:
        f.write('Total: {}\n'.format(refs.shape))

        # Get info about <0.05 RA950 cases
        clean_refs=np.copy(refs)
        for r in refs:
            if r['RA950']>=0.05:
                pipe_id    = r['id'];
                clean_refs = clean_refs[clean_refs['id']!=pipe_id]

        f.write('Total(<0.05): {}\n'.format(clean_refs.shape));

        # Get info about >0.05 & <0.10 RA950 cases
        clean_refs=np.copy(refs)
        for r in refs:
            if r['RA950']<0.05 or r['RA950']>=0.10:
                pipe_id    = r['id'];
                clean_refs = clean_refs[clean_refs['id']!=pipe_id]

        f.write('Total(>0.05 and <=0.10): {}\n'.format(clean_refs.shape));
        
        # Get info about >=0.10 RA950 cases
        clean_refs=np.copy(refs)
        for r in refs:
            if r['RA950']<=0.1:
                pipe_id    = r['id'];
                clean_refs = clean_refs[clean_refs['id']!=pipe_id]

        f.write('Total(>=0.10): {}\n'.format(clean_refs.shape));
