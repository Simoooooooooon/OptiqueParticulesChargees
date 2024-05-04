import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_writers import AnalogMultiChannelWriter
import numpy as np


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
        task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(signal_lr))
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
        Writes voltage signals to the NI-DAQmx card using specified channels.

        This function creates and configures a DAQmx task to write analog voltage signals for Left-Right (LR) and Up-Down (UD) movements to specified channels. It controls the timing and duration of the signal output based on the provided sampling frequency and the required operation time. The function handles task setup, execution, and teardown to ensure that the signals are output correctly.

        Parameters:
        - channel_lr (str): The name of the channel for outputting the LR signal.
        - channel_ud (str): The name of the channel for outputting the UD signal.
        - signal_lr (numpy.ndarray): The array containing the LR signal data.
        - signal_ud (numpy.ndarray): The array containing the UD signal data.
        - sampling_frequency (int): The frequency at which the signals should be sampled and output.
        - required_time (float): The maximum duration in seconds to wait for the task to complete before stopping.

        Raises:
        - Exception: If any part of the signal writing process fails, an exception is raised with a detailed error message.
        """

    try:
        with nidaqmx.Task() as task:
            config_task(task, channel_lr, channel_ud, signal_lr, signal_ud, sampling_frequency)

            # Start the task
            task.start()

            # Wait for the task to end
            task.wait_until_done(timeout=required_time)

            # Stop the task
            task.stop()

    except Exception as e:
        raise Exception(f"\nCouldn't write the signals to the card : {e}")
