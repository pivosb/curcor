import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  
from scipy.optimize import curve_fit
from scipy.signal import butter, filtfilt, find_peaks
from matplotlib.pyplot import cm
import ephem
import scipy.special as scp
import sys
from brokenaxes import brokenaxes
from matplotlib.gridspec import GridSpec

import utilities as uti
import corrections as cor
import geometry as geo

star = sys.argv[1]

# Add error on the zero baseline from fluctuations in Acrux autocorrelation data
zero_baseline_systematic = True
zero_baseline_fluctuations = np.loadtxt("oscillations.txt")

# Get the timebin shift of the specific measurement from the time difference
def timebin(tdiff):
    return int(1.0* np.floor((tdiff+0.8)/1.6))
def shift_bins(data, binshift):
    # A negative number means shifting to the right, so scrapping the right end of the array to the beginning
    if binshift <= 0:
        for j in range (binshift,0):
            data = np.insert(data,0,data[-1])
            data = np.delete(data, -1)
    # A positive number means shifting to the left, so scrapping the beginning of the array to the end
    if binshift > 0:
        for j in range (0, binshift):
            data = np.append(data,data[0])
            data = np.delete(data, 0)
    return data

# Average over all 4 functions
def average_g2s(cA, cB, c3Ax4B, c4Ax3B):
    g2_avg = np.zeros( len(cA) )
    g2_avg += cA/np.std(cA[0:4500])**2
    g2_avg += cB/np.std(cB[0:4500])**2
    g2_avg += c3Ax4B/np.std(c3Ax4B[0:4500])**2
    g2_avg += c4Ax3B/np.std(c4Ax3B[0:4500])**2

    g2_avg = g2_avg/np.mean(g2_avg[0:4500])

    return g2_avg

print("Final Analysis of {}".format(star))
################################################
#### Analysis over whole measurement time #####
################################################
# Read in the data (g2 functions and time/baseline parameters)
chAs    = np.loadtxt("g2_functions/weight_rms_squared/{}/ChA.txt".format(star))     
chBs    = np.loadtxt("g2_functions/weight_rms_squared/{}/ChB.txt".format(star))     
ct3s    = np.loadtxt("g2_functions/weight_rms_squared/{}/CT3.txt".format(star))     
ct4s    = np.loadtxt("g2_functions/weight_rms_squared/{}/CT4.txt".format(star))     
c3Ax4Bs = np.loadtxt("g2_functions/weight_rms_squared/{}/c3Ax4B.txt".format(star))  
c4Ax3Bs = np.loadtxt("g2_functions/weight_rms_squared/{}/c4Ax3B.txt".format(star))  
data    = np.loadtxt("g2_functions/weight_rms_squared/{}/baseline.txt".format(star))

