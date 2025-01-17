import os
import pandas as pd
import csv

def VFFVA(nCores, nThreads, model, scaling=0, memAff='none', schedule='dynamic', nChunk=50, optPerc=90, ex=[]):
    '''
    VFFVA performs Very Fast Flux Variability Analysis (VFFVA). VFFVA is a parallel implementation of FVA that
    allows dynamically assigning reactions to each worker depending on their computational load
    Guebila, Marouen Ben. "Dynamic load balancing enables large-scale flux variability analysis." bioRxiv (2018): 440701.

    USAGE:
    minFlux,maxFlux=VFFVA(nCores, nThreads, model, scaling, memAff, schedule, nChunk, optPerc, ex)

    :param nCores:   Number of non-shared memory cores/machines.
    :param nThreads: Number of shared memory threads in each core/machine.
    :param model:    .mps format: path to metabolic model in .mps format.
    :param scaling:  CPLEX parameter. It corresponds to SCAIND parameter (Default = 0).
                     -1: no scaling; 0: equilibration scaling; 1: more aggressive scaling.
                     more information here: https://www.ibm.com/support/knowledgecenter/SSSA5P_12.7.0/ilog.odms.cplex.help/CPLEX/Parameters/topics/ScaInd.html.
    :param memAff:   'none', 'core', or 'socket'. (Default = 'none'). This an OpenMPI parameter, more
                     information here: https://www.open-mpi.org/faq/?category=tuning#using-paffinity-v1.4.
    :param schedule: 'dynamic', 'static', or 'guided'. (Default = 'dynamic'). This is an OpenMP parameter, more
                     information here: https://software.intel.com/en-us/articles/openmp-loop-scheduling
    :param nChunk:   Number of reactions in each chunk (Default = 50). This is an OpenMP parameter, more
                     information here: https://software.intel.com/en-us/articles/openmp-loop-scheduling
    :param optPerc:  Percentage of the optimal objective used in FVA. Integer between 0 and 100. For example, when set to 90
                     FVA will be computed on 90% of the optimal objective.
    :param ex:      0-based indices of reactions to optimize as a numpy array.  (Default, all reactions)
    :return:
           minFlux:          (n,1) vector of minimal flux values for each reaction.
           maxFlux:          (n,1) vector of maximal flux values for each reaction.
    '''

    status = os.system('mpirun --version')
    if status != 0:
        raise ValueError(['MPI and/or CPLEX nont installed, please follow the install guide'
               'or use the quick install script'])

    # Set schedule and chunk size parameters
    os.environ["OMP_SCHEDUELE"] = schedule+str(nChunk)

    # Set reactions to optimize
    if ex!=[]:
        with open('rxns.csv', 'w', newline='') as myfile:
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            wr.writerow(ex)
        ex='rxns.csv'
    else:
        ex=''

    # Call VFFVA
    status = os.system(
        'mpirun -np ' + str(nCores) + ' --bind-to ' + str(memAff) + ' -x OMP_NUM_THREADS=' + str(nThreads) +
         ' ./veryfastFVA ' + model + ' ' + str(optPerc) + ' ' + str(scaling) + ' ' + ex)

    # Fetch results
    resultFile = model[:-4] + 'output.csv'
    results = pd.read_csv(resultFile)
    minFlux = results.minFlux
    maxFlux = results.maxFlux

    # remove result file
    os.system('rm '+resultFile)
    if ex!='':
        os.system('rm '+ex)

    return minFlux,maxFlux

def test_VFFVA():
    minFlux,maxFlux=VFFVA(2, 2, '../data/models/Ecoli_core/Ecoli_core.mps',ex=[1,2,10,5,46])
    print(minFlux)

test_VFFVA()