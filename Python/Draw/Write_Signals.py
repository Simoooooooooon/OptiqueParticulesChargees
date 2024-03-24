from . import Image_to_Signals
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_writers import AnalogMultiChannelWriter
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def config_task(task, channel_lr, channel_ud, signal_lr, signal_ud, sampling_frequency):
    task.ao_channels.add_ao_voltage_chan(channel_lr, min_val=-10, max_val=10)
    task.ao_channels.add_ao_voltage_chan(channel_ud, min_val=-10, max_val=10)
    task.timing.cfg_samp_clk_timing(rate=sampling_frequency, sample_mode=AcquisitionType.CONTINUOUS)
    data_to_write = np.array([signal_lr, signal_ud])

    # Create a StreamWriter for the analog outputs
    writer = AnalogMultiChannelWriter(task.out_stream)

    # Write both signals at the same time
    writer.write_many_sample(data_to_write)


def write_signals_to_NI(channel_lr, channel_ud, signal_lr, signal_ud, sampling_frequency, iterations, timeout,
                        required_time):
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


def ajout_sinus(signal_lr, signal_ud, amplitude, frequence_relative):
    # Nombre total d'échantillons dans les signaux
    n_echantillons = len(signal_lr)  # Supposant que signal_lr et signal_ud ont la même longueur

    # Générer le signal sinusoidal pour chaque échantillon
    sinus = amplitude * np.sin(2 * np.pi * frequence_relative * np.arange(n_echantillons))

    # Ajouter le sinus aux signaux existants
    signal_lr += sinus
    signal_ud += sinus

    return signal_lr, signal_ud


if __name__ == "__main__":
    iterations = 2
    sampling_frequency = 250000

    Objects = Image_to_Signals.Image_to_Objects('INSA.png', 20)
    print("Objects done")

    Objects_path = Image_to_Signals.Objects_path(Objects)
    print("Objects path done")

    signal_lr, signal_ud = Image_to_Signals.Path_To_Signal(Objects)
    print("Signals done")

    signal_lr, signal_ud = ajout_sinus(signal_lr, signal_ud, 0.01, 500000)

    timeout = len(signal_lr) / sampling_frequency + 1

    required_time = timeout * iterations
    print(f"Required time : {required_time} s")

    write_signals_to_NI('Dev1/ao0', 'Dev1/ao1', signal_lr, signal_ud, sampling_frequency, iterations, timeout,
                        required_time)

    print("Signals written")
