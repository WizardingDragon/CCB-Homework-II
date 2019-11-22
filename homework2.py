import os
import platform
import shutil
import subprocess
import sys
import time

import numpy as np


def clean_cwd(*args):
    """Removes most of the simulation files from the current directory"""

    # Generator of the files generated for each runs
    mv_files = (file for file in os.listdir() if file.endswith('.vtk')
                or file.endswith('.dat')
                or file.startswith('eeldata')
                or file.startswith('dmpcis.')
                or file.startswith('dmpcls.')
                or file.startswith('dmpchs.')
                or file.startswith('dmpcas.')
                or file.endswith('_sim'))

    # If no argument were given to name the folder, we will default to date and time to name the folder and archive the simulation files.
    folder_loc = '_'.join(list(map(str, args))) if args is not None else time.strftime("%Y.%m.%d-%H%M%S")
    os.makedirs(folder_loc, exist_ok=True)

    for file in mv_files:
        try:
            shutil.move(file, os.path.join(folder_loc, file))
        except:
            print(f"Failed to move {file}")
            raise
        
    print('')


def archive_results(seeds):
    """ Moves all the resulting folders in a single one, in the 'results' folder, by name. """

    # Moves all created folder and result files in a single folder
    datetime = time.strftime("%Y.%m.%d-%H%M%S")
    try:
        os.makedirs(f"Results/{datetime}")
    except:
        print("Failed to create folder Results/{:s}".format(datetime))
        raise

    try:
        shutil.move('results.log', f"Results/{datetime:s}/results.log")        
    except:
        print("Failed to move results.log")

    for seed in seeds:
        mv_folders = (folder for folder in os.listdir() if folder.endswith(str(seed)))
        for folder in mv_folders:
            try:
                shutil.move(folder, f"Results/{datetime}/{folder}")
            except:
                print(f"Failed to move {folder}")
                raise


def change_input(filename, frac_p, seed=None, time=3000):
    """Creates a new dmpci.pcs_sim with updated number fraction values (cf dpd doc)"""

    frac_p = round(frac_p, 5)
    frac_w = 1 - frac_p

    params = {'Box': "20 20 20\t1 1 1", 'RNGSeed': seed if seed is not None else -4073, 'Step': 0.04, 'Time': time, 
              'SamplePeriod': 100, 'AnalysisPeriod': time //30, 'DensityPeriod': time, 'DisplayPeriod': time //10, 'RestartPeriod': time,
              }

    with open(filename, 'rt') as rf:
        with open(filename+'_sim', 'wt') as wf:

            for line in rf:

                if line.startswith('Polymer Water'):
                    line = line.strip().split()
                    line[2] = f"{frac_w:.5f}"
                    
                    # Converts list to list[str]
                    line = list(map(str, line))
                    wf.write('\t'.join(line) + '\n')  
                    line = next(rf) 

                if line.startswith('Polymer PEG'):
                    line = line.strip().split()
                    line[2] = f"{frac_p:.5f}"

                    # Converts list to list[str]
                    line = list(map(str, line))
                    wf.write('\t'.join(line) + '\n')
                    line = next(rf)
                    
                if line.strip().split() and line.strip().split()[0] in params.keys():
                    key = line.strip().split()[0]
                    wf.write(f"{key:<12}\t{str(params[key])}\n")

                else:
                    wf.write(line)
                    

def get_lengths(filename, polymer, time, means, stds):
    """Parses 'as' file to get the EE length mean and std, time allows to return the correct ee lengths based on dmpci analysis time"""

    time_toggle = False
    with open(filename, 'rt') as f:
        for line in f:
            if line.startswith(f"Time = {time}"):
                time_toggle = True

            if line.startswith(f"{polymer} EE distance") and time_toggle:
                line = next(f)
                means.append(float(line.strip().split()[0]))
                stds.append(float(line.strip().split()[1]))
                break

        else:
            raise EOFError(f"No {polymer} EE distance found")
        

def main():

    # Creates a file to store the simulation values
    with open('results.log', 'wt') as f:    
        f.write("{:<8s}\t{:<8s}\t{:<8s}\t{:<8s}\t{:<8s}\n".format("N pol", "Mean", "Std", "Seed", "FracP"))
    
    means = []
    stds = []
    # density, defined in dmpci
    density = 3
    # Water beads volume !! Does not change !!
    V_w = 4 * 0.5 **3
    # Simulation box volume !! Can be changed in dmpci !!
    V_sim = 20 **3
    # Number of PEG polymer in the simulation volume
    N_p = np.linspace(10, 60, 58)
    np.random.seed(279)
    seeds = np.random.randint(-9999, -1000, size=1)

    for i in range(N_p.shape[0]):
        for seed in seeds:
            # Polymer & water density
            
            frac_p = N_p[i]/(density * V_sim)
            change_input('dmpci.pcs', frac_p, seed)

            # Starts simulation
            os.system('dpd-w10.exe pcs_sim') if platform.system().lower() == 'windows' else os.system('./dpd-linux pcs_sim')

            #Get EE length
            get_lengths('dmpcas.pcs_sim', 'PEG', 30000, means, stds)

            # Writes data to file
            with open('results.log', 'a') as f:
                f.write(f"{N_p[i]:.4f}\t{means[-1]:.4f}\t{stds[-1]:.4f}\t{seed:.4f}\t{frac_p:.4f}\n")

            print(N_p[i], means[-1], stds[-1])
             
            # Archive simulation files
            clean_cwd(N_p[i], seed)

    # Archive the simulation folders
    archive_results(seeds)


if __name__ == "__main__":
    main()
