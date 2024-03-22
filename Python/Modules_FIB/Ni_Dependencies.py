import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration, Edge
from nidaqmx.stream_writers import AnalogMultiChannelWriter


# Elementary ni functions
###############################################################################
def ni_cards_system():
    """
    Retrieve the local NI DAQmx system information.

    This function returns an object representing the local NI DAQmx system,
    which contains information about the installed NI DAQmx devices and
    their properties.

    Returns:
    nidaqmx.system.System: An object representing the local NI DAQmx system.
    """

    return nidaqmx.system.System.local()


def ni_cards_device(port_dev):
    """
    Retrieve information about a specific NI DAQmx device.

    This function retrieves information about the NI DAQmx device specified
    by the given port or device name.

    Args:
    port_dev (str): The port or device name of the NI DAQmx device.

    Returns:
    nidaqmx.system.Device: An object representing the specified NI DAQmx device.
    """

    return nidaqmx.system.Device(port_dev)


def close_rw_tasks(write_task, read_task):
    """
   Close nidaqmx tasks.

   This function closes the nidaqmx tasks for reading and writing.

   Args:
       write_task (nidaqmx.Task): The task configured for writing scanning signals.
       read_task (nidaqmx.Task): The task configured for reading the input signal.
   """

    read_task.close()
    write_task.close()


###############################################################################
# Tasks configurations

def initial_voltage_setting(min_tension, max_tension, channel_ud):
    """
    Configures the initial voltage for a given channel.

    This function configures a task to write an initial voltage to a specified analog output channel.
    The task is created, configured, and the maximum voltage is written to the channel. The task is
    then started to apply the voltage, and immediately stopped.

    Args:
        min_tension (float): The minimum voltage that can be output by the channel.
        max_tension (float): The maximum voltage that can be output by the channel.
        channel_ud (str): The name of the analog output channel to configure.

    Returns:
        None
    """
    with nidaqmx.Task() as init_task:
        init_task.ao_channels.add_ao_voltage_chan(channel_ud, min_val=min_tension, max_val=max_tension)
        init_task.write(max_tension)
        init_task.start()
        init_task.stop()
        init_task.close()


def configure_tasks(channel_lr, channel_ud, channel_read, min_tension, max_tension,
                    sampling_frequency, complete_horizontal_staircase, total_samples_to_read):
    """
    Configures and returns tasks for writing and reading signals.

    This function configures two separate tasks: one for writing scanning signals (both
    horizontal and vertical), and another for reading the corresponding input signal. The
    analog output channels and the analog input channel are configured with the specified
    minimum and maximum voltages. The tasks are configured with the provided sampling
    frequency and scanning signals.

    Args:
        channel_lr (str): The name of the analog output channel for left-right scanning.
        channel_ud (str): The name of the analog output channel for up-down scanning.
        channel_read (str): The name of the analog input channel for reading the signal.
        min_tension (float): The minimum voltage that can be output by the analog output channels.
        max_tension (float): The maximum voltage that can be output by the analog output channels.
        sampling_frequency (float): The sampling frequency for data acquisition, in Hz.
        complete_horizontal_staircase (numpy.array): The complete scanning signal for left-right scanning.
        total_samples_to_read (int): The total number of samples to read during data acquisition.

    Returns:
        tuple: A tuple containing two nidaqmx task objects configured for writing and reading signals.

    """
    try:
        write_task = nidaqmx.Task()
        read_task = nidaqmx.Task()

        # Channels configuration
        write_task.ao_channels.add_ao_voltage_chan(channel_lr, min_val=min_tension, max_val=max_tension)
        write_task.ao_channels.add_ao_voltage_chan(channel_ud, min_val=min_tension, max_val=max_tension)
        read_task.ai_channels.add_ai_voltage_chan(channel_read, min_val=min_tension, max_val=max_tension,
                                                  terminal_config=TerminalConfiguration.DIFF)

        # Timing configuration
        write_task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.FINITE,
                                              samps_per_chan=len(complete_horizontal_staircase))
        read_task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=total_samples_to_read)

        # Trigger the read task at the start of the write task
        read_trigger_source = '/' + channel_lr.split('/')[0] + '/ao/StartTrigger'
        read_task.triggers.start_trigger.cfg_dig_edge_start_trig(read_trigger_source, trigger_edge=Edge.RISING)

    except Exception as e:
        print("Error while task configuration:", e)

    return write_task, read_task


