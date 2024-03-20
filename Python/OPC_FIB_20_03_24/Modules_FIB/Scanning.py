import numpy as np
from Modules_FIB import Ni_Dependencies as NID


def Scanning_Rise(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read):
    """
    Generates and reads scanning signals for a Focused Ion Beam (FIB) system.

    This function configures and executes two simultaneous tasks: one for writing
    analog output signals for scanning (both horizontal and vertical), and another
    for reading the corresponding analog input signal. It initially sets a voltage
    for 'channel_ud' to avoid synchronization issues at the start. Then it performs
    scanning by generating staircase signals in both horizontal and vertical directions
    while reading the input signal synchronously. The function averages the read data
    if more than one sample per pixel is acquired.

    Parameters:
    - time_per_pixel: Time spent per pixel, in microseconds.
    - sampling_frequency: Sampling frequency for data acquisition, in Hz.
    - pixels_number: Number of pixels per row and column in the image.
                     Two additional pixels are considered to avoid synchronization issues.
    - channel_lr: Channel name for the left-right scanning signal.
    - channel_ud: Channel name for the up-down scanning signal.
    - channel_read: Channel name for reading the input signal.

    Returns:
    - A 2D NumPy array representing the acquired image. The array dimensions correspond
      to 'pixels_number' (minus 2 to compensate for the initial extra rows and columns),
      and each element represents the averaged signal value at the corresponding pixel.
    """

    # We have to take 2 more lines and columns because the acquisition isn't really synchronised at first
    pixels_number += 2

    # Converts microseconds to seconds
    time_per_pixel = time_per_pixel / 1000000
    timeout = time_per_pixel * pixels_number * pixels_number + 1

    # Number of samples per step/pixel
    samples_per_step = int(time_per_pixel * sampling_frequency)
    total_samples_to_read = samples_per_step * pixels_number ** 2

    # Configuring the voltages for the staircases
    min_tension = -10
    max_tension = 10

    # Set initial voltage for channel_ud
    NID.initial_voltage_setting(min_tension, max_tension, channel_ud)

    # Generating the staircase signal for left-right scanning (repeated "pixels_number" times)
    horizontal_staircase = np.repeat(np.linspace(min_tension, max_tension, pixels_number), samples_per_step)
    complete_horizontal_staircase = np.tile(horizontal_staircase, pixels_number)

    # Generating the staircase signal for top-down scanning (unique for the entire image)
    vertical_staircase = np.repeat(np.linspace(max_tension, min_tension, pixels_number),
                                   samples_per_step * pixels_number)

    # Write both signal in one task and read with another
    write_task, read_task = NID.configure_tasks(channel_lr, channel_ud, channel_read, min_tension, max_tension,
                                                sampling_frequency, complete_horizontal_staircase,
                                                total_samples_to_read,
                                                vertical_staircase)
    print(write_task, read_task)
    # Structure datas to write
    data_to_write = np.array([complete_horizontal_staircase, vertical_staircase])

    # Create a StreamWriter for the analog outputs
    raw_data = NID.write_and_read(write_task, read_task, data_to_write, total_samples_to_read, timeout)
    # Stop the tasks

    # If there is only one sample per pixel, we skip the averaging process
    if samples_per_step == 1:

        # Reshape to a numpy 2D array (pixels_number x pixels_number)
        image_array = np.array(raw_data).reshape(pixels_number, pixels_number)

    else:

        # Convert raw_data to a NumPy array for efficient processing
        raw_data_array = np.array(raw_data)

        # Reshape the array so that each row contains samples_per_step elements
        reshaped_data = raw_data_array.reshape(-1, samples_per_step)

        # Compute the mean along the second axis (axis=1) to average each group
        averaged_data = np.mean(reshaped_data, axis=1)

        # Reshape to a 2D array (pixels_number x pixels_number)
        image_array = averaged_data.reshape(pixels_number, pixels_number)

    # To avoid weird behaviour we delete the first column and the first row of the image twice
    image_array = image_array[1:, 1:]
    image_array = image_array[1:, 1:]
    NID.close(write_task, read_task)
    return image_array


