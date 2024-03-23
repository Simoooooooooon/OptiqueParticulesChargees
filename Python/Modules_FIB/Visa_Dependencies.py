import pyvisa
import time


# Lists the available VISA resources.
def resources_list():
    """
    Lists the available VISA resources.

    This function retrieves a list of available VISA resources, such as connected instruments,
    using the PyVISA library.

    Returns:
        list: A list of strings representing the available VISA resources.
    """

    try:
        rm = pyvisa.ResourceManager()
        items = rm.list_resources()  # Lists the connected VISA devices
        rm.close()
        return items
    except Exception as e:
        raise Exception(f"\nFunction resources_list returned : {e}")


# Power supply object
class PowerSupply:
    """
    A class to handle the operations related to the GPP4323 power supply.

    This class provides functionalities to connect to, configure, and control the GPP4323 power supply
    using the PyVISA library. It allows setting the tension, and disconnecting from the power supply.

    Attributes:
        port (str): The port name where the power supply is connected.
        device (pyvisa.Resource): A PyVISA resource representing the power supply.
    """

    def __init__(self, port):
        """
        Initializes the PowerSupply object with the specified port.

        Parameters:
            port (str): The port name where the power supply is connected.
        """

        self.port = port
        self.device = None

    def connect(self):
        """
        Connects to the power supply, checks for a specific identification, and initializes its settings if matched.

        This method establishes a connection to the power supply, queries its identification, and if the identification
        contains "GPP", sets initial current and voltage settings. It prints the device's identification string if it
        contains "GPP".

        Returns:
            Exception: Any exception raised during connection, if any.
        """

        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(self.port)
            idn_response = self.device.query('*IDN?')

            if "GPP" in idn_response:
                self.device.write(f'ISET1:0.03')
                self.device.write(f'ISET2:0.03')
                self.device.write(f'ISET4:0.03')
                self.device.write(f'VSET1:32')
                self.device.write(f'VSET2:32')
                self.device.write(f'VSET3:0')
                self.device.write(f'VSET4:0')
                self.device.write(f':ALLOUTON')
            else:
                raise Exception(f"\nDevice not recognized. IDN: {idn_response}")
        except Exception as e:
            raise Exception(f"\nFunction connect in PowerSupply class returned : {e}")

    def set_tension(self, tension):
        """
        Sets the tension of the power supply to the specified value.

        Parameters:
            tension (float): The tension value to set on the power supply.
        """

        try:
            if self.device:
                self.device.write(f'VSET4:{tension}')
        except Exception as e:
            raise Exception(f"\nFunction set_tension in PowerSupply class returned : {e}")

    def disconnect(self):
        """
        Disconnects the power supply and resets its settings.

        This method turns off all outputs and closes the connection to the power supply.
        """

        try:
            if self.device:
                self.device.write(f'ISET1:0')
                self.device.write(f'ISET2:0')
                self.device.write(f'ISET4:0')
                self.device.write(f'VSET1:0')
                self.device.write(f'VSET2:0')
                self.device.write(f'VSET3:0')
                self.device.write(f'VSET4:0')
                self.device.write(f':ALLOUTOFF')
                time.sleep(0.1)
                self.device.close()
        except Exception as e:
            raise Exception(f"\nFunction disconnect in PowerSupply class returned : {e}")
