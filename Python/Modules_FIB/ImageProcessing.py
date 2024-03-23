import numpy as np


def normalize(raw_image):
    """
    Normalizes a raw image data array to a scale of 0 to 255 (8-bit grey values).

    Parameters:
        raw_image (numpy.ndarray): The input raw image data array.

    Returns:
        numpy.ndarray: The normalized image data array with values scaled to the range [0, 255].
    """

    try:
        min_val = raw_image.min()
        max_val = raw_image.max()
        raw_image = np.interp(raw_image, (min_val, max_val), (0, 255))

        return raw_image

    except Exception as e:
        raise Exception(f"\nFunction normalize returned : {e}")


def remove_two_columns(raw_image):
    """
    Removes the first two rows and columns from an image data array to correct for edge artifacts.

    Parameters:
        raw_image (numpy.ndarray): The input image data array.

    Returns:
        numpy.ndarray: The modified image data array with the first two rows and columns removed.
    """
    try:
        raw_image = raw_image[1:, 1:]
        raw_image = raw_image[1:, 1:]

        return raw_image

    except Exception as e:
        raise Exception(f"\nFunction remove_two_columns returned : {e}")


def reverse_alternate_rows(image):
    """
    Reverses every alternate row in an image data array. This is used to correct for the scanning direction in
    bidirectional scanning methods, ensuring a consistent orientation across all rows.

    Parameters:
        image (numpy.ndarray): The input image data array.

    Returns:
        numpy.ndarray: The image data array with alternate rows reversed.
    """

    try:
        image[1::2, :] = image[1::2, ::-1]
        return image

    except Exception as e:
        raise Exception(f"\nFunction reverse_alternate_rows returned : {e}")


def average(raw_data, samples_per_step, pixels_number):
    """
    Averages groups of samples in raw data to reduce noise and improve signal quality. This is useful in
    situations where multiple samples correspond to a single pixel value.

    Parameters:
        raw_data (list or numpy.ndarray): The raw data samples to be averaged.
        samples_per_step (int): The number of samples corresponding to each pixel.
        pixels_number (int): The total number of pixels in one dimension of the square image.

    Returns:
        numpy.ndarray: The averaged image data array, reshaped to a 2D square array corresponding to the
                       dimensions of the image.
    """

    try:
        # Convert raw_data to a NumPy array for efficient processing
        raw_data_array = np.array(raw_data)

        # Reshape the array so that each row contains samples_per_step elements
        reshaped_data = raw_data_array.reshape(-1, samples_per_step)

        # Compute the mean along the second axis (axis=1) to average each group
        averaged_data = np.mean(reshaped_data, axis=1)

        # Reshape to a 2D array (pixels_number x pixels_number)
        image_array = averaged_data.reshape(pixels_number, pixels_number)

        return image_array

    except Exception as e:
        raise Exception(f"\nFunction average returned : {e}")