def configure_video_tasks(channel_lr, channel_ud, channel_read, min_tension, max_tension,
                          sampling_frequency, complete_horizontal_staircase, total_samples_to_read, data_to_write):
    """
    Configures the necessary NI-DAQmx tasks for video acquisition, including setting up the analog output channels
    for scanning and the analog input channel for data acquisition. This function prepares the system for
    synchronized reading and writing operations, essential for acquiring video data.

    Parameters: channel_lr (str): The identifier for the left-right scanning channel. channel_ud (str): The
    identifier for the up-down scanning channel. channel_read (str): The identifier for the channel from which to
    read the video signal. min_tension (float): The minimum voltage value for the scanning signals. max_tension (
    float): The maximum voltage value for the scanning signals. sampling_frequency (int): The sampling frequency for
    both reading and writing operations. complete_horizontal_staircase (numpy.ndarray): The precomputed staircase
    signal for horizontal scanning. total_samples_to_read (int): The total number of samples to be read, determining
    the duration of the read task. data_to_write (numpy.ndarray): The array containing both the horizontal and
    vertical staircase signals to be written.

    Returns:
        tuple: A tuple containing the configured write and read tasks ready for execution.
    """

    try:
        write_task = nidaqmx.Task()
        read_task = nidaqmx.Task()

        # Channels configuration
        write_task.ao_channels.add_ao_voltage_chan(channel_lr, min_val=min_tension, max_val=max_tension)
        write_task.ao_channels.add_ao_voltage_chan(channel_ud, min_val=min_tension, max_val=max_tension)
        read_task.ai_channels.add_ai_voltage_chan(channel_read, min_val=min_tension, max_val=max_tension,
                                                  terminal_config=TerminalConfiguration.DIFF)

        # Timing configuration
        write_task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.FINITE,
                                              samps_per_chan=len(complete_horizontal_staircase))
        read_task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=total_samples_to_read)

        # Trigger the read task at the start of the write task
        read_trigger_source = '/' + channel_lr.split('/')[0] + '/ao/StartTrigger'
        read_task.triggers.start_trigger.cfg_dig_edge_start_trig(read_trigger_source, trigger_edge=Edge.RISING)

        # Create a StreamWriter for the analog outputs
        writer = AnalogMultiChannelWriter(write_task.out_stream)

        # Write both signals at the same time
        writer.write_many_sample(data_to_write)

    except Exception as e:
        print("Error while task configuration:", e)

    return write_task, read_task


###############################################################################
# Writing & Reading functions

def write_and_read(write_task, read_task, data_to_write, total_samples_to_read, timeout):
    """
   Writes scanning signals and reads the input signal simultaneously.

   This function writes the provided scanning signals to the analog output channels of the write task.
   It then starts both the write and read tasks to write and read the signals simultaneously. The
   read data is returned raw after acquisition.

   Args:
       write_task (nidaqmx.Task): The task configured for writing scanning signals.
       read_task (nidaqmx.Task): The task configured for reading the input signal.
       data_to_write (numpy.array): The data to be written to the analog output channels.
       total_samples_to_read (int): The total number of samples to read during data acquisition.
       timeout (float): The maximum timeout for data acquisition, in seconds.

   Returns:
       numpy.array: The raw data read from the analog input channel.
   """

    try:
        # Create a StreamWriter for the analog outputs
        writer = AnalogMultiChannelWriter(write_task.out_stream)

        # Write both signals at the same time
        writer.write_many_sample(data_to_write)

        # Start the tasks
        read_task.start()
        write_task.start()

        # Read the data for the entire image
        raw_data = read_task.read(number_of_samples_per_channel=total_samples_to_read, timeout=timeout)

        # Wait for the end of the tasks
        write_task.wait_until_done(timeout=timeout)

        write_task.stop()
        read_task.stop()

    except Exception as e:
        print("Error while Reading&Writing:", e)

    return raw_data


def quick_write_and_read(write_task, read_task, total_samples_to_read, timeout):
    """
   Start and stop the writing and the reading task.

   This function starts both the write and read tasks to write and read the signals simultaneously. The
   read data is returned raw after acquisition.

   Args:
       write_task (nidaqmx.Task): The task configured for writing scanning signals.
       read_task (nidaqmx.Task): The task configured for reading the input signal.
       total_samples_to_read (int): The total number of samples to read during data acquisition.
       timeout (float): The maximum timeout for data acquisition, in seconds.

   Returns:
       numpy.array: The raw data read from the analog input channel.
   """
    try:
        # Start the tasks
        read_task.start()
        write_task.start()

        # Read the data for the entire image
        raw_data = read_task.read(number_of_samples_per_channel=total_samples_to_read, timeout=timeout)

        # Wait for the end of the tasks
        write_task.wait_until_done(timeout=timeout)

        write_task.stop()
        read_task.stop()

        return raw_data

    except Exception as e:
        print("Error while QuickReading&Writing:", e)
