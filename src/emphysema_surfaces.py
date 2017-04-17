import sys
import os

import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

kernel_label_dict={
    1.0:"Smooth",
    2.0:"Medium",
    3.0:"Sharp"
    }

def emphysema_differences(data,patient,emphysema_measure):
    # This function determines the difference between the maximum and
    # minimum emphysema scores for a patient.  A little more verbose
    # than needed for clarity

    # Extract data for requested patient
    data=data[data['id']==patient]

    # Extract data for specific emphysema measure
    scores=data[emphysema_measure]

    # Compute difference
    maximum=scores.max()
    minimum=scores.min()
    diff=maximum-minimum

    print(str(patient) + " , " + str(minimum) + " , " + str(maximum) + " , " + str(diff) +  " , " + str(scores.mean()) +" , "  + str(np.median(scores)))

def emphysema_surfaces(data,patient,emphysema_measure,output_dir):
    # This function generates surface plots of emphysema scores for a
    # given patient

    # Inputs:
    #    data - full numpy array of data read from CSV
    #    patient - patient id, used directly to index numpy array so much match CSV value
    #    emphysema_measure - string specifying of measure to be plotted. Accepted values are '950','920','910','15', and '20'. 
    
    # Three possible surfaces for each patient:
    #   emphysema score vs (slice_thickness, dose)
    #   emphysema score vs (dose, kernel)
    #   emphysema score vs (kernel,slice_thickness)

    data=data[data['id']==patient]

    # Determine the number of slice thicknesses, doses and kernel available
    vals                    = {}
    vals['slice_thickness'] = np.unique(data['slice_thickness'])
    vals['dose']            = np.unique(data['dose'])    
    vals['kernel']          = np.unique(data['kernel'])

    n={}
    n['slice_thickness'] = len(vals['slice_thickness'])
    n['dose']            = len(vals['dose'])
    n['kernel']          = len(vals['kernel'])
    
    fig = plt.figure(figsize=(9*3,9))

    def gen_plot(hold_constant,x,y,idx):
        ax = fig.add_subplot(130+idx,projection='3d')
        
        cmap = plt.get_cmap('jet')
        colors = cmap(np.linspace(0, 1, n[hold_constant]))

        for i, c in zip(vals[hold_constant],colors):
            data_1=data[data[hold_constant]==i]

            data_1.sort(order=['dose','kernel','slice_thickness'],axis=0)
            
            if hold_constant=='slice_thickness':
                lab=('S.T. {}mm'.format(str(i)));
            elif hold_constant=='kernel':
                lab=('{} kernel'.format(kernel_label_dict[i]));
            elif hold_constant=='dose':
                lab=('Perc. Dose {}'.format(str(i)));
            else:
                pass

            mesh_1=data_1[x].reshape(n[y],n[x])
            mesh_2=data_1[y].reshape(n[y],n[x])
            mesh_3=data_1[emphysema_measure].reshape(n[y],n[x])
                
            ax.plot_wireframe(mesh_1,mesh_2,mesh_3,linewidth=1,color=c,label=lab)
            
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        p=patient.decode("UTF-8")
        p=p.replace("17007_SCMP2DFA","").replace(".ptr","")

        ax.set_title("Patient {}; {}".format(p,emphysema_measure))
        ax.legend(bbox_to_anchor=(1,.91))
        ax.set_zlim3d(0,0.5)

        if y=='kernel':
            ax.set_yticks([1.0,2.0,3.0])
            ax.set_yticklabels(['Smooth','Medium','Sharp'],rotation=-21,ha='center',va='top')#multialignment='right')

        if hold_constant=='kernel':
            ax.view_init(elev=18,azim=-50)
        elif hold_constant=='slice_thickness':
            ax.view_init(elev=18,azim=40)
        elif hold_constant=='dose':
            ax.view_init(elev=18,azim=40)            
        else:
            pass

    gen_plot('kernel','slice_thickness','dose',1)
    gen_plot('dose','slice_thickness','kernel',2)
    gen_plot('dose','slice_thickness','kernel',3)

    p=patient.decode("UTF-8")
    p=p.replace("17007_SCMP2DFA","").replace(".ptr","")
    print(p)

    #plt.show()
    plt.savefig(os.path.join(output_dir,'emphy_surfaces_patient_{}.png'.format(p)),bbox_inches='tight',dpi=200);
    
if __name__=="__main__":
    # CL argument is the results files containing the emphysema data

    results_file=sys.argv[1]

    if len(sys.argv)<2:        
        output_dir=os.getcwd()
    else:
        output_dir=sys.argv[2]

    data=np.genfromtxt(results_file,dtype=None,delimiter=',',names=True)

    # Each patient has the following measures in the results file:
    #
    #  RAs:
    #   950
    #   920
    #   910
    #  
    #  Percentiles:
    #   15
    #   20
    # 
    # These are given for each patient, dose, kernel, and slice_thickness

    for i in np.unique(data['id']):
        emphysema_surfaces(data,i,'RA950',output_dir)
        
#        emphysema_differences(data,i,'950')
#
