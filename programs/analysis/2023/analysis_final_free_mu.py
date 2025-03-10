import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
import scipy.stats as stats
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp
import sys
from brokenaxes import brokenaxes
from matplotlib.gridspec import GridSpec
import os
from scipy import odr
from collections import OrderedDict
from matplotlib.offsetbox import AnchoredText
from optparse import OptionParser

import utilities as uti
import corrections as cor
import geometry as geo

star = sys.argv[1]

# Option parser for options
parser = OptionParser()
parser.add_option("-o", "--only", dest="onlys", help="only telescope combinations")

(options, args) = parser.parse_args()
onlys = str(options.onlys)

if onlys != "None":
    onlys = onlys.split(",")

bl_HBT = []
# Open text file with star data from HBT
f = open("stars_HBT.txt")
# Find line for the star
line = f.readline()
while star not in line:
    line = f.readline()
lam_HBT = line.split()[1]
ang_HBT = uti.mas2rad(float(line.split()[2]))
logg_star = line.split()[3]
temp_star = int(line.split()[4])
line = f.readline()
while "[end]" not in line:
    bl_HBT.append(float(line.split()[0]))
    line = f.readline()
f.close()

combicolorsA = np.zeros((5,5), dtype=object); combicolorsA[:] = np.nan
combicolorsA[1,3] = 'lightblue'
combicolorsA[1,4] = 'deepskyblue'
combicolorsA[3,4] = 'dodgerblue'

combicolorsB = np.zeros((5,5), dtype=object); combicolorsB[:] = np.nan
combicolorsB[1,3] = 'mediumpurple'
combicolorsB[1,4] = 'blueviolet'
combicolorsB[3,4] = 'purple'

combicolors = np.zeros((5,5), dtype=object); combicolors[:] = np.nan
combicolors[1,3] = "blue"
combicolors[1,4] = "fuchsia"
combicolors[3,4] = "turquoise"

# Create array of fixed parameters
mu_A = np.zeros((5,5)); mu_A[:] = np.nan
mu_B = np.zeros((5,5)); mu_B[:] = np.nan
sigma_A = np.zeros((5,5)); sigma_A[:] = np.nan
sigma_B = np.zeros((5,5)); sigma_B[:] = np.nan
amp_A = np.zeros((5,5)); amp_A[:] = np.nan
amp_B = np.zeros((5,5)); amp_B[:] = np.nan

lam_g = 470e-9
lam_uv = 375e-9
lam_all = 422.5e-9
amp_g = 21.25
amp_uv = 10

ratioA = []; ratioB = []

