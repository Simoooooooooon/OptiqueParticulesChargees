import numpy as np


def normalize(raw_image):
    """
    Parameters
    ----------
    raw_image : Numpy Data Array

    Returns
    -------
    Raw_Image : Normalized Data Array in grey values.
    """
    min_val = raw_image.min()
    max_val = raw_image.max()
    raw_image = np.interp(raw_image, (min_val, max_val), (0, 255))

    return raw_image


def remove_two_columns(raw_image):
    """
    Parameters
    ----------
    raw_image : Numpy Array

    Returns
    -------
    raw_image : Same Array with two rows removed
    """
    raw_image = raw_image[1:, 1:]
    raw_image = raw_image[1:, 1:]

    return raw_image


def reverse_alternate_rows(image):
    """
    In case of a triangle scanning, this function invert one line over 2 to
    obtain the right Image.
    
    Parameters
    ----------
    image : Data Array of the Image

    Returns
    -------
    Image : Corrected Data Array
    """
    image[1::2, :] = image[1::2, ::-1]
    return image


def average(raw_data, samples_per_step, pixels_number):
    # Convert raw_data to a NumPy array for efficient processing
    raw_data_array = np.array(raw_data)

    # Reshape the array so that each row contains samples_per_step elements
    reshaped_data = raw_data_array.reshape(-1, samples_per_step)

    # Compute the mean along the second axis (axis=1) to average each group
    averaged_data = np.mean(reshaped_data, axis=1)

    # Reshape to a 2D array (pixels_number x pixels_number)
    image_array = averaged_data.reshape(pixels_number, pixels_number)

    return image_array
