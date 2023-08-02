import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
import image_chi as ic
from scipy.ndimage import rotate
from scipy.ndimage import gaussian_filter

def correctReddening(value, band):
    """
    Correct for reddening in the observed data. R_v = 3.1
    A_lam / A_v = a(x) + b(x) / R_v = shiftVal
    where shiftVal is given in CCM 1989
    """
    R_v = 3.1
    A_v = 0.5
    bandMidpoints = {
        # mostly for convenience
        "V": 0.55,
        "R": 0.658,
        "I": 0.806,
        "J": 1.22,
        "H": 1.63,
        "K": 2.19,
        "L": 3.45
    }

    shiftVals = {
        # values of a(x) + b(x) / R_v for different bands
        "V": 1,
        "R": 0.751,
        "I": 0.479,
        "J": 0.282,
        "H": 0.190,
        "K": 0.114,
        "L": 0.056
    }

    shiftVal = shiftVals[band]

    A_lam = A_v * shiftVal

    f_vega = {
        # * 10^-11 erg cm^-2 s^-1 A^-1
        # https://www.astronomy.ohio-state.edu/martini.10/usefuldata.html
        # L band flux calculated from https://www.gemini.edu/observing/resources/magnitudes-and-fluxes
        "V": 363.1,
        "R": 217.7,
        "I": 112.6,
        "J": 31.47,
        "H": 11.38,
        "K": 3.961,
        "L": 0.531
    }
    f_ref = f_vega[band] * 10 # convert from erg cm^-2 s^-2 A^-1 to W m^-2 um^-1
    flux = f_ref * bandMidpoints[band] # convert to W m^-2

    mag = -2.5 * np.log10(value/flux) # convert to mags
    newMag = mag + A_lam # adjust for extinction
    corrected = flux * 10 ** (newMag/(-2.5)) # convert back to flux

    return corrected

hdu_kliprdi = fits.open('kliprdi_collapsed.fits')
k = hdu_kliprdi[1].data
hdu_kliprdi.close()

model = fits.open('disk_J.fits')
m = model[0].data
model.close()
#print('model: ', np.shape(m))
k[k == np.nan] = 0.0
m = m * 0.00026802
m = gaussian_filter(m, sigma=1)
m = rotate(m, 138)
mask = ic.create_full_mask(m, (int(len(m)/2),int(len(m)/2)), maxradius=100, minradius=20)
m = mask * m

reddenedModel = correctReddening(m, "J")
# flatM = m.flat
# for entry in flatM:
#     if entry != np.nan:
#         print(entry)

for index, value in np.ndenumerate(m):
    corrVal = reddenedModel[index]
    if np.nan not in (value, corrVal):
        print('percent change: ', 100 * (value - corrVal)/value)
print('max model point: ', np.nanmax(m))
print('max reddened point: ', np.nanmax(reddenedModel))
print('percent change: ', 100 * (np.nanmax(m) - np.nanmax(reddenedModel))/np.nanmax(m))

#print('kliprdi: ', np.shape(k))

fig, ( ax2, ax3) = plt.subplots(1,2)
#plt.set_cmap('inferno')
#im = ax1.imshow(k, vmin = 0.0, vmax = 0.05)
#ax1.set_title('Observed')
im = ax2.imshow(m, vmin = 0.0, vmax = 0.05)
ax2.set_title('Model')
im = ax3.imshow(reddenedModel, vmin = 0.0, vmax = 0.05)
ax3.set_title('Reddened Model')
#plt.colorbar(im, ax = [ax1, ax2])
plt.show()
