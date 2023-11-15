import requests

class SensorError(Exception):
    pass

class PS3MAPIWrapper:
    def __init__(self, ip: str ):
        self.ip = ip

    def _get_sensor_status(self):
        endpoint = f"http://{self.ip}/index.ps3"

        try:
            response = requests.get(endpoint, timeout=5)  # Set a timeout value in seconds
            return response.status_code
        except requests.exceptions.Timeout:
            return None 
        except requests.exceptions.RequestException as e:
            raise SensorError(f"Error checking sensor status: {e}")

    @property
    def state(self):
        try:
            status_code = self._get_sensor_status()
            
            # If the status code is not None, it's on; otherwise, it's off
            return "On" if status_code == 200 else "Off"
        except SensorError as e:
            print(f"Error getting sensor state: {e}")
            return "Unknown"     



test = PS3MAPIWrapper("192.168.1.59")
print(test.state)