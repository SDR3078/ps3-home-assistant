import asyncio
import aiohttp

class SensorError(Exception):
    pass

class PS3MAPIWrapper:
    def __init__(self, ip: str):
        self.ip = ip
        self._state = None

    async def _update_state(self):
        endpoint = f"http://{self.ip}/index.ps3"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    if response.status == 200:
                        self._state = "On"
                    else:
                        self._state = "Unknown"
                        raise SensorError(f"Unexpected response code: {response.status}")
        except asyncio.TimeoutError:
            self._state = "Off"
        except SensorError as e:
            print(f"SensorError: {e}")

    async def update(self):
            await self._update_state()

    @property
    def state(self):
        return self._state
        
if __name__ == "__main__":
    async def main():
        ps3mapi = PS3MAPIWrapper("192.168.1.59")

        await ps3mapi.update()
        print(f"Initial state: {ps3mapi.state}")

        while True:
            await asyncio.sleep(10)
            await ps3mapi.update()
            print(f"Current state: {ps3mapi.state}")

    asyncio.run(main())