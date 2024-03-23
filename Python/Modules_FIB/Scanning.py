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
    try:
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

    except Exception as e:
        raise Exception(f"\nFunction rise_scanning returned : {e}")


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

    try:
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

    except Exception as e:
        raise Exception(f"\nFunction triangle_scanning returned : {e}")


def video_init(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read):
    """
    Initializes the configuration for video acquisition, including creating the staircase signals for scanning
    and setting up read and write tasks. It adjusts the number of pixels to account for synchronization issues
    at the start and converts time units appropriately.

    Parameters:
        time_per_pixel (int): Time in microseconds allocated for each pixel.
        sampling_frequency (int): The frequency at which samples are acquired.
        pixels_number (int): The total number of pixels in one dimension of the square video frame.
        channel_lr (str): The channel used for horizontal (left-right) scanning.
        channel_ud (str): The channel used for vertical (up-down) scanning.
        channel_read (str): The channel used for reading the video signal.

    Returns:
        tuple: Contains the write task, read task, timeout for the operation, and the total number of samples to read.
    """

    try:
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

    except Exception as e:
        raise Exception(f"\nFunction video_init returned : {e}")


def video_instance(write_task, read_task, timeout, pixels_number, total_samples_to_read):
    """
    Captures a single instance of video data by writing to and reading from the configured tasks. It processes
    the raw data into a 2D image array, normalizes the image values, and corrects for initial acquisition
    synchronization issues.

    Parameters:
        write_task: The task used for writing the scan signals.
        read_task: The task used for reading the video data.
        timeout (float): The maximum time to wait for the read operation to complete.
        pixels_number (int): The number of pixels in one dimension of the video frame, adjusted for synchronization.
        total_samples_to_read (int): The total number of samples to be read from the read task.

    Returns:
        numpy.ndarray: The processed 2D image array.
    """

    try:
        # Create a StreamWriter for the analog outputs
        raw_data = NID.quick_write_and_read(write_task, read_task, total_samples_to_read, timeout)

        # Reshape to a numpy 2D array (pixels_number x pixels_number)
        image_array = np.array(raw_data).reshape(pixels_number + 2, pixels_number + 2)

        # To avoid weird behaviour we delete the first row of the image twice
        image_array = ImageProcessing.remove_two_columns(image_array)

        # Normalize the values between 0 and 255
        image_array = ImageProcessing.normalize(image_array)

        return image_array.astype(np.uint8)

    except Exception as e:
        raise Exception(f"\nFunction video_instance returned : {e}")


def video_stop(write_task, read_task):
    """
    Stops and closes the write and read tasks used for video acquisition, effectively terminating the acquisition
    process.

    Parameters:
        write_task: The task used for writing the scan signals.
        read_task: The task used for reading the video data.
    """

    try:
        # Stop the tasks
        NID.close_rw_tasks(write_task, read_task)

    except Exception as e:
        raise Exception(f"\nFunction video_stop returned : {e}")
