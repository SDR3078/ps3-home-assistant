import asyncio
import aiohttp

class SensorError(Exception):
    pass

class PS3MAPIWrapper:
    def __init__(self, ip: str):
        self.ip = ip
        self._state = None

    async def _update(self):
        endpoint = f"http://{self.ip}/index.ps3"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    if response.status == 200:
                        self._state = "On"
                    else:
                        self._state = None
                        raise SensorError(f"Unexpected response code: {response.status}")
        except asyncio.TimeoutError:
            self._state = "Off"
        except SensorError as e:
            print(f"SensorError: {e}")

    async def update(self):
            await self._update()

    @property
    def state(self):
        return self._state