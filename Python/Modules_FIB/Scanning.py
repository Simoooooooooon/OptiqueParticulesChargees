import numpy as np
from Modules_FIB import Ni_Dependencies as NID
from Modules_FIB import ImageProcessing


def rise_scanning(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read):
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
                                                total_samples_to_read)
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
        image_array = ImageProcessing.average(raw_data, samples_per_step, pixels_number)

    # To avoid weird behaviour we delete the first row of the image twice
    image_array = ImageProcessing.remove_two_columns(image_array)

    # Normalize the values between 0 and 255
    image_array = ImageProcessing.normalize(image_array)

    # Closes all tasks
    NID.close_rw_tasks(write_task, read_task)

    return image_array.astype(np.uint8)


def triangle_scanning(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read):
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
                                                total_samples_to_read)

    # Structure datas to write
    data_to_write = np.array([complete_horizontal_staircase, vertical_staircase])

    # Create a StreamWriter for the analog outputs
    raw_data = NID.write_and_read(write_task, read_task, data_to_write, total_samples_to_read, timeout)

    # Closes all tasks
    NID.close_rw_tasks(write_task, read_task)

    # If there is only one sample per pixel, we skip the averaging process
    if samples_per_step == 1:
        # Reshape to a numpy 2D array (pixels_number x pixels_number)
        image_array = np.array(raw_data).reshape(pixels_number, pixels_number)

    else:
        image_array = ImageProcessing.average(raw_data, samples_per_step, pixels_number)

    # Reverse rows alternatively
    image_array = ImageProcessing.reverse_alternate_rows(image_array)

    # Normalize the values between 0 and 255
    image_array = ImageProcessing.normalize(image_array)

    return image_array.astype(np.uint8)


def video_init(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read):
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

    # Structure datas to write
    data_to_write = np.array([complete_horizontal_staircase, vertical_staircase])

    # Write both signal in one task and read with another
    write_task, read_task = NID.configure_video_tasks(channel_lr, channel_ud, channel_read, min_tension, max_tension,
                                                      sampling_frequency, complete_horizontal_staircase,
                                                      total_samples_to_read, data_to_write)

    return write_task, read_task, timeout, total_samples_to_read


def video_instance(write_task, read_task, timeout, pixels_number, total_samples_to_read):
    # Create a StreamWriter for the analog outputs
    raw_data = NID.quick_write_and_read(write_task, read_task, total_samples_to_read, timeout)

    # Reshape to a numpy 2D array (pixels_number x pixels_number)
    image_array = np.array(raw_data).reshape(pixels_number + 2, pixels_number + 2)

    # To avoid weird behaviour we delete the first row of the image twice
    image_array = ImageProcessing.remove_two_columns(image_array)

    # Normalize the values between 0 and 255
    image_array = ImageProcessing.normalize(image_array)

    return image_array.astype(np.uint8)


def video_stop(write_task, read_task):
    # Stop the tasks
    NID.close_rw_tasks(write_task, read_task)
