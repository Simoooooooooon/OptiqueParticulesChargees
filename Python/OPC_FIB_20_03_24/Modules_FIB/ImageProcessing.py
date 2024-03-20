import numpy as np


def normalize(raw_image):
    """
    Parameters
    ----------
    raw_image : Raw Data Array

    Returns
    -------
    Raw_Image : Normalized Data Array in grey values.
    """
    min_val = raw_image.min()
    max_val = raw_image.max()
    if max_val > min_val:
        raw_image = ((raw_image - min_val) / (max_val - min_val)) * 255
        raw_image = raw_image.astype(np.uint8)
    return raw_image


def triangle_scanning(image, pixel_size):
    """
    In case of a triangle scanning, this function invert one line over 2 to
    obtain the right Image.
    
    Parameters
    ----------
    image : Data Array of the Image
    pixel_size : Size of the Image

    Returns
    -------
    Image : Corrected Data Array
    """
    for i in range(pixel_size):
        if i % 2 == 1:
            image[i] = image[i][::-1]
    return image