################################################
#### Analysis over whole measurement time #####
################################################
plt.figure("CrossCorr", figsize=(12,8))
def par_fixing(star, telcombi):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)
    plotnumber = len(telcombis)*100 + 10 + telcombis.index(telstring) + 1

    # Read in the data g2 functions
    chAs    = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))     
    chBs    = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))      

    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
    
    # Combine all data for channel A and B each for initial parameter estimation and fixing
    g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
    for i in range (0,len(chAs)):
        #plt.plot(chAs[i]); plt.plot(chBs[i]); plt.show()
        g2_allA += chAs[i]/np.std(chAs[i][0:4500])**2
        g2_allB += chBs[i]/np.std(chBs[i][0:4500])**2
    g2_allA /= np.mean(g2_allA[0:4500])
    g2_allB /= np.mean(g2_allB[0:4500])

    # Fit for gaining mu and sigma to fix these parameters for different baseline combis
    plt.figure("CrossCorr")
    plt.subplot(plotnumber)
    plt.title("Cross correlation data of {} for {}".format(star, telstring))
    print("Fixed parameters")
    # Channel A
    xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
    mu_A[c1][c2] = popt[1]; sigma_A[c1][c2] = popt[2] # fixing mu and sigma
    amp_A[c1][c2] = popt[0]*1e7
    noise_A = np.std(g2_allA)*1e7
    dmuA = []; dsigA = []
    dmuA = perr[1]; dsigA = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print("{} A 470nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t A Noise: {:.2f} \t Ratio: {:.2f}".format(telstring, amp_A[c1][c2], perr[0]*1e7, mu_A[c1][c2], perr[1],sigma_A[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_A, amp_A[c1][c2]/noise_A))
    ratioA.append(amp_A[c1][c2]/noise_A)
    plt.plot(x, g2_allA, label=telstring + "A", color=uti.color_chA)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    # Channel B
    xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
    mu_B[c1][c2] = popt[1]; sigma_B[c1][c2] = popt[2]
    amp_B[c1][c2] = popt[0]*1e7
    noise_B = np.std(g2_allB)*1e7
    dmuB = []; dsigB = []
    dmuB = perr[1]; dsigB = perr[2]
    integral, dintegral = uti.integral(popt, perr)
    print ("{} B 375nm amp: {:.2f}e-7 +/- {:.2f}e-7 \t mean: {:.2f} +/- {:.2f} ns \t sigma: {:.2f} +/- {:.2f} ns \t integral: {:.2f} +/- {:.2f} fs \t B Noise: {:.2f} \t Ratio: {:.2f}".format(telstring,amp_B[c1][c2], perr[0]*1e7, mu_B[c1][c2],perr[1],sigma_B[c1][c2],perr[2],1e6*integral,1e6*dintegral, noise_B, amp_B[c1][c2]/noise_B))
    ratioB.append(amp_B[c1][c2]/noise_B)
    plt.plot(x, g2_allB, label=telstring + "B", color=uti.color_chB)
    plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")
    
    plt.legend(); plt.xlim(-100,100); plt.grid()
    plt.ticklabel_format(useOffset=False)
    plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")
    plt.tight_layout()
    print(f'DONE par fixing for {telstring}')


#########################################
###### Chunk analysis ###################
#########################################
plt.figure('SC', figsize=(12,8))
plt.suptitle("Spatial coherence of {}".format(star))

intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
ints_fixedA = []; dints_fixedA = []
ints_fixedB = []; dints_fixedB = []
ints_fixedA1 = []; dints_fixedA1 = []
ints_fixedB1 = []; dints_fixedB1 = []
baselines_all = []; dbaselines_all = []
time_all = [] ; telstrings =[]
baselinesA = []; dbaselinesA = []
baselinesB = []; dbaselinesB = []


def chunk_ana(star, telcombi, ratioA, ratioB):
    c1 = telcombi[0]
    c2 = telcombi[1]
    telstring = "{}{}".format(c1,c2)  
    
    # initialize cleaned arrays
    chA_clean = []; chB_clean = []; ampA = []; ampB = []; muA = []; muB =[] ; chiA =[]; chiB = []; dmuA = []; dmuB =[]
    ffts = []
    chAs    = np.loadtxt("g2_functions/{}/{}/chA.g2".format(star, telstring))
    chBs    = np.loadtxt("g2_functions/{}/{}/chB.g2".format(star, telstring))

    # Read the telescope data (acquisition times of chunks, baselines and baseline uncertainties)
    timestrings = np.loadtxt("g2_functions/{}/{}/ac_times.txt".format(star,telstring))
    baselines   = np.loadtxt("g2_functions/{}/{}/baselines.txt".format(star,telstring))
    dbaselines  = np.loadtxt("g2_functions/{}/{}/dbaselines.txt".format(star,telstring))
    
    # Demo function for initializing x axis and some stuff
    demo = chAs[0]
    x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

    # Define figure which will show individual g2 cross correlations for 470nm chA
    a = int(len(chAs)/3)
    print(len(chAs),a)
    singlesA, axsA = plt.subplots(a,3, sharex=True, sharey=True)
    singlesA.suptitle(f'Single g2 functions for {telstring} and 470nm')
    singlesA.supxlabel('Time difference (ns)')
    singlesA.supylabel('$g^(2)$')

    singlesB, axsB = plt.subplots(a,3, sharex=True, sharey=True)
    singlesB.suptitle(f'Single g2 functions for {telstring} and 375nm')
    singlesB.supxlabel('Time difference (ns)')
    singlesB.supylabel('$g^(2)$')

    # Define figure to show integrals of g2 fcts
    plt.figure(f'Integrals {telstring}')
    plt.suptitle(f'Integrals of single g2 functions for {telstring}')

    # loop over every g2 function chunk
    for i in range(0,len(chAs)):
        # Check acquisition time of original data
        timestring = ephem.Date(timestrings[i])
        tstring_short = str(timestring)[5:-3]
        baseline   = baselines[i]
        dbaseline  = dbaselines[i]
        baselines_all.append(baseline); dbaselines_all.append(dbaseline)
        time_all.append(timestring)
        telstrings.append(telstring)  
    
        # Read g2 function
        chA = chAs[i]
        chB = chBs[i]
        # Do some more data cleaning, e.g. lowpass filters
        chA = cor.lowpass(chA)
        chB = cor.lowpass(chB)
    
        '''
        ### building fft of g2 to cut out noise ###
        F_fft = plt.figure(figsize=(12,7))
        ax1 = F_fft.add_subplot(121)
        stepsize = 1.6e-3                   # sampling bin size
        N = len(chA)
        chAfft = chA # für auto corr teil ohne crosstalk [5500:10000]            
        N = len(chAfft)
        xfft = np.linspace(0.0, stepsize*N, N)
        ax1.plot(xfft, chAfft, label='A') 
        x_fft = np.linspace(0.0, 1./(2.*stepsize), N//2) #N2//2)
        chA_fft = np.abs(np.fft.fft(chAfft)/(N/2)) # ct4_fft = np.abs(np.fft.fft(ct4)/(N2))
        #chA_freq, rest = find_peaks(chA_fft, threshold=[0.5e-8, 1.e-8], width=[0,5])
        #print(chA_freq)
        ax2 = F_fft.add_subplot(122)
        ax2.plot(x_fft, chA_fft[0:N//2], label='A')
        '''
        # more data cleaning with notch filter for higher frequencies
        freqA = [45,95,110,145,155,175,195]
        for j in range(len(freqA)):
            chA = cor.notch(chA, freqA[j]*1e6, 80)
        freqB = [50]
        for j in range(len(freqB)):
            chB = cor.notch(chB, freqB[j]*1e6, 80)
    
        '''
        ### Plot g2 after cleaning ####
        chAfft = chA
        ax1.plot(xfft, chAfft, label='A')
        ax1.legend()
        ax1.set_xlabel('bins of 1.6ns')
        chA_fft = np.abs(np.fft.fft(chAfft)/(N/2))
        ax2.plot(x_fft, chA_fft[0:N//2], label='A')
        ax2.set_ylim(0,8e-8)
        ax2.legend()
        ax2.set_xlabel('MHz')
        #plt.show()
        plt.close()
        '''    
        

        # Fit with fixed mu and sigma
        # chA
        xplotf, popt_A, perr_A = uti.fit_fixed(chA, x, -50, 50, mu_A[c1][c2], sigma_A[c1][c2])
        Int, dInt = uti.integral_fixed(popt_A, perr_A, sigma_A[c1][c2], factor=2.3)
        ints_fixedA.append(1e6*Int); dints_fixedA.append(1e6*dInt)# in femtoseconds
        # chB
        xplotf, popt_B, perr_B = uti.fit_fixed(chB, x, -50, 50, mu_B[c1][c2], sigma_B[c1][c2])
        Int, dInt = uti.integral_fixed(popt_B, perr_B, sigma_B[c1][c2], factor=2.38)
        ints_fixedB.append(1e6*Int); dints_fixedB.append(1e6*dInt)# in femtoseconds
        
        # Fit with mu free
        # chA
        xplotf1, popt_A1, perr_A1 = uti.fit_fixed1(chA, x, -50, 50, sigma_A[c1][c2], mu_start=mu_A[c1][c2])
        Int1, dInt1 = uti.integral_fixed(popt_A1, perr_A1, sigma_A[c1][c2], factor=2.3)
        #dInt1 = np.sqrt( dInt1**2 + (np.std(chA)*sig_A*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedA1.append(1e6*Int1); dints_fixedA1.append(1e6*dInt1)# in femtoseconds
        #print('CHIA = {}'.format(chi_A1))
        # chB
        xplotf1, popt_B1, perr_B1 = uti.fit_fixed1(chB, x, -50, 50, sigma_B[c1][c2], mu_start=mu_B[c1][c2])
        Int1, dInt1 = uti.integral_fixed(popt_B1, perr_B1, sigma_B[c1][c2], factor=2.38)
        #dInt1 = np.sqrt( dInt1**2 + (np.std(chB)*sig_B*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
        ints_fixedB1.append(1e6*Int1); dints_fixedB1.append(1e6*dInt1)# in femtoseconds
        #print('CHIB = {}'.format(chi_B1))
        
        ### Plots ###
        plt.figure(f'Integrals {telstring}')
        plt.subplot(121)
        plt.title('470nm')
        plt.errorbar(i, ints_fixedA[-1], dints_fixedA[-1], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, ints_fixedA1[-1], dints_fixedA1[-1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.title('375nm')
        plt.errorbar(i, ints_fixedB[-1], dints_fixedB[-1], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
        plt.errorbar(i, ints_fixedB1[-1], dints_fixedB1[-1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
        plt.xlabel("# time chunk") 
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())


        plt.figure('SC')
        plt.subplot(121)
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedA[-1], yerr=dints_fixedA[-1], marker='o', color='red', label='mu fixed')
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedA1[-1], yerr=dints_fixedA1[-1], marker='o', color='blue', label='mu free')
        plt.axhline(y=0, color="black", linestyle="--") 
        plt.xlabel("Projected baseline (m)")
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())
        plt.subplot(122)
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedB[-1], yerr=dints_fixedB[-1], marker='o', color='red', label='mu fixed')
        plt.errorbar(x=baseline, xerr=dbaseline, y=ints_fixedB1[-1], yerr=dints_fixedB1[-1], marker='o', color='blue', label='mu free')
        plt.axhline(y=0, color="black", linestyle="--") 
        plt.xlabel("Projected baseline (m)")
        plt.ylabel("Spatial coherence (fs)") 
        # legend 
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles)) 
        plt.legend(by_label.values(), by_label.keys())

        # errorbars for g2 fct
        errorA = []; errorB = []
        errorA.append(np.std(chA[0:4000]))
        errorB.append(np.std(chB[0:4000]))
        # only plot certain range of g2 fct -> cut data to that range
        chAss = []; chBss = []
        for k in range(0, len(x)):
            if -100<= x[k] <=100:
                chAss.append(chA[k])
                chBss.append(chB[k])       
        demo = chAss
        xnew = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)  


        b = int(np.floor(i/3))
        c = int(i%3)
        axsA[b,c].errorbar(xnew, chAss, yerr=errorA, linestyle="-", color = uti.color_chA,   alpha=0.7)
        axsA[b,c].plot(xplotf, uti.gauss_fixed(xplotf, popt_A[0], mu_A[c1][c2], sigma_A[c1][c2]), color='red', linestyle="--", zorder=4, label='mu fixed')                
        axsA[b,c].plot(xplotf1, uti.gauss_fixed(xplotf1, popt_A1[0], popt_A1[1], sigma_A[c1][c2]), color='blue', ls='--', zorder=4, label='mu free')
        #plt.ylim(np.min(chAss), np.max(chAss))
        axsA[b,c].set_xlim(-100,100)
        axsA[b,c].text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
        axsA[b,c].axhline(y=1, color='black', linestyle='--', linewidth=1)
        axsA[b,c].legend() 

        axsB[b,c].errorbar(xnew, chBss, yerr=errorB, linestyle="-", color = uti.color_chB,   alpha=0.7)
        axsB[b,c].plot(xplotf, uti.gauss_fixed(xplotf, popt_B[0], mu_B[c1][c2], sigma_B[c1][c2]), color='red', linestyle="--", zorder=4, label='mu fixed')                
        axsB[b,c].plot(xplotf1, uti.gauss_fixed(xplotf1, popt_B1[0], popt_B1[1], sigma_B[c1][c2]), color='blue', ls='--', zorder=4, label='mu free')
        axsB[b,c].set_xlim(-100,100)
        axsB[b,c].text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
        axsB[b,c].axhline(y=1, color='black', linestyle='--', linewidth=1)
        axsB[b,c].legend() 
    

            #plt.figure('singles 14 B')
            #plt.subplot(5,3,i+1)
            #plt.errorbar(xnew, chBss, yerr=errorB, linestyle="-", color = uti.color_chB,   alpha=0.7)
            #plt.plot(xplotf, uti.gauss_fixed(xplotf, popt_B[0], mu_B[c1][c2], sigma_B[c1][c2]), color='red', linestyle="--", zorder=4, label='mu fixed')                
            #plt.plot(xplotf1, uti.gauss_fixed(xplotf1, popt_B1[0], popt_B1[1], sigma_B[c1][c2]), color='blue', ls='--', zorder=4, label='mu free')
            #plt.ylim(-0.5e-6+1, popt_B[0]*1e-6+1)
            #plt.xlim(-100,100)
            #plt.text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            #plt.axhline(y=1, color='black', linestyle='--', linewidth=1)
            #plt.legend() 
            ##plt.xlabel('Time difference (ns)'); plt.ylabel('$g^{(2)}$')
            #plt.tight_layout() 

            #plt.figure('Integrals 14')
            #plt.subplot(121)
            #plt.title('470nm')
            #plt.errorbar(i, ints_fixedA[-1], dints_fixedA[-1], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
            #plt.errorbar(i, ints_fixedA1[-1], dints_fixedA1[-1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
            ## legend 
            #handles, labels = plt.gca().get_legend_handles_labels()
            #by_label = OrderedDict(zip(labels, handles)) 
            #plt.legend(by_label.values(), by_label.keys())

            #plt.subplot(122)
            #plt.title('375nm')
            #plt.errorbar(i, ints_fixedB[-1], dints_fixedB[-1], marker='o', ls='', color='red', alpha=0.7, label='mu fixed')
            #plt.errorbar(i, ints_fixedB1[-1], dints_fixedB1[-1], marker='o', ls='', color='blue', alpha=0.7, label='mu free')
            ## legend 
            #handles, labels = plt.gca().get_legend_handles_labels()
            #by_label = OrderedDict(zip(labels, handles)) 
            #plt.legend(by_label.values(), by_label.keys())
            #

    print("DONE Chunks {}".format(telcombi))

