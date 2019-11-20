import os
import sys
import subprocess
import numpy as np
import time

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
    if args is None:
        folder_loc = time.strftime("%Y.%m.%d-%H%M%S")
    else:
        folder_loc = ''
        for arg in args:
            folder_loc = '{}_{}'.format(folder_loc, arg)

    os.system('mkdir ' + folder_loc)
    for file in mv_files:
        try:
            os.system('mv {} {}/{}'.format(file, folder_loc, file))
            #print("\rMoved {:s} succesfully!".format(file), end=' '*15)
        except:
            print("\rFailed to move {:s}".format(file))
            raise
        
    print('')

def archive_results(seeds):
    """ Moves all the resulting folders in a single one, in the "results" folder, by name. """
    # Moves all created folder and result files in a single folder
    datetime =time.strftime("%Y.%m.%d-%H%M%S")
    try:
        os.system(str('mkdir Results/'+str(datetime)))
    except:
        print("\rFailed to create folder Results/{:s}".format(datetime))
    try:
        os.system('mv results.log Results/{:}/results.log'.format(datetime))
    except:
        print("\rFailed to move results.log")
    for seed in seeds:
        mv_folders = (folder for folder in os.listdir() if folder.endswith(str(seed)))
        for folder in mv_folders:
            try:
                os.system('mv {} Results/{}/{}'.format(folder, datetime, folder))
                #print("\rMoved {:s} succesfully!".format(file), end=' '*15)
            except:
                print("\rFailed to move {:s}".format(folder))
                raise

def change_input(filename, frac_p, frac_w, seed=None):
    """Creates a new dmpci.pcs_sim with updated number fraction values (cf dpd doc)"""
    
    with open(filename, 'rt') as rf:
        with open(filename+'_sim', 'wt') as wf:

            for line in rf:
                if line.startswith('Polymer PEG'):
                    line = line.strip().split()
                    line[2] = frac_p
                    # Converts list to list[str]
                    line = list(map(lambda x: str(x), line))
                    wf.write('\t'.join(line) + '\n')
                    
                    # Gets next line
                    line = next(rf)
                    wf.write('\n')

                elif line.startswith('Polymer Water'):
                    c_line = line
                    c_line = c_line.strip().split()
                    c_line[2] = frac_w
                    
                    # Converts list to list[str]
                    c_line = list(map(lambda x: str(x), c_line))

                    wf.write('\t'.join(c_line)+'\n')

                elif line.startswith('RNGSeed') and seed:
                    wf.write('{:<12}{:<}\n'.format('RNGSeed',seed))
                else:
                    wf.write(line)
                    
def get_lengths(filename, polymer, time, means, stds):
    """Parses 'as' file to get the EE length mean and std, time allows to return the correct ee lengths based on dmpci analysis time"""
    time_toggle = 0
    with open(filename, 'rt') as f:
        for line in f:
            if line.startswith('Time = {}'.format(time)):
                time_toggle = 1
            if (line.startswith('{} EE distance'.format(polymer)) and time_toggle == 1):
                line = next(f)
                means.append(float(line.split()[0]))
                stds.append(float(line.split()[1]))
                break
        else:
            raise EOFError('No {} EE distance found'.format(polymer))
        
def main():

    # Creates a file to store the simulation values
    with open('results.log', 'wt') as f:    
        f.write("{:<8s}\t{:<8s}\t{:<8s}\t{:<8s}\t{:<8s}\n".format("N pol", "Mean", "Std", "Seed", "FracP"))
    
    means = []
    stds = []
    # density, defined in dmpci
    density = 3
    # Water beads volume !! Does not change !!
    V_w = 4 * (0.5)**3
    # Simulation box volume !! Can be changed in dmpci !!
    V_sim = 15*15*15
    # Number of PEG polymer in the simulation volume
    N_p = np.linspace(1, 100, 100)
    np.random.seed(279)
    seeds = np.random.randint(-9999,-1000,size=10)
    print(seeds)
    for i in range(N_p.shape[0]):
        for seed in seeds:
            # Polymer & water density
            frac_p = "%.4f" % round(N_p[i]/(density * V_sim), 4)
            frac_w = "%.4f" % round(1 - (N_p[i]/(density * V_sim)), 4)
            change_input('dmpci.pcs', frac_p, frac_w, seed)

            # Starts simulation
            os.system(str('./dpd-linux pcs_sim'))

            #Get EE length
            get_lengths('dmpcas.pcs_sim','PEG', 3000, means, stds)

            # Writes data to file
            with open('results.log', 'a') as f:
                f.write("{:.4f}\t{:.4f}\t{:.4f}\t{:.4f}\t{:s}\n".format(N_p[i], means[-1], stds[-1], seed, frac_p))
            print(N_p[i], means[-1], stds[-1])
            
            # Archive simulation files
            clean_cwd(N_p[i], seed)
    # Archive the simulation folders
    archive_results(seeds)
            
        


if __name__ == "__main__":
    main()