def Scanning_Triangle(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read):
    """
    Generates and reads triangle scanning signals for a Focused Ion Beam (FIB) system.

    This function configures and executes two simultaneous tasks: one for writing
    analog output signals for triangle scanning (both horizontal and vertical), and another
    for reading the corresponding analog input signal. It initially sets a voltage
    for 'channel_ud' to avoid synchronization issues at the start. Then it performs
    scanning by generating staircase signals in both horizontal and vertical directions
    while reading the input signal synchronously. The function averages the read data
    if more than one sample per pixel is acquired.

    Parameters:
    - time_per_pixel: Time spent per pixel, in microseconds.
    - sampling_frequency: Sampling frequency for data acquisition, in Hz.
    - pixels_number: Number of pixels per row and column in the image.
                     Two additional pixels are considered to avoid synchronization issues.
    - channel_lr: Channel name for the left-right scanning signal.
    - channel_ud: Channel name for the up-down scanning signal.
    - channel_read: Channel name for reading the input signal.

    Returns:
    - A 2D NumPy array representing the acquired image. The array dimensions correspond
      to 'pixels_number' (minus 2 to compensate for the initial extra rows and columns),
      and each element represents the averaged signal value at the corresponding pixel.
    """

    # We have to take 2 more lines and columns because the acquisition isn't really synchronised at first
    pixels_number += 2

    # Converts microseconds to seconds
    time_per_pixel = time_per_pixel / 1000000
    timeout = time_per_pixel * pixels_number * pixels_number + 1

    # Number of samples per step/pixel
    samples_per_step = int(time_per_pixel * sampling_frequency)
    total_samples_to_read = samples_per_step * pixels_number ** 2

    # Configuring the voltages for the staircases
    min_tension = -10
    max_tension = 10

    # Set initial voltage for channel_ud
    NID.initial_voltage_setting(min_tension, max_tension, channel_ud)

    # Generating the staircase signal for left-right scanning (repeated "pixels_number" times)
    horizontal_staircase = np.repeat(np.append(np.linspace(min_tension, max_tension, pixels_number),
                                               np.linspace(max_tension, min_tension, pixels_number)), samples_per_step)
    complete_horizontal_staircase = np.tile(horizontal_staircase, pixels_number // 2)

    # Generating the staircase signal for top-down scanning (unique for the entire image)
    vertical_staircase = np.repeat(np.linspace(max_tension, min_tension, pixels_number),
                                   samples_per_step * pixels_number)

    # Write both signal in one task and read with another
    write_task, read_task = NID.configure_tasks(channel_lr, channel_ud, channel_read, min_tension, max_tension,
                                                sampling_frequency, complete_horizontal_staircase,
                                                total_samples_to_read,
                                                vertical_staircase)

    # Structure datas to write
    data_to_write = np.array([complete_horizontal_staircase, vertical_staircase])
    # Create a StreamWriter for the analog outputs
    raw_data = NID.write_and_read(write_task, read_task, data_to_write, total_samples_to_read, timeout)

    # If there is only one sample per pixel, we skip the averaging process
    if samples_per_step == 1:

        # Reshape to a numpy 2D array (pixels_number x pixels_number)
        image_array = np.array(raw_data).reshape(pixels_number, pixels_number)

    else:

        # Convert raw_data to a NumPy array for efficient processing
        raw_data_array = np.array(raw_data)

        # Reshape the array so that each row contains samples_per_step elements
        reshaped_data = raw_data_array.reshape(-1, samples_per_step)

        # Compute the mean along the second axis (axis=1) to average each group
        averaged_data = np.mean(reshaped_data, axis=1)

        # Reshape to a 2D array (pixels_number x pixels_number)
        image_array = averaged_data.reshape(pixels_number, pixels_number)

    # To avoid weird behaviour we delete the first column and the first row of the image twice
    image_array = image_array[1:, 1:]
    image_array = image_array[1:, 1:]
    NID.close(write_task, read_task)
    return image_array


def VideoStair(time_per_pixel, sampling_frequency, pixels_number):
    """
    Generate staircase signals for video scanning.

    This function generates staircase signals for both horizontal and vertical scanning.
    It calculates the number of samples per step/pixel, configures voltages for the staircases,
    and generates the staircase signals for top-down scanning (unique for the entire image).

    Args:
        time_per_pixel (float): The time (in microseconds) spent on each pixel during scanning.
        sampling_frequency (float): The sampling frequency for data acquisition, in Hz.
        pixels_number (int): The number of pixels in one dimension of the image.

    Returns:
        tuple: A tuple containing three numpy arrays:
            - data_to_write: The complete staircase signals for both horizontal and vertical scanning.
            - complete_horizontal_staircase: The staircase signal for horizontal scanning.
            - vertical_staircase: The staircase signal for vertical scanning.

    """

    # We have to take 2 more lines and columns because the acquisition isn't really synchronised at first
    pixels_number += 2

    # Converts microseconds to seconds
    time_per_pixel = time_per_pixel / 1000000

    # Number of samples per step/pixel
    samples_per_step = int(time_per_pixel * sampling_frequency)

    # Configuring the voltages for the staircases
    min_tension = -10
    max_tension = 10

    # Generating the staircase signal for left-right scanning (repeated "pixels_number" times)
    horizontal_staircase = np.repeat(np.linspace(min_tension, max_tension, pixels_number), samples_per_step)
    complete_horizontal_staircase = np.tile(horizontal_staircase, pixels_number)

    # Generating the staircase signal for top-down scanning (unique for the entire image)
    vertical_staircase = np.repeat(np.linspace(max_tension, min_tension, pixels_number),
                                   samples_per_step * pixels_number)

    data_to_write = np.array([complete_horizontal_staircase, vertical_staircase])
    return data_to_write, complete_horizontal_staircase, vertical_staircase


def videoInitConf(channel_lr, channel_ud, channel_read, complete_horizontal_staircase, vertical_staircase,
                  pixels_number, time_per_pixel, data_to_write, sampling_frequency):
    """
    Initialize configuration for several close in time
 scanning (video scanning).

    This function initializes the configuration for video scanning, including setting up tasks for
    writing and reading signals, configuring voltage settings, and calculating timeout.

    Args:
        channel_lr (str): The name of the analog output channel for left-right scanning.
        channel_ud (str): The name of the analog output channel for up-down scanning.
        channel_read (str): The name of the analog input channel for reading the signal.
        complete_horizontal_staircase (numpy.array): The staircase signal for horizontal scanning.
        vertical_staircase (numpy.array): The staircase signal for vertical scanning.
        pixels_number (int): The number of pixels in one dimension of the image.
        time_per_pixel (float): The time (in microseconds) spent on each pixel during scanning.
        data_to_write (numpy.array): The complete staircase signals for both horizontal and vertical scanning.
        sampling_frequency (float): The sampling frequency for data acquisition, in Hz.

    Returns:
        tuple: A tuple containing the following elements:
            - samples_per_step (int): The number of samples per step/pixel.
            - total_samples_to_read (int): The total number of samples to read during data acquisition.
            - timeout (float): The maximum timeout for data acquisition, in seconds.
            - write_task (nidaqmx.Task): The task configured for writing scanning signals.
            - read_task (nidaqmx.Task): The task configured for reading the input signal.

    """

    # We have to take 2 more lines and columns because the acquisition isn't really synchronised at first
    pixels_number += 2

    # Converts microseconds to seconds
    time_per_pixel = time_per_pixel / 1000000
    timeout = time_per_pixel * pixels_number * pixels_number + 1

    # Number of samples per step/pixel
    samples_per_step = int(time_per_pixel * sampling_frequency)
    total_samples_to_read = samples_per_step * pixels_number ** 2

    # Configuring the voltages for the staircases
    min_tension = -10
    max_tension = 10

    NID.initial_voltage_setting(min_tension, max_tension, channel_ud)
    write_task, read_task = NID.configure_tasks(channel_lr, channel_ud, channel_read, min_tension, max_tension,
                                                sampling_frequency, complete_horizontal_staircase,
                                                total_samples_to_read,
                                                vertical_staircase)

    NID.writer(write_task, data_to_write)

    return samples_per_step, total_samples_to_read, timeout, write_task, read_task


def videoGo(pixels_number, write_task, read_task, total_samples_to_read, timeout):
    """
    Start video scanning process.

    This function starts the video scanning process by writing and reading signals simultaneously,
    and processes the acquired data into an image array.

    Args:
        pixels_number (int): The number of pixels in one dimension of the image.
        write_task (nidaqmx.Task): The task configured for writing scanning signals.
        read_task (nidaqmx.Task): The task configured for reading the input signal.
        total_samples_to_read (int): The total number of samples to read during data acquisition.
        timeout (float): The maximum timeout for data acquisition, in seconds.

    Returns:
        numpy.array: The image array containing the acquired data.
    """
    # We have to take 2 more lines and columns because the acquisition isn't really synchronised at first    
    pixels_number += 2

    raw_data = NID.quick_write_and_read(write_task, read_task, total_samples_to_read, timeout)

    # If there is only one sample per pixel, we skip the averaging process

    image_array = np.array(raw_data).reshape(pixels_number, pixels_number)

    image_array = image_array[1:, 1:]
    image_array = image_array[1:, 1:]

    return image_array