def plotting(star): 
    # Define figure which will show individual g2 cross correlations for 470nm chA
    plt.figure('singles')
    plt.title('Cross correlations of {} for 470nm'.format(star),fontweight="bold")
    plt.xlabel('Time difference (ns)')
    plt.ylabel('$g^{(2)}$')
    #crfigureA = plt.figure(figsize=(20,15))
    #crfigureA.suptitle("2Cross correlations of {} for {}".format(star, labelA),fontweight="bold")
    #crfigureA.supxlabel("Time difference (ns)", fontweight="bold", ha='center', va='center'); crfigureA.supylabel("$g^{(2)}$", fontweight="bold")
    plt.tight_layout()

    # Define figure which will show individual g2 cross correlations
    crossfigure = plt.figure('singles',figsize=(12,8))
    # cross correlations for telcombis
    ax_cross1 = crossfigure.add_subplot(211); ax_cross1.set_title("1Cross correlations of {} for {}".format(star, telcombis[0]))
    ax_cross1.set_xlabel("Time difference (ns)"); ax_cross1.set_ylabel("$g^{(2)}$"); ax_cross1.ticklabel_format(useOffset=False)
    ax_cross1.set_xlim(-100,100)
    ax_cross2 = crossfigure.add_subplot(212); ax_cross2.set_title("Cross correlations of {} for {}".format(star, telcombis[1]))
    ax_cross2.set_xlabel("Time difference (ns)"); ax_cross2.set_ylabel("$g^{(2)}$"); ax_cross2.ticklabel_format(useOffset=False)
    ax_cross2.set_xlim(-100,100)
    plt.tight_layout()

    # Define figure showing mean of g2 fcts
    meanfig = plt.figure(figsize=(10,7))
    ax_mean = plt.subplot(111)
    ax_mean.set_title('Mean of $g^{(2)}$ vs time'); ax_mean.set_xlabel('Time UTC'); ax_mean.set_ylabel('Mean')
    ax_mean.tick_params(labelrotation=45)

    # Define figure showing chi squared of g2 fcts
    chifigure =plt.figure(figsize=(10,7))
    ax_chi = plt.subplot(111)
    ax_chi.set_title('Chi squared of $g^{(2)}$ vs time'); ax_chi.set_xlabel('Time UTC'); ax_chi.set_ylabel('Chi squared')
    ax_chi.tick_params(labelrotation=45)

    # Define figure which will show the spatial coherence curve (baseline vs. g2 integral)
    scfigure = plt.figure(figsize=(12,8))
    sps1, sps2, sps3, sps4 = GridSpec(2,2)
    ax_sc1 = scfigure.add_subplot(221)
    ax_sc1.set_title("Spatial coherence of {} for 470nm".format(star))
    ax_sc1.set_xlabel("Baseline/Wavelength"); ax_sc1.set_ylabel("Coherence time (fs)")
    ax_sc1.set_xlim(-1e7,6e8)
    ax_sc3 = scfigure.add_subplot(223)
    ax_sc3.set_title("Spatial coherence of {} for 375nm".format(star))
    ax_sc3.set_xlabel("Baseline/Wavelength"); ax_sc3.set_ylabel("Coherence time (fs)")
    ax_sc3.set_xlim(-1e7,6e8)
    plt.tight_layout()

    # Define figure showing all tel combos with one fit
    combifigure = plt.figure(figsize=(10,7))
    ax_combi = plt.subplot(111)
    ax_combi.set_title("Spatial coherence of {}". format(star))
    ax_combi.set_xlabel("Baseline/Wavelength"); ax_combi.set_ylabel("Coherence time (fs)") 
    ax_combi.set_xlim(-1e7,5e8)
    
    # for loop over telescope combinations
    for i in range(len(telcombis)):
        # read in all necessary data and parameters
        chAs_clean = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChA_clean.txt".format(star,telcombis[i]))
        chBs_clean = np.loadtxt("g2_functions/weight_rms_squared/{}/{}/ChB_clean.txt".format(star,telcombis[i]))
        mu_A, sigA, mu_B, sigB = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_{}.txt".format(star,telcombis[i]))
        muA  = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,0]
        dmuA  = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,1]
        ampA = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,2]
        muB  = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,3]
        dmuB  = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,4]        
        ampB = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,5]
        timestrings = np.loadtxt("g2_functions/fixed_parameters/{}/mu_sig_individual_{}.txt".format(star,telcombis[i]))[:,6]
        xplotf = np.loadtxt("g2_functions/fixed_parameters/{}/xplot.txt".format(star))
        chiA = np.loadtxt("g2_functions/fixed_parameters/{}/chi_squared_{}.txt".format(star, telcombis[i]))[:,0]
        chiB = np.loadtxt("g2_functions/fixed_parameters/{}/chi_squared_{}.txt".format(star, telcombis[i]))[:,1]
        baselines     = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,0]
        dbaselines    = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,1]
        ints_fixedA   = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,2]
        dints_fixedA  = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,3]
        ints_fixedB   = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,4]
        dints_fixedB  = np.loadtxt("spatial_coherence/{}/{}_{}_data.sc".format(star,star,telcombis[i])) [:,5]
        ints_fixedA1  = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,2]
        dints_fixedA1 = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,3]
        ints_fixedB1  = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,4]
        dints_fixedB1 = np.loadtxt("spatial_coherence/{}/{}_{}_data_fixed.sc".format(star,star,telcombis[i])) [:,5]

        # add data of all tel combis to one list
        ints_fixed_all.append(ints_fixedA); ints_fixed_all.append(ints_fixedB); dints_fixed_all.append(dints_fixedA); dints_fixed_all.append(dints_fixedB)
        baselines_all.append(baselines); baselines_all.append(baselines); dbaselines_all.append(dbaselines); dbaselines_all.append(dbaselines)


        #--------------------#
        # Try fitting with ods
        # Model object
        from scipy import odr
        
        sc_modelG = odr.Model(uti.spatial_coherence_odrG)
        # RealData object
        rdataG = odr.RealData( baselines, ints_fixedA, sx=dbaselines, sy=dints_fixedA )
        # Set up ODR with model and data
        odrODRG = odr.ODR(rdataG, sc_modelG, beta0=[25,2.2e-9])
        # Run the regression
        outG = odrODRG.run()
        # Fit parameters
        popt_odrA = outG.beta
        perr_odrA = outG.sd_beta
        chi_odrA = outG.res_var # chi squared value
        
        
        sc_modelUV = odr.Model(uti.spatial_coherence_odrUV)
        # RealData object
        rdataUV = odr.RealData( baselines, ints_fixedB, sx=dbaselines, sy=dints_fixedB )
        # Set up ODR with model and data
        odrODRUV = odr.ODR(rdataUV, sc_modelUV, beta0=[20,3.2e-9])
        # Run the regression
        outUV = odrODRUV.run()
        # Fit parameters
        popt_odrB = outUV.beta
        perr_odrB = outUV.sd_beta
        chi_odrB = outUV.res_var # chi squared value
        #--------------------#

        print("SC fits")
        print("{}A 470nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(telcombis[i], uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1]), popt_odrA[0], perr_odrA[0], chi_odrA))
        print("{}B 375nm: Angular diameter: {:.2f} +/- {:.2f} (mas)\t Amplitude: {:.2f} +/- {:.2f}\t Chi^2 reduced: {:.2f}".format(telcombis[i], uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1]), popt_odrB[0], perr_odrB[0], chi_odrB))

        # save fitted amplitude
        amplitudes_odr.append(popt_odrA[0]); amplitudes_odr.append(perr_odrA[0])
        amplitudes_odr.append(popt_odrB[0]); amplitudes_odr.append(perr_odrB[0])
        ang_odr.append(popt_odrA[1]); ang_odr.append(perr_odrA[1])
        ang_odr.append(popt_odrB[1]); ang_odr.append(perr_odrB[1])

        
        # Define colormap for plotting all summarized individual g2 functions (not needed)
        cm_sub = np.linspace(1.0, 0.0, len(chAs_clean))
        colors = [cm.viridis(x) for x in cm_sub]
        # Demo function for initializing x axis and some stuff
        demo = chAs_clean[0]
        x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)
        
        lam_g = 470e-9
        lam_uv = 375e-9
        lam_all = 422.5e-9
        # make x-axis wavelength indepedent 
        xplot = np.arange(0.1,300,0.1)
        xplot_g = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_g[j] = xplot[j] / lam_g
        xplot_uv = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_uv[j] = xplot[j] /lam_uv
        xplot_all = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_all[j] = xplot[j] /lam_all
        # add HBT measurement to the plot
        xplot_HBT = np.zeros(len(xplot))
        for j in range(0,len(xplot)):
            xplot_HBT[j] = (xplot[j] /float(lam_HBT))

        # Nullstelle for SC plot
        nsA = 1.22*(lam_g/popt_odrA[1])
        nsB = 1.22*(lam_uv/popt_odrB[1])

        # Make plotting range smaller 
        chAs = []; chBs = []; errorA =[]; errorB = []
        for j in range(0,len(chAs_clean)):
            chA = chAs_clean[j] ; chB = chBs_clean[j]; chAss = []; chBss = []
            # errorbars for g2 fct
            errorA.append(np.std(chAs_clean[j][0:4000]))
            errorB.append(np.std(chBs_clean[j][0:4000]))
            # only plot certain range of g2 fct -> cut data to that range
            for k in range(0, len(x)):
                if -100<= x[k] <=100:
                    chAss.append(chA[k])
                    chBss.append(chB[k])        
            chAs.append(np.array(chAss))
            chBs.append(np.array(chBss))  
        demo = chAs[0]
        xnew = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)     

        # Subplot for all cross correlations for telcombi 14
        if telcombis[i] == 14:
            labelA = '{}A 470nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrA)
            labelB = '{}B 375nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrB) 
            # Define figure which will show individual g2 cross correlations for channel A
            crfigureA = plt.figure(figsize=(20,15))
            crfigureA.suptitle("2Cross correlations of {} for {}".format(star, labelA),fontweight="bold")
            crfigureA.supxlabel("Time difference (ns)", fontweight="bold", ha='center', va='center'); crfigureA.supylabel("$g^{(2)}$", fontweight="bold")
            plt.tight_layout()
            # for loop over all chunks to show individual g2 fcts
            for n, A in enumerate(chAs):
                timestring = ephem.Date(timestrings[n])
                tstring_short = str(timestring)[5:-3]
                ax_crA = plt.subplot(5,3,n+1)
                ax_crA.errorbar(xnew, chAs[n], yerr=errorA[n], linestyle="-", color = colorA14,   alpha=0.7)
                ax_crA.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampA[n], mu=muA[n], sigma=sigA), color='red', linestyle="--", zorder=4, label='fit mu free')
                ax_crA.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampA[n], mu=mu_A, sigma=sigA), color='blue', linestyle="--", zorder=4, label='fit mu fixed')                
                ax_crA.set_ylim(-0.5e-6+1, 1.5e-6+1)
                ax_crA.text(x=-100, y=1.2e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                ax_crA.axhline(y=1, color='black', linestyle='--', linewidth=1)
                ax_crA.legend()
            plt.savefig('images/{}/g2_singles_{}.pdf'.format(star,labelA[0:9]))
            
            # Define figure which will show individual g2 cross correlations for channel B
            crfigureB = plt.figure(figsize=(20,15))
            crfigureB.suptitle("Cross correlations of {} for {}".format(star, labelB),fontweight="bold")
            crfigureB.supxlabel("Time difference (ns)", fontweight="bold"); crfigureB.supylabel("$g^{(2)}$", fontweight="bold")
            plt.tight_layout()
            # for loop over all chunks to show individual g2 fcts
            for n, A in enumerate(chBs): 
                timestring = ephem.Date(timestrings[n])
                tstring_short = str(timestring)[5:-3]   
                ax_crB = plt.subplot(5,3,n+1)
                ax_crB.errorbar(xnew, chBs[n], yerr=errorB[n], linestyle="-", color = colorB14,   alpha=0.7)
                ax_crB.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampB[n], mu=muB[n], sigma=sigB), color='red', linestyle="--", zorder=4, label='fit mu free')
                ax_crB.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampB[n], mu=mu_A, sigma=sigA), color='green', linestyle="--", zorder=4, label='fit mu fixed')                
                ax_crB.set_ylim(-0.75e-6+1, 1.0e-6+1)
                ax_crB.text(x=-100, y=0.5e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                ax_crB.axhline(y=1, color='black', linestyle='--', linewidth=1)
                ax_crB.legend()
            plt.savefig('images/{}/g2_singles_{}.pdf'.format(star,labelB[0:9]))
            
            # for loop over all chunks 
            for j in range(len(chAs)):
                # plot all g2 fcts together
                the_shift = (len(chAs)-j-1)*1e-6
                ticks.append(1.+the_shift)
                timestring = ephem.Date(timestrings[j])
                tstring_short = str(timestring)[5:-3]
                ax_cross1.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
                ax_cross1.errorbar(xnew, chAs[j] + the_shift, yerr=errorA[j], linestyle="-", color = colorA14,   alpha=0.7)
                ax_cross1.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampA[j], mu=muA[j], sigma=sigA, shift=j, inverse=True, ntotal=len(chAs)), color=colorA14, linestyle="--", zorder=4)
                ax_cross1.errorbar(xnew, chBs[j] + the_shift, yerr=errorB[j], linestyle="-", color =colorB14,   alpha=0.7)                
                ax_cross1.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampB[j], mu=muB[j], sigma=sigB, shift=j, inverse=True, ntotal=len(chBs)), color=colorB14, linestyle="--", zorder=4)
                ax_cross1.text(x=70, y=1+the_shift+0.4e-6, s=tstring_short, color=colors[j], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                # plot mean of gauss fit of g2 fcts and reduced chi squared
                ax_mean.errorbar(tstring_short, muA[j], yerr=dmuA[j], color=colorA14, marker='o', label=labelA)
                ax_mean.errorbar(tstring_short, muB[j], yerr=dmuB[j], color=colorB14, marker='o', label=labelB)
                p5, = ax_chi.plot(tstring_short, chiA[j], color=colorA14, marker='o', label=labelA)
                p6, = ax_chi.plot(tstring_short, chiB[j], color=colorB14, marker='o', label=labelB)
                # add vertical line for new measurement day
                if j==6:
                    ax_mean.axvline(tstring_short, color='black')
                    ax_chi.axvline(tstring_short, color='black')
            ### Plot SC data ###
            for k in range (0,len(baselines)):
                ax_sc1.errorbar(baselines[k]/lam_g, ints_fixedA[k],  yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA14)
                ax_sc3.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14)
                ax_sc2.errorbar(baselines[k], ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorA14)
                ax_sc4.errorbar(baselines[k], ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorB14)
                # all SC curves in one plot
                ax_combi.errorbar(baselines[k]/lam_g, ints_fixedA[k],  yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g,  marker="o", linestyle="", color=colorA14, label=labelA)
                ax_combi.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB14, label=labelB)
            # plot SC fit and error band
            ax_sc1.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA14, linewidth=2)
            ax_sc1.fill_between(xplot_g, uti.spatial_coherence(xplot,popt_odrA[0]+perr_odrA[0],popt_odrA[1]-perr_odrA[1], lam_g), uti.spatial_coherence(xplot,popt_odrA[0]-perr_odrA[0],popt_odrA[1]+perr_odrA[1], lam_g), color=colorA14, alpha=0.3)
            ax_sc3.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB14, linewidth=2)
            ax_sc3.fill_between(xplot_uv, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), color=colorB14, alpha=0.2)
            ax_combi.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA14, linewidth=2)
            ax_combi.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB14, linewidth=2)
            # plot scaled version of SC fit
            ax_sc2.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrA[1]), lam_g), label=labelA[0:9], color=colorA14, linewidth=2)
            ax_sc4.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrB[1]), lam_uv),label=labelB[0:9], color=colorB14,  linewidth=2)
            # add zero baseline data point with error bar
            ax_sc1.errorbar(xplot_g[0],  uti.spatial_coherence(xplot[0],*popt_odrA, lam_g),  yerr=perr_odrA[0], marker='x', color=colorA14 )
            ax_sc3.errorbar(xplot_uv[0], uti.spatial_coherence(xplot[0],*popt_odrB, lam_uv), yerr=perr_odrB[0], marker='x', color=colorB14 )
            # add vertical lines for Nullstellen and text to plots
            ax_sc1.axvline(x=nsA/lam_g, color=colorA14, ymax=0.3); ax_sc3.axvline(x=nsB/lam_uv, color=colorB14, ymax=0.4)
            ax_sc1.text(x=xplot_g[1000], y=20, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])), color=colorA14)
            ax_sc1.text(x=xplot_g[1000], y=18, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrA[0], perr_odrA[0]), color=colorA14)
            ax_sc3.text(x=xplot_uv[800], y=20, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])), color=colorB14, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            ax_sc3.text(x=xplot_uv[800], y=18, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrB[0], perr_odrB[0]), color=colorB14, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            
        # Subplot for all cross correlations for telcombi 34
        elif telcombis[i] == 34:
            labelA = '{}A 470nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrA)
            labelB = '{}B 375nm, $\chi^2$/dof={:.2f}'.format(telcombis[i], chi_odrB)
            # Define figure which will show individual g2 cross correlations for channel A
            crfigureA2 = plt.figure(figsize=(20,15))
            crfigureA2.suptitle("Cross correlations of {} for {}".format(star, labelA),fontweight="bold")
            crfigureA2.supxlabel("Time difference (ns)", fontweight="bold"); crfigureA2.supylabel("$g^{(2)}$", fontweight="bold")
            plt.tight_layout()
            # for loop over all chunks to show individual g2 fcts
            for n, A in enumerate(chAs):
                timestring = ephem.Date(timestrings[n])
                tstring_short = str(timestring)[5:-3]
                ax_crA2 = plt.subplot(5,3,n+1)
                ax_crA2.errorbar(xnew, chAs[n], yerr=errorA[n], linestyle="-", color = colorA34,   alpha=0.7)
                ax_crA2.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampA[n], mu=muA[n], sigma=sigA), color='red', linestyle="--", zorder=4, label='fit mu free')
                ax_crA2.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampA[n], mu=mu_A, sigma=sigA), color='green', linestyle="--", zorder=4, label='fit mu fixed')                
                ax_crA2.set_ylim(-0.5e-6+1, 1.0e-6+1)
                ax_crA2.text(x=-100, y=0.75e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                ax_crA2.axhline(y=1, color='black', linestyle='--', linewidth=1)
                ax_crA2.legend()
            plt.savefig('images/{}/g2_singles_{}.pdf'.format(star,labelA[0:0]))

            # Define figure which will show individual g2 cross correlations for channel B
            crfigureB2 = plt.figure(figsize=(20,15))
            crfigureB2.suptitle("Cross correlations of {} for {}".format(star, labelB),fontweight="bold")
            crfigureB2.supxlabel("Time difference (ns)", fontweight="bold"); crfigureB2.supylabel("$g^{(2)}$", fontweight="bold")
            plt.tight_layout()
            # for loop over all chunks to show individual g2 fcts
            for n, A in enumerate(chBs):
                timestring = ephem.Date(timestrings[n])
                tstring_short = str(timestring)[5:-3]    
                ax_crB2 = plt.subplot(5,3,n+1)
                ax_crB2.errorbar(xnew, chBs[n], yerr=errorB[n], linestyle="-", color = colorB34,   alpha=0.7)
                ax_crB2.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampB[n], mu=muB[n], sigma=sigB), color='red', linestyle="--", zorder=4, label='fit mu free')
                ax_crB2.plot(xplotf, uti.gauss_fixed(x=xplotf,  a=ampB[n], mu=mu_B, sigma=sigB), color='blue', linestyle="--", zorder=4, label='fit mu fixed')
                ax_crB2.set_ylim(-0.25e-6+1, 0.25e-6+1)
                ax_crB2.text(x=-100, y=0.15e-6+1, s=tstring_short, fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                ax_crB2.axhline(y=1, color='black', linestyle='--', linewidth=1)
                ax_crB2.legend(loc='upper right')
            plt.savefig('images/{}/g2_singles_{}.pdf'.format(star,labelB[0:9]))
            
            # for loop over all chunks
            for j in range(len(chAs)):
                # plot all g2 fcts together
                the_shift = (len(chAs)-j-1)*1e-6
                ticks.append(1.+the_shift)
                timestring = ephem.Date(timestrings[j])
                tstring_short = str(timestring)[5:-3]
                ax_cross2.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
                ax_cross2.errorbar(xnew, chAs[j] + the_shift, yerr=errorA[j], linestyle="-", color = colorA34,   alpha=0.7)
                ax_cross2.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampA[j], mu=muA[j], sigma=sigA, shift=j, inverse=True, ntotal=len(chAs)), color=colorA34, linestyle="--", zorder=4)
                ax_cross2.errorbar(xnew, chBs[j] + the_shift, yerr=errorB[j], linestyle="-", color = colorB34,   alpha=0.7)
                ax_cross2.plot(xplotf, uti.gauss_shifted(x=xplotf,  a=ampB[j], mu=muB[j], sigma=sigB, shift=j, inverse=True, ntotal=len(chBs)), color=colorB34, linestyle="--", zorder=4)
                ax_cross2.text(x=70, y=1+the_shift+0.4e-6, s=tstring_short, color=colors[j], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
                # plot mean of gauss fit of g2 fcts and reduced chi squared
                ax_mean.errorbar(tstring_short, muA[j], yerr=muA[j], color=colorA34, marker='x', label=labelA)
                ax_mean.errorbar(tstring_short, muB[j], yerr=muB[j], color=colorB34, marker='x', label=labelB)
                p7, = ax_chi.plot(tstring_short, chiA[j], color=colorA34, marker='x', label=labelA)
                p8, = ax_chi.plot(tstring_short, chiB[j], color=colorB34, marker='x', label=labelB)
                # add vertical line for new measurement day
                if j==0 or j==4 or j==15 or j==12:
                    ax_mean.axvline(tstring_short, color='black')
                    ax_chi.axvline(tstring_short, color='black')
            ### Plot SC data ###
            for k in range (0,len(baselines)):
                ax_sc1.errorbar(baselines[k]/lam_g,  ints_fixedA[k], yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g, marker="o", linestyle="", color=colorA34)
                ax_sc3.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB34)
                ax_sc2.errorbar(baselines[k], ints_fixedA_scaled[k], yerr=dints_fixedA_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorA34)
                ax_sc4.errorbar(baselines[k], ints_fixedB_scaled[k], yerr=dints_fixedB_scaled[k], xerr=dbaselines[k], marker="o", linestyle="", color=colorB34)
                # all SC curves in one plot
                ax_combi.errorbar(baselines[k]/lam_g,  ints_fixedA[k], yerr=dints_fixedA[k], xerr=dbaselines[k]/lam_g,  marker="o", linestyle="", color=colorA34, label=labelA)
                ax_combi.errorbar(baselines[k]/lam_uv, ints_fixedB[k], yerr=dints_fixedB[k], xerr=dbaselines[k]/lam_uv, marker="o", linestyle="", color=colorB34, label=labelB)
            # plot SC fit and error band
            ax_sc1.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA34, linewidth=2)
            ax_sc1.fill_between(xplot_g, uti.spatial_coherence(xplot,popt_odrA[0]+perr_odrA[0],popt_odrA[1]-perr_odrA[1], lam_g), uti.spatial_coherence(xplot,popt_odrA[0]-perr_odrA[0],popt_odrA[1]+perr_odrA[1], lam_g), color=colorA34, alpha=0.3)
            ax_sc3.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB34, linewidth=2)  
            ax_sc3.fill_between(xplot_uv, uti.spatial_coherence(xplot,popt_odrB[0]+perr_odrB[0],popt_odrB[1]-perr_odrB[1], lam_uv), uti.spatial_coherence(xplot,popt_odrB[0]-perr_odrB[0],popt_odrB[1]+perr_odrB[1], lam_uv), color=colorB34, alpha=0.2)
            ax_combi.plot(xplot_g, uti.spatial_coherence(xplot,*popt_odrA, lam_g), label=labelA, color=colorA34, linewidth=2)
            ax_combi.plot(xplot_uv, uti.spatial_coherence(xplot,*popt_odrB, lam_uv), label=labelB, color=colorB34, linewidth=2)   
            # plot scaled version of SC fit
            ax_sc2.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrA[1]), lam_g), label=labelA[0:9], color=colorA34, linewidth=2)
            ax_sc4.plot(xplot, uti.spatial_coherence(xplot,1, float(popt_odrB[1]), lam_uv),label=labelB[0:9], color=colorB34,  linewidth=2)
            # add zero baseline data point with error bar
            ax_sc1.errorbar(xplot_g[0],  uti.spatial_coherence(xplot[0],*popt_odrA, lam_g),  yerr=perr_odrA[0], marker='x', color=colorA34 )
            ax_sc3.errorbar(xplot_uv[0], uti.spatial_coherence(xplot[0],*popt_odrB, lam_uv), yerr=perr_odrB[0], marker='x', color=colorB34 )
            # add vertical lines for Nullstellen and text to plots
            ax_sc1.axvline(x=nsA/lam_g, color=colorA34,ymax=0.4); ax_sc3.axvline(x=nsB/lam_uv, color=colorB34, ymax=0.4)
            ax_sc1.text(x=xplot_g[1000], y=16, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrA[1]), uti.rad2mas(perr_odrA[1])), color=colorA34)
            ax_sc1.text(x=xplot_g[1000], y=14, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrA[0], perr_odrA[0]), color=colorA34)
            ax_sc3.text(x=xplot_uv[800], y=16, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odrB[1]), uti.rad2mas(perr_odrB[1])), color=colorB34, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
            ax_sc3.text(x=xplot_uv[800], y=14, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odrB[0], perr_odrB[0]), color=colorB34, bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
    
    # add HBT curve and making plot pretty        
    ax_sc2.plot(xplot, uti.spatial_coherence(xplot,1, ang_HBT, float(lam_HBT)), label="HBT {}nm".format(lam_HBT[0:3]), color="red", linewidth=2)
    ax_sc1.axhline(y=0.0, color='black', linestyle='--'); ax_sc2.axhline(y=0.0, color='black', linestyle='--'); ax_sc3.axhline(y=0.0, color='black', linestyle='--'); ax_sc4.axhline(y=0.0, color='black', linestyle='--')
    ax_sc1.legend() ; ax_sc2.legend(); ax_sc3.legend(); ax_sc4.legend()
    #plt.tight_layout()
    ax_mean.axhline(0.0, color='black', linestyle='--')
    h1,l1 = plt.gca().get_legend_handles_labels()
    labelall_mean = dict(zip(l1,h1))
    ax_mean.legend(labelall_mean.values(), labelall_mean.keys())
    ax_chi.legend(handles=[p5,p6,p7,p8])
    ax_chi.axhline(0.0, color='black', linestyle='--')

    print(amplitudes_odr)
    np.savetxt('spatial_coherence/{}/amplitudes_odr.sc'.format(star), np.c_[amplitudes_odr], header='14: ampA, dampA, ampB, dampB/n 34: ampA, dampA, ampB, dampB')
    np.savetxt('spatial_coherence/{}/angular_dia_odr.sc'.format(star), np.c_[ang_odr], header='14: angA, dangA, angB, dangB/n 34: angA, dangA, angB, dangB')

    '''
    #--------------------#
    # Try fitting with ods
    # Model object
    from scipy import odr
    
    sc_model = odr.Model(uti.spatial_coherence_odr)
    # RealData object
    rdata = odr.RealData( baselines_all, ints_fixed_all, sx=dbaselines_all, sy=dints_fixed_all )
    # Set up ODR with model and data
    odrODR = odr.ODR(rdata, sc_model, beta0=[22,2.7e-9])
    # Run the regression
    out = odrODR.run()
    # Fit parameters
    popt_odr_all = out.beta
    perr_odr_all = out.sd_beta

    print("SC fit all")
    print("Angular diameter AVG (odr): {:.3f} +/- {:.3f} (mas)".format(uti.rad2mas(popt_odr_all[1]), uti.rad2mas(perr_odr_all[1])))
    print("Amplitude: {:.3f} +/- {:.3f}".format(popt_odr_all[0], perr_odr_all[0]))
    '''
    #ax_combi.plot(xplot_all, uti.spatial_coherence(xplot,*popt_odr_all, lam_all), color='orange', linewidth=2)
    #ax_combi.errorbar(xplot_all[0], uti.spatial_coherence(xplot[0],*popt_odr_all, lam_all), yerr=perr_odr_all[0], marker='x', color='orange' )
    #ax_combi.fill_between(xplot_all, uti.spatial_coherence(xplot,popt_odr_all[0]+perr_odr_all[0],popt_odr_all[1]-perr_odr_all[1], lam_all), uti.spatial_coherence(xplot,popt_odr_all[0]-perr_odr_all[0],popt_odr_all[1]+perr_odr_all[1], lam_all), color='orange', alpha=0.2)
    ax_combi.axhline(0.0, color='black', linestyle='--')
    ax_combi.text(x=xplot_all[1800], y=25, s='14A 470nm', color=colorA14); ax_combi.text(x=xplot_all[1800], y=24, s='34A 470nm', color=colorA34)
    ax_combi.text(x=xplot_all[1800], y=23, s='14B 375nm', color=colorB14); ax_combi.text(x=xplot_all[1800], y=22, s='34B 375nm', color=colorB34)    
    #ax_combi.text(x=xplot_all[1000], y=20, s='Angular diameter: {:.3f} +/- {:.3f} (mas)'.format(uti.rad2mas(popt_odr_all[1]), uti.rad2mas(perr_odr_all[1])), color='orange')
    #ax_combi.text(x=xplot_all[1000], y=19, s='Amplitude: {:.3f} +/- {:.3f}'.format(popt_odr_all[0], perr_odr_all[0]), color='orange')
    


# Loop over every potential telescope combination and check if it exists
telcombis = []
for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombis.append("{}{}".format(c1,c2))

for c1 in range (1,5):
    for c2 in range(1,5):
        if os.path.isfile("g2_functions/{}/{}{}/ac_times.txt".format(star,c1,c2,)):
            telcombi = [c1,c2]
            telcombistring = str(c1) + str(c2)
            print ("Found telescope combination {}".format(telcombi))
            if telcombistring in onlys or onlys == "None":
                par_fixing(star, telcombi)
                chunk_ana(star, telcombi, ratioA, ratioB)
#plotting(star)


plt.show()     
