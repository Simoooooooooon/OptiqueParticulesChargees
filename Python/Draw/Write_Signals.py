import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_writers import AnalogMultiChannelWriter
import numpy as np
import time


def config_task(task, channel_lr, channel_ud, signal_lr, signal_ud, sampling_frequency):
    """
    Configures a NI-DAQmx task for writing voltage signals to specified channels.

    This function sets up a DAQmx task to output analog voltage signals on two channels,
    typically representing Left-Right (LR) and Up-Down (UD) movements. It configures the
    channels for voltage output within a specified range and sets the sampling frequency
    for the signals. Finally, it writes the provided signal arrays to the channels.

    Parameters:
    - task (nidaqmx.Task): The DAQmx Task to be configured for analog output.
    - channel_lr (str): The name of the channel for outputting the LR signal.
    - channel_ud (str): The name of the channel for outputting the UD signal.
    - signal_lr (numpy.ndarray): The array containing the LR signal data.
    - signal_ud (numpy.ndarray): The array containing the UD signal data.
    - sampling_frequency (int): The frequency at which the signals should be sampled and output.

    Raises:
    - Exception: If an error occurs during task configuration or signal writing, an exception
      is raised with a message detailing the failure.
    """

    try:
        # Configure the channels
        task.ao_channels.add_ao_voltage_chan(channel_lr, min_val=-10, max_val=10)
        task.ao_channels.add_ao_voltage_chan(channel_ud, min_val=-10, max_val=10)
        task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.CONTINUOUS)
        data_to_write = np.array([signal_lr, signal_ud])

        # Create a StreamWriter for the analog outputs
        writer = AnalogMultiChannelWriter(task.out_stream)

        # Write both signals at the same time
        writer.write_many_sample(data_to_write)

    except Exception as e:
        raise Exception(f"\nCouldn't configure the writing task : {e}")


def reset(port):
    """
    Resets a NI-DAQmx device to its default configuration.

    This function attempts to reset a specified DAQ device identified by its port name.
    The reset operation returns the device to its default state, clearing any configurations
    or states that may have been previously set.

    Parameters:
    - port (str): The name of the device port to reset, as recognized by the NI-DAQmx system.

    Raises:
    - Exception: If the reset operation fails, an exception is raised with a message detailing
      the cause of the failure.
    """

    try:
        # Communicate and reset the device
        device = nidaqmx.system.System.local().devices[port]
        device.reset_device()

    except Exception as e:
        raise Exception(f"\nCouldn't reset the card : {e}")


def write_signals_to_NI(channel_lr, channel_ud, signal_lr, signal_ud, sampling_frequency, required_time):
    """
    Writes specified LR and UD signals to a NI-DAQmx device over a set duration.

    Initiates a task to write analog voltage signals to specified channels for controlling
    Left-Right and Up-Down movements. The function sets up the task with the provided channel
    names, signal data, and sampling frequency, then starts the task and maintains it for
    the duration specified by `required_time`. After the operation completes, the task is
    stopped and cleaned up.

    Parameters:
    - channel_lr (str): The name of the channel for the LR signal.
    - channel_ud (str): The name of the channel for the UD signal.
    - signal_lr (numpy.ndarray): The data array for the LR signal.
    - signal_ud (numpy.ndarray): The data array for the UD signal.
    - sampling_frequency (int): The sampling frequency for signal output.
    - iterations (int): The number of iterations to repeat the signal output.
                        This parameter is currently not used but included for future scalability.
    - timeout (float): The timeout for the operation, in seconds. Currently not used but included for
                       compatibility and future scalability.
    - required_time (float): The total duration to run the signal output, in seconds.

    Raises:
    - Exception: If any part of the signal writing process fails, an exception is raised with a
      detailed message of what went wrong.
    """

    try:
        start_time = time.time()  # Capture the start time
        with nidaqmx.Task() as task:
            config_task(task, channel_lr, channel_ud, signal_lr, signal_ud, sampling_frequency)

            # Start the task
            task.start()

            # Wait for the end of the tasks based on a custom time control
            while time.time() - start_time < required_time:
                time.sleep(0.1)  # Sleep for a short period to avoid busy waiting

            # Stop the task
            task.stop()

    except Exception as e:
        raise Exception(f"\nCouldn't write the signals to the card : {e}")

# TBD
'''def ajout_sinus(signal_lr, signal_ud, amplitude, frequence_relative):
    # Nombre total d'échantillons dans les signaux
    n_echantillons = len(signal_lr)

    # Générer le signal sinusoidal
    sinus = amplitude * np.sin(2 * np.pi * frequence_relative * np.arange(n_echantillons))

    # Ajouter le sinus aux signaux
    signal_lr += sinus
    signal_ud += sinus

    return signal_lr, signal_ud'''
