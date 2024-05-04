import matplotlib.pyplot as plt
from PIL import Image
import numpy as np


def Image_to_voltage_pairs(image_path, voltage_range, sensitivity):
    """
    Converts an image into a list of voltage coordinates based on pixel transparency.

    This function reads an image from the specified path and calculates the voltage coordinates
    for non-transparent pixels. It maintains the image's aspect ratio in its voltage representation.
    Each pixel's position is converted into a voltage coordinate, which is then adjusted to be
    centered within a given voltage range.

    Parameters:
    - image_path (str): Path to the image file.
    - voltage_range (float): The maximum range of voltage values for the output coordinates.
    - sensitivity (float): The smallest change in voltage represented in the output, determining the granularity.

    Returns:
    - list of tuple: A list of (voltage_x, voltage_y) tuples for non-transparent pixels.

    The function supports images with transparency (e.g., RGBA format), where only non-transparent pixels
    are converted into voltage coordinates.
    """

    try:
        image = Image.open(image_path)
        width, height = image.size
        aspect_ratio = width / height

        # Determine the voltage ranges that maintain the image aspect ratio
        if width > height:
            voltage_range_x = voltage_range
            voltage_range_y = voltage_range / aspect_ratio
        else:
            voltage_range_y = voltage_range
            voltage_range_x = voltage_range * aspect_ratio

        # Create grids for voltage coordinates, adjusting the starting point
        x_coords = np.arange(-voltage_range_x/2, voltage_range_x/2, sensitivity)[:width]
        y_coords = np.arange(voltage_range_y/2, -voltage_range_y/2, -sensitivity)[:height]

        # Adjust the coordinates so the image center aligns with the voltage center
        offset_x = (voltage_range_x - (width - 1) * sensitivity) / 2
        offset_y = (voltage_range_y - (height - 1) * sensitivity) / 2
        x_coords += offset_x
        y_coords -= offset_y  # Subtract because y-coords are decreasing

        non_transparent_coords = []

        # Collect non-transparent pixel coordinates
        for y in range(height):
            for x in range(width):
                pixel = image.getpixel((x, y))
                # Check if pixel is non-transparent (assuming RGBA)
                if len(pixel) == 4 and pixel[3] > 0:
                    voltage_x = x_coords[x]
                    voltage_y = y_coords[y]
                    non_transparent_coords.append((voltage_x, voltage_y))

        # Sort the coordinates to go row by row, left to right
        non_transparent_coords.sort(key=lambda coord: (-coord[1], coord[0]))

        return non_transparent_coords

    except Exception as e:
        raise Exception(f"\nCouldn't generate voltage pairs : {e}")


def pairs_to_signal(voltage_pairs, samples_per_pixel):
    """
    Generates Left-Right (LR) and Up-Down (UD) signals from a list of voltage coordinates.

    This function creates continuous signal arrays for both the x (LR) and y (UD) coordinates from a list
    of voltage coordinates, where each coordinate is repeated a specified number of times to simulate
    the duration each voltage is held during a scanning process.

    Parameters:
    - voltage_pairs (list of tuple): A list of (voltage_x, voltage_y) tuples representing voltage coordinates.
    - samples_per_pixel (int): Number of samples each voltage value should be held, corresponding to the
                               duration a voltage level is maintained.

    Returns:
    - tuple of numpy.ndarray: A tuple containing two 1D numpy arrays for the LR and UD signals respectively.

    This method is useful in applications requiring precise control of output signals, such as in scanning
    microscopy or other applications involving precise voltage control.
    """

    try:
        # Initializing lists to store signals
        signal_lr = []
        signal_ud = []

        for point in voltage_pairs:
            # Generation of constant values for each point during the defined time
            signal_lr.extend([point[0]] * samples_per_pixel)
            signal_ud.extend([point[1]] * samples_per_pixel)

        # Converting lists into 1D numpy arrays
        signal_lr = np.array(signal_lr)
        signal_ud = np.array(signal_ud)

        return signal_lr, signal_ud

    except Exception as e:
        raise Exception(f"\nCouldn't generate the signals from the voltage pairs : {e}")


if __name__ == '__main__':
    import matplotlib
    matplotlib.use('TkAgg')

    # Example usage
    image_path = 'INSA.png'
    voltage_range = 20  # Example voltage range
    bits = 16  # Example bits resolution
    samples_per_pixel = 10
    sensitivity = voltage_range / (2 ** bits)

    voltage_pairs = Image_to_voltage_pairs(image_path, voltage_range, sensitivity)

    signal_lr, signal_ud = pairs_to_signal(voltage_pairs, samples_per_pixel)

    # Unzip the list of coordinates
    x_vals, y_vals = zip(*voltage_pairs)
    plt.figure(figsize=(10, 6))
    plt.scatter(x_vals, y_vals, s=1)  # s=1 sets the size of each point
    plt.title('Voltage Coordinates for Non-Transparent Pixels')
    plt.xlabel('Voltage X')
    plt.ylabel('Voltage Y')
    plt.grid(True)
    plt.show()

    # Plotting signals part
    fig, ax = plt.subplots(2, 1, figsize=(10, 6))

    ax[0].set_title('Signal Left-Right (LR)')
    ax[0].set_xlabel('Sample Number')
    ax[0].set_ylabel('Voltage')
    ax[0].plot(signal_lr)

    ax[1].set_title('Signal Up-Down (UD)')
    ax[1].set_xlabel('Sample Number')
    ax[1].set_ylabel('Voltage')
    ax[1].plot(signal_ud)

    plt.tight_layout()
    plt.show()
