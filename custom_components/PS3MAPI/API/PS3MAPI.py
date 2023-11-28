import asyncio
import aiohttp
from bs4 import BeautifulSoup

class SensorError(Exception):
    pass

class PS3MAPIWrapper:
    def __init__(self, ip: str):
        self.ip = ip
        self._state = None
        self._cpu_temp = None
        self._rsx_temp = None

    async def _update(self):
        endpoint_temps_fan = f"http://{self.ip}/cpursx.ps3"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint_temps_fan, timeout = 5) as response:
                    if response.status == 200:
                        self._state = "On"
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        temperature_text = soup.find('a', class_='s', href = '/cpursx.ps3?up').text
                        self._cpu_temp = temperature_text.split(': ')[1].split('°C')[0]
                        self._rsx_temp = temperature_text.split(': ')[3].split('°C')[0]
                    else:
                        self._state = None
                        self._cpu_temp = None
                        self._rsx_temp = None
                        raise SensorError(f"Unexpected response code: {response.status}")
        except asyncio.TimeoutError:
            self._state = "Off"
            self._cpu_temp = None
            self._rsx_temp = None
        except SensorError as e:
            print(f"SensorError: {e}")

    async def update(self):
        await self._update()

    @property
    def state(self):
        return self._state

    @property
    def cpu_temp(self):
        return self._cpu_temp

    @property
    def rsx_temp(self):
        return self._rsx_temp