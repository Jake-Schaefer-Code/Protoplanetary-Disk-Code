import matplotlib.pyplot as plt 
import numpy as np 
from astropy.io import fits
from scipy.ndimage.interpolation import rotate

def mask_circle(image, center, radius = 15.0, filler = 0.0, keep = 1.0): 
    Y, X = np.ogrid[:len(image[:,0]),:len(image[0,:])] 
    dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2) 
    dist_from_center[dist_from_center < radius] = filler 
    dist_from_center[dist_from_center >= radius] = keep 
    image = dist_from_center * image
    return image

def chi_square(real, model):
    sum = 0
    for i in range(len(real[:,0])):
        for j in range(len(real[:,0])):
            real_data = real[i,j]
            model_data = model[i,j]
            if (real_data != 0) and (model_data != 0):
                sum+= (((model_data - real_data)**2)/real_data)
                
    return sum
    
hdul = fits.open('/Users/jakeschaefer/Desktop/research/MWC_275_GPI_2014-04-24_J.fits') #crop to 177 by 177
data = hdul[0].data #hdul is a list of data packets
header = hdul[0].header
hdul.close()
#print(np.shape(data[1]))


#hdul2 = fits.open('/Users/jakeschaefer/Desktop/research/fits1.fits') 
hdul2 = fits.open('/Users/jakeschaefer/Desktop/research/fits1.fits') #change inner disk so not visible, 
#and make outer disk so that it is barely visible
#2 ways to make it less visible: make it less dense, so light doesnt have a chance to scatter off of it (it would be a settled disk)
#outer portion is not part of the chi squared because if it is too bright it is wrong
#inner disk is not part of it
#DS9 makes disk easy to plot. Online version: search JS9 astronomy
data2 = hdul2[0].data
header2 = hdul2[0].header
hdul2.close()
#imagine have some image[ymin:ymax, xmin:xmax]
#[ycent-176/2:ycent+176/2, ] #check size of array to know if off by 1.  
#put really hot pixel in the center and see if it moves


#print(np.shape(data2[1]))

center = (header['STAR_X'],header['STAR_Y'])
tmp = data[1]
tmp = tmp[int(center[0] - 177/2):int(center[0] + 177/2),int(center[1] - 177/2):int(center[1] + 177/2)]
#print(len(tmp[:,0]))
#print(center[0] - 176/2)
center = (176/2,176/2)
mask = np.ones(np.shape(tmp))
mask = mask_circle(mask,center)

mask[tmp>100.] = 0.0
mask[tmp<-20.] = 0.0

mask2 = np.ones(np.shape(tmp))
mask2 = mask_circle(mask,center, radius=60., filler = 1.0, keep = 0.0)
std = np.std(np.nan_to_num(mask2*tmp))
#print(std)


#mask2[np.abs(data[1]) < std] = 0.0
image = mask2*tmp
image[image==0.0] = np.nan
#print(image[88,88])
#image[88,88] = 3;
#for i in range(len(image[0,:])):
    #image[i,88] = 3
    #image[88,i] = 3
plt.imshow(image,origin='lower',vmin=0.0,vmax=3)
plt.colorbar()
plt.show()
plt.close()


image = np.nan_to_num(image)
image_rot = rotate(image,42.,axes=(1,0))
image_rot = image_rot[int(125 - 177/2):int(125 + 177/2),int(125 - 177/2):int(125 + 177/2)]
#print(len(image_rot[:,0]))
plt.imshow(image_rot,origin='lower',vmin=0.0,vmax=3)
plt.colorbar()
plt.show()
plt.close()

#image = np.nan_to_num(image,0.0000000000001)
#image[image==0.0] = 0.0000000000001
#image_rot[image_rot==0.0] = 0.0000000000001
test_chi = chi_square(image,image)
print(test_chi)