# Demo function for initializing x axis and some stuff
demo = chAs[0]
x = np.arange(-1.6*len(demo)//2,+1.6*len(demo)//2,1.6)

# Combine all data for channel A and B each for initial parameter estimation and fixing
plt.figure(figsize=(6,7))
plt.subplot(211)
plt.title("Cumulative cross correlation data of {}".format(star))

g2_allA = np.zeros(len(x)); g2_allB = np.zeros(len(x))
g2_all3Ax4B = np.zeros(len(x)); g2_all4Ax3B = np.zeros(len(x))
for i in range (0,len(chAs)):
    g2_allA += chAs[i]/len(chAs)
    g2_allB += chBs[i]/len(chBs)
    g2_all3Ax4B += c3Ax4Bs[i]/len(c3Ax4Bs)
    g2_all4Ax3B += c4Ax3Bs[i]/len(c4Ax3Bs)

# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(g2_allA, x, -50, +50)
muA = popt[1]; sigmaA = popt[2]
integral, dintegral = uti.integral(popt, perr)
print ("3A x 4A sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
plt.plot(x, g2_allA, label="3A x 4A", color=uti.color_chA)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_allB, x, -50, +50)
muB = popt[1]; sigmaB = popt[2]
integral, dintegral = uti.integral(popt, perr)
print ("3B x 4B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
plt.plot(x, g2_allB, label="3B x 4B", color=uti.color_chB)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_all3Ax4B, x, 90, 140, mu_start=115)
mu3Ax4B = popt[1]; sigma3Ax4B = popt[2]
integral, dintegral = uti.integral(popt, perr)
print ("3A x 4B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
plt.plot(x, g2_all3Ax4B, label="3A x 4B", color=uti.color_c3A4B)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

xplot, popt, perr = uti.fit(g2_all4Ax3B, x, 65, 165, mu_start=115)
mu4Ax3B = popt[1]; sigma4Ax3B = popt[2]
integral, dintegral = uti.integral(popt, perr)
print ("4A x 3B sigma/integral: {:.2f} +/- {:.2f} ns \t {:.2f} +/- {:.2f} fs".format(popt[2],perr[2],1e6*integral,1e6*dintegral))
plt.plot(x, g2_all4Ax3B, label="4A x 3B", color=uti.color_c4A3B)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--")

plt.legend(); plt.xlim(-100,200); plt.grid()#; plt.tight_layout()
#plt.ticklabel_format(useOffset=False)
plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")

plt.tight_layout()
#########################
# Shift all peaks to zero
#########################
plt.subplot(212); plt.title("Cable-delay corrected cross correlations")

tbin = timebin(muA); g2_allA = shift_bins(g2_allA, tbin)
tbin = timebin(muB); g2_allB = shift_bins(g2_allB, tbin)
tbin = timebin(mu3Ax4B); g2_all3Ax4B = shift_bins(g2_all3Ax4B, tbin)
tbin = timebin(mu4Ax3B); g2_all4Ax3B = shift_bins(g2_all4Ax3B, tbin)

g2_avg = average_g2s(g2_allA, g2_allB, g2_all3Ax4B, g2_all4Ax3B)

# Fit for gaining mu and sigma to fix these parameters
xplot, popt, perr = uti.fit(g2_avg, x, -100, +100)
mu_avg = popt[1]; sigma_avg = popt[2]
print ("Resolution: {:.2f} +/- {:.2f}  (ns)".format(sigma_avg,perr[2]))


plt.plot(x, g2_allA,     label="3A x 4A", zorder=1, color=uti.color_chA)
plt.plot(x, g2_allB,     label="3B x 4B", zorder=1, color=uti.color_chB)
plt.plot(x, g2_all3Ax4B, label="3A x 4B", zorder=1, color=uti.color_c3A4B)
plt.plot(x, g2_all4Ax3B, label="4A x 3B", zorder=1, color=uti.color_c4A3B)

plt.plot(x, g2_avg, color="grey", linewidth="4", label="Average", zorder=2, alpha=0.7)
plt.plot(xplot, uti.gauss(xplot,*popt), color="black", linestyle="--", label="Gaussian fit")

plt.legend(); plt.xlim(-100,100); plt.grid()#; plt.tight_layout()
#plt.ticklabel_format(useOffset=False)
plt.xlabel("Time delay (ns)"); plt.ylabel("$g^{(2)}$")

plt.tight_layout()
plt.savefig("images/{}_cumulative.pdf".format(star))
plt.plot()


#########################################
###### Chunk analysis ###################
#########################################
# Define colormap for plotting all summarized individual g2 functions
cm_sub = np.linspace(1.0, 0.0, len(chAs))
colors = [cm.viridis(x) for x in cm_sub]

# Define total figure which will show individual g2 cross correlations and averaged auto correlation
# and also the spatial coherence curve (baseline vs. g2 integral)
bigfigure = plt.figure(figsize=(12,7))
grid = GridSpec (10, 2, left=0.1, bottom=0.15, right=0.94, top=0.94, wspace=0.1, hspace=0.3)


# cross correlations
ax_cross = bigfigure.add_subplot(121); ax_cross.set_title("Cross correlations of {}".format(star))
ax_cross.set_xlabel("Time difference (ns)"); ax_cross.set_ylabel("$g^{(2)}$"); ax_cross.ticklabel_format(useOffset=False)
ax_cross.set_xlim(-150,150); ax_cross.set_yticks(np.arange(1,1+2e-6*len(chAs),2e-6))
# spatial coherence
sps1, sps2, sps3, sps4 = GridSpec(2,2)
if star == "Acrux":# broken x axis for better representation later
    ax_sc = brokenaxes(xlims=((0, 10), (73, 120)), subplot_spec=sps2, wspace=0.05, despine=False)
else:
    ax_sc = bigfigure.add_subplot(222)
#ax_sc.set_title("Spatial coherence of {}".format(star))
ax_sc.set_xlabel("Baseline (m)"); ax_sc.set_ylabel("Coherence time (fs)")
# auto correlation
ax_auto  = bigfigure.add_subplot(224); ax_auto.set_title("Auto correlation of {}".format(star))
ax_auto.set_xlabel("Time difference (ns)"); ax_auto.set_ylabel("$g^{(2)}$"); ax_auto.ticklabel_format(useOffset=False)
ax_auto.set_xlim(-100,100)


intsA = []; dintsA = []; times = []
intsB = []; dintsB = []
ints3Ax4B = []; dints3Ax4B = []
ints4Ax3B = []; dints4Ax3B = []

ints_fixed = []; dints_fixed = []

# initialize CT3 and CT4 sum arrays and cleaned arrays
chA_clean = []
chB_clean = []
ct3_clean = []
ct4_clean = []
c3Ax4B_clean = []
c4Ax3B_clean = []
ct3_sum = np.zeros(len(ct3s[0]))
ct4_sum = np.zeros(len(ct4s[0]))
ticks = []
ffts = []

# loop over every g2 function chunks
for i in range(0,len(chAs)):
    chA = chAs[i]
    chB = chBs[i]
    ct3 = ct3s[i]
    ct4 = ct4s[i]
    c3Ax4B = c3Ax4Bs[i]
    c4Ax3B = c4Ax3Bs[i]

    # Do some more data cleaning, e.g. lowpass filters
    chA = cor.lowpass(chA)
    chB = cor.lowpass(chB)
    ct3 = cor.lowpass(ct3)
    ct4 = cor.lowpass(ct4)
    c3Ax4B = cor.lowpass(c3Ax4B)
    c4Ax3B = cor.lowpass(c4Ax3B)
    '''
    F_fft = plt.figure(figsize=(12,7))
    ax1 = F_fft.add_subplot(121)
    ax1.plot(x, chA); ax1.plot(x, chB); ax1.plot(x, ct3); ax1.plot(x, ct4)
    N = len(chA)
    stepsize = 1.6
    x = np.linspace(0.0, stepsize*N, N)
    x_fft = np.linspace(0.0, 1./(2.*stepsize), N//2)
    chA_fft = np.abs(np.fft.fft(chA)/(N/2)); chB_fft = np.abs(np.fft.fft(chB)/(N/2)); ct3_fft = np.abs(np.fft.fft(ct3)/(N/2)); ct4_fft = np.abs(np.fft.fft(ct4)/(N/2))
    ax2 = F_fft.add_subplot(122)
    ax2.plot(x_fft, chA_fft[0:N//2]); ax2.plot(x_fft, chB_fft[0:N//2]); ax2.plot(x_fft, ct3_fft[0:N//2]); ax2.plot(x_fft, ct4_fft[0:N//2])
    ax2.set_ylim(0,8e-8)
    plt.show()
    '''

    # more data cleaning with notch filter for higher frequencies
    freqA = [90,130,150]
    for j in range(len(freqA)):
        chA = cor.notch(chA, freqA[j]*1e6, 80)
    freqAB = [90,250]
    for j in range(len(freqAB)):
        c3Ax4B = cor.notch(c3Ax4B, freqAB[j]*1e6, 80)
    freqBA = [90]
    for j in range(len(freqBA)):
        c4Ax3B = cor.notch(c4Ax3B, freqBA[j]*1e6, 80)
    freqB = [90, 110, 130, 150, 250]
    for j in range(len(freqB)):
        chB = cor.notch(chB, freqB[j]*1e6, 80)
    freq3 = [50, 90, 125, 130, 150, 250]
    for j in range(len(freq3)):
        ct3 = cor.notch(ct3, freq3[j]*1e6, 80)
    freq4 = [90,130,150,250]
    for j in range(len(freq4)):
        ct4 = cor.notch(ct4, freq4[j]*1e6, 80)
    freqAB = [90,130,150,250]
    for j in range(len(freqAB)):
        c3Ax4B = cor.notch(c3Ax4B, freqAB[j]*1e6, 80)
    freqBA = [50,90,110,130]
    for j in range(len(freqBA)):
        c4Ax3B = cor.notch(c4Ax3B, freqBA[j]*1e6, 80)

    # save cleaned data
    chA_clean.append(chA)
    chB_clean.append(chB)
    ct3_clean.append(ct3)
    ct4_clean.append(ct4)
    c3Ax4B_clean.append(c3Ax4B)
    c4Ax3B_clean.append(c4Ax3B)

    #########################
    # Shift all peaks to zero
    #########################
    tbin = timebin(muA); chA = shift_bins(chA, tbin)
    tbin = timebin(muB); chB = shift_bins(chB, tbin)
    tbin = timebin(mu3Ax4B); c3Ax4B = shift_bins(c3Ax4B, tbin)
    tbin = timebin(mu4Ax3B); c4Ax3B = shift_bins(c4Ax3B, tbin)


    # for autocorrelations of CT3 and CT4 we also average over all acquised data and sum all up
    rms = np.std(ct3[0:4500])
    g2_for_averaging = ct3/rms
    ct3_sum += g2_for_averaging

    rms = np.std(ct4[0:4500])
    g2_for_averaging = ct4/rms
    ct4_sum += g2_for_averaging

    # Averaged cross correlations
    avg = average_g2s(chA, chB, c3Ax4B, c4Ax3B)
    # additional data cleaning
    freq_avg = [50,110,130,144.4,150,230]
    for j in range(len(freq_avg)):
        avg = cor.notch(avg, freq_avg[j]*1e6, 80)


    # Fit with fixed mu and sigma
    xplotf, popt_avg, perr_avg = uti.fit_fixed(avg, x, -100, 100, mu_avg, sigma_avg)
    Int, dInt = uti.integral_fixed(popt_avg, perr_avg, sigma_avg)
    # TEST: use an other formula for the integral calculation
    #dInt = 2 * np.std(avg) * np.sqrt( 1.6 * sigma_avg )
    #print (np.std(avg), sigma_avg)
    dInt = np.sqrt( dInt**2 + (np.std(avg)*sigma_avg*np.sqrt(2*np.pi))**2 ) # this is the empirical formula from the simulations
    ints_fixed.append(1e6*Int); dints_fixed.append(1e6*dInt)# in femtoseconds

    # Check acquisition time of original data
    timestring = ephem.Date(data[:,0][i])
    print("{}".format(i), timestring, Int, dInt)
    # Shorter timestring for plotting, not showing year and seconds
    tstring_short = str(timestring)[5:-3]

    # FFT check
    fft = np.abs(np.fft.fft(avg-1))
    ffts.append(fft)
    
    # Subplot for all cross correlations
    the_shift = (len(chAs)-i-1)*2e-6
    ticks.append(1.+the_shift)
    ax_cross.errorbar(x, chA    + the_shift, yerr=0, linestyle="-", color = uti.color_chA,   alpha=0.5)
    ax_cross.errorbar(x, c3Ax4B + the_shift, yerr=0, linestyle="-", color = uti.color_c3A4B, alpha=0.5)
    ax_cross.errorbar(x, c4Ax3B + the_shift, yerr=0, linestyle="-", color = uti.color_c4A3B, alpha=0.5)
    ax_cross.errorbar(x, chB    + the_shift, yerr=0, linestyle="-", color = uti.color_chB,   alpha=0.5)
    ax_cross.errorbar(x, avg    + the_shift, yerr=0, linestyle="-", color = colors[i], linewidth=3, label=timestring)
    ax_cross.text(x=70, y=1+the_shift+0.7e-6, s=tstring_short, color=colors[i], fontweight="bold", bbox=dict(boxstyle="round", ec="white", fc="white", alpha=0.75))
    ax_cross.plot(xplotf,  uti.gauss_shifted(x=xplotf,  a=popt_avg[0], mu=mu_avg, sigma=sigma_avg, shift=i, inverse=True, ntotal=len(chAs)), color="black", linestyle="--", zorder=4)


# store cleaned data
np.savetxt("g2_functions/weight_rms_squared/{}/ChA_clean.txt".format(star), np.c_[chA_clean], header="{} Channel A cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/ChB_clean.txt".format(star), np.c_[chB_clean], header="{} Channel B cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/CT3_clean.txt".format(star), np.c_[ct3_clean], header="{} CT3 cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/CT4_clean.txt".format(star), np.c_[ct4_clean], header="{} CT4 cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/C3Ax4B_clean.txt".format(star), np.c_[c3Ax4B_clean], header="{} CT3A x CT4B cleaned".format(star) )
np.savetxt("g2_functions/weight_rms_squared/{}/C4Ax3B_clean.txt".format(star), np.c_[c4Ax3B_clean], header="{} CT4A x CT3B cleaned".format(star) )

############################
# Autocorrelation analysis #
############################
# ---- This is the new method ---- #
# Read in the autocorrelation functions
try:
    autocorrelation = np.loadtxt("g2_functions/weight_rms_squared/{}/autocorrelation.txt".format(star))
except:
    print ("No autocorrelation found, please make sure it exists")
    exit(1)

x_auto  = autocorrelation[:,0]
c_auto = autocorrelation[:,1]
# Fit gaussian into autocorrelation
xplotf, popt_avg_free, perr_avg_free = uti.fit(c_auto, x_auto, -30, 30)
int_auto, dint_auto = uti.integral(popt_avg_free, perr_avg_free)

ax_auto.plot(x_auto, c_auto, "o-", color="black", alpha=0.5)
ax_auto.plot(xplotf, uti.gauss(xplotf, *popt_avg_free), linestyle="--", color="red")
ax_auto.set_ylim(1-1*popt_avg_free[0] , 1+2*popt_avg_free[0])

# Add systematic error
lower_error = [zero_baseline_fluctuations[0]]
upper_error = [zero_baseline_fluctuations[1]]
if zero_baseline_systematic == True:
    asymmetric_error = np.array(list(zip(lower_error, upper_error))).T
    #ax_auto.errorbar(x=popt_avg_free[1], y=uti.gauss(popt_avg_free[1], *popt_avg_free), yerr=asymmetric_error, marker="^", color="red")
    ax_auto.fill_between(x=xplotf, y1=uti.gauss(xplotf, popt_avg_free[0]-lower_error, popt_avg_free[1], popt_avg_free[2], popt_avg_free[3]) , y2=uti.gauss(xplotf, popt_avg_free[0]+upper_error, popt_avg_free[1], popt_avg_free[2], popt_avg_free[3]), color="red", alpha=0.4, label="systematic amplitude uncertainty")
    ax_auto.legend()

    int_auto, dint_auto = uti.integral_systematic(popt_avg_free, perr_avg_free, zero_baseline_fluctuations)
    # now dint_auto is an array [error_down, error_up]

    print (dint_auto)
    #dint_auto = np.array(list(zip(dint_auto[0], dint_auto[1]))).T


##############################################################
#### making SC plot (spatial coherence) via integral data ####
##############################################################
xplot = np.arange(0.1,300,0.1)

# get baselines for x axes
baselines  = data[:,1]
dbaselines = data[:,2]

# Average over all 4 cross correlations
ints_avg, dints_avg = uti.weighted_avg(intsA,dintsA, intsB,dintsB, ints3Ax4B,dints3Ax4B, ints4Ax3B, dints4Ax3B)

# Add zero-baseline
baselines   = np.append(baselines, 5.43) # Average photon distance in a 12 m diameter circle
dbaselines  = np.append(dbaselines,2.50) # rms distance of photon in a 12 m diameter circle
ints_fixed  = np.append(ints_fixed,  1e6*int_auto)
dints_fixed = np.append(dints_fixed, 1e6*dint_auto)
colors.append( (0,0,0,1.) )

# Calculate SC fit and errorbars for the averaged signal
poptavg, pcov = curve_fit(uti.spatial_coherence, baselines, ints_fixed, sigma=dints_fixed, p0=[25, 2.2e-9])
perravg = np.sqrt(np.diag(pcov))

#--------------------#
# Try fitting with ods
# Model object
from scipy import odr
sc_model = odr.Model(uti.spatial_coherence_odr)
# RealData object
rdata = odr.RealData( baselines, ints_fixed, sx=dbaselines, sy=dints_fixed )
# Set up ODR with model and data
odr = odr.ODR(rdata, sc_model, beta0=[25,2.2e-9])
# Run the regression
out = odr.run()
# Fit parameters
popt_odr = out.beta
perr_odr = out.sd_beta
chi_odr = out.res_var
print('CHIIII= {}'.format(out.res_var))


# evaluating chi squared reduced
chi, chi_red = uti.chi_squared(ints_fixed, uti.spatial_coherence(baselines, *popt_odr), error=dints_fixed, N=len(ints_fixed), par=2)
print('CHI= {} & reduced= {}'.format(chi, chi_red))
#--------------------#

deltas_sc_avg = []
for i in xplot:
    deltas_sc_avg.append( np.abs(uti.delta_spatial_coherence(x=i, A=poptavg[0],dA=perravg[0], phi=poptavg[1], dphi=perravg[1])) )
print ("Angular diameter AVG (fixed): {:.2f} +/- {:.2f} (mas)".format(uti.rad2mas(poptavg[1]),  uti.rad2mas(perravg[1])))
print ("Angular diameter AVG (odr)  : {:.2f} +/- {:.2f} (mas)".format(uti.rad2mas(popt_odr[1]), uti.rad2mas(perr_odr[1])))
print ("Zero baseline correlation   : {:.2f} +/- {:.2f} (fs)".format(popt_odr[0], perr_odr[0]))

####################################################
# plot datapoints in SC plot and fit to all points #
####################################################
# cross and auto correlations
for i in range (0,len(baselines)):
    ax_sc.errorbar(baselines[i], ints_fixed[i], yerr=dints_fixed[i], xerr=dbaselines[i], marker="o", linestyle="", color=colors[i])
    #plt.text(baselines[i]+1,ints_fixed[i]+0.5,ephem.Date(data[:,0][i]), color=colors[i])
#plt.plot(xplot, uti.spatial_coherence(xplot,*poptavg),   label="fit", color="red", linewidth=2)

np.savetxt("spatial_coherence/{}_sc_data.txt".format(star), np.c_[baselines, dbaselines, ints_fixed, dints_fixed], header="{} {} \nbl\tdbl\tscA\tdscA".format(popt_odr[0], popt_odr[1]))

# Obtain values for error band
lower = []; upper = []
for i in xplot:
    uncertainty = uti.get_error_numerical(x=i, amp=popt_odr[0], damp=perr_odr[0], ang=popt_odr[1], dang=perr_odr[1])
    uncertainty = uti.get_error_numerical(x=i, amp=popt_odr[0], damp=perr_odr[0], ang=popt_odr[1], dang=perr_odr[1])

    lower.append(uti.spatial_coherence(i, *popt_odr) - uncertainty)
    upper.append(uti.spatial_coherence(i, *popt_odr) + uncertainty)

lower = cor.lowpass(lower, cutoff=0.001)
upper = cor.lowpass(upper, cutoff=0.001)

ax_sc.set_ylim(0,)
# Special treatment of Acrux: do not fit into the spatial coherence data, instead zoom in
if star != "Acrux":
    ax_sc.fill_between(xplot, lower, upper, color="#003366", alpha=0.15)
    ax_sc.plot(xplot, uti.spatial_coherence(xplot,*popt_odr),   label="ODR fit, $\chi^2$/dof={:.2f}".format(chi_odr), color="#003366", linewidth=2)
    ax_sc.text(75, 38, "Angular diameter: {:.2f} +/- {:.2f} mas".format(uti.rad2mas(popt_odr[1]), uti.rad2mas(perr_odr[1])), color="#003366", fontsize=10)
    ax_sc.set_xlim(-15,250)
    ax_sc.legend(loc="upper right")
    plt.tight_layout()

plt.savefig("images/{}_sc.pdf".format(star))
plt.savefig("images/{}_sc.png".format(star))

# In addition save also only the spatial coherence plot
#extent = ax_sc.get_window_extent()#.transformed(fig.dpi_scale_trans.inverted())
#plt.savefig("images/{}_sc_only.pdf".format(star), bbox_inches=extent)
## Pad the saved area by 10% in the x-direction and 20% in the y-direction
#fig.savefig('ax2_figure_expanded.png', bbox_inches=extent.expanded(1.1, 1.2))


### make only SC plot ###
fig, ax = plt.subplots()
# spatial coherence
for i in range (0,len(baselines)):
    ax.errorbar(baselines[i], ints_fixed[i], yerr=dints_fixed[i], xerr=dbaselines[i], marker="o", linestyle="", color=colors[i])
if star != "Acrux":
    ax.fill_between(xplot, lower, upper, color="#003366", alpha=0.15)
    ax.plot(xplot, uti.spatial_coherence(xplot,*popt_odr),   label="ODR fit, $\chi^2$/dof={:.2f}".format(chi_odr), color="#003366", linewidth=2)
    ax.text(75, 38, "Angular diameter: {:.2f} +/- {:.2f} mas".format(uti.rad2mas(popt_odr[1]), uti.rad2mas(perr_odr[1])), color="#003366", fontsize=10)
    ax.set_xlim(-15,250)
    ax.legend(loc="upper right")
    plt.tight_layout()

plt.title("{}".format(star))
plt.xlabel("Projected baseline (m)")
plt.ylabel("Spatial coherence (fs)")
ax.axhline(y=0.0, color='black', linestyle='--')
#plt.xlim(0,200)

plt.legend()
plt.tight_layout()
plt.savefig("images/{}_sc_only.pdf".format(star))
plt.savefig("images/{}_sc_only.png".format(star))

plt.show()