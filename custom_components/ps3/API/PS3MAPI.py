import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import quote

from . import endpoints
from .exceptions import SensorError, NotificationError, FanError, RequestError, TempError, PlaybackError, DeviceOffError, LockError

class PS3MAPIWrapper:
    def __init__(self, ip: str):
        self.ip = ip
        self._state = None
        self._cpu_temp = None
        self._rsx_temp = None
        self._fan_speed = None
        self._fan_mode = None
        self._target_temp = None
        self._media_session = None
        self._games = None
        self._mounted_gamefile = None
        self._fan_modes_mapping = {
            'SYSCON': 'SYSCON',
            'Manual': 'Manual',
            'MAX': 'Dynamic',
            'AUTO': 'Auto'
        }
        self._lock = asyncio.Lock()
        self._update_done = asyncio.Event()

    def slow_server_request(evaluator, func_arg_idx = None, timeout = 30):
        def decorator(func):
            async def wrapper(self, *args, **kwargs):

                async def wait_with_timeout(self, evaluator, *func_args):
                    while not evaluator(self, *func_args):
                        await self._update_done.wait()

                if self._lock.locked():
                    raise LockError("Waiting for other request to complete")
                
                else:
                    async with self._lock:
                        await func(self, *args, **kwargs)
                        try:
                            if func_arg_idx is not None:
                                await asyncio.wait_for(wait_with_timeout(self, evaluator, args[func_arg_idx]), timeout)
                            else:
                                await asyncio.wait_for(wait_with_timeout(self, evaluator), timeout)
                        except asyncio.TimeoutError:
                            raise SensorError("Could not update sensors after request")

            return wrapper
        return decorator

    async def _update(self):
        endpoint_temps_fan = f"http://{self.ip}/cpursx.ps3"
        endpoint_games = f"http://{self.ip}/index.ps3"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint_games, timeout = 5) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        game_names = soup.select('div[class="gn"] a')
                        game_links = soup.select('div[class="ic"] a')
                        if game_names and game_links:
                            self._games = {name.text: link['href'] for name, link in zip(game_names, game_links)}
                    else:
                        self._games = None
                        raise SensorError(f"Unexpected response code: {response.status}")
                    
                await asyncio.sleep(0)

                async with session.get(endpoint_temps_fan, timeout = 5) as response:
                    if response.status == 200:
                        self._state = "On"
                        soup = BeautifulSoup(await response.text(), 'html.parser')

                        temperature_text = soup.find('a', class_='s', href = '/cpursx.ps3?up').text
                        self._cpu_temp = float(temperature_text.split(': ')[1].split('°C')[0])
                        self._rsx_temp = float(temperature_text.split(': ')[-1].split('°C')[0])
                        fan_speed_text = soup.find('a', class_='s', href = '/cpursx.ps3?mode').text
                        self._fan_speed = int(fan_speed_text.split(': ')[1].split('%')[0])

                        for substring, fan_mode in self._fan_modes_mapping.items():
                            if substring in temperature_text:
                                self._fan_mode = fan_mode
                                break
                        else:
                            raise SensorError("Fan mode sensor does not work")
                        
                        if self._fan_mode == 'Dynamic':
                            self._target_temp = float(temperature_text.split(': ')[2].split('°C')[0])
                        else:
                            self._target_temp = None

                        game_session_tags = soup.select('span[style="position:relative;top:-20px;"] h2 a')
                        playback_state = soup.find('label', title = 'Play')
                        if game_session_tags and playback_state:
                            self._media_session = {'media_type': 'game', 
                                                   'game_id': game_session_tags[0].text, 
                                                   'game_title': game_session_tags[1].text, 
                                                   'playback_time': playback_state.next_sibling, 
                                                   'image': game_session_tags[2].find('img')['src']
                                                   }
                        elif playback_state:
                            self._media_session = {'media_type': 'media', 'playback_time': playback_state.next_sibling}
                        else:
                            self._media_session = None

                        gamefile_tags = soup.select('font[size="3"] a')
                        if gamefile_tags:
                            self._mounted_gamefile = gamefile_tags[-1]['href']
                        else:
                            self._mounted_gamefile = None

                    else:
                        self._state = None
                        self._cpu_temp = None
                        self._rsx_temp = None
                        self._fan_speed = None
                        self._fan_mode = None
                        self._target_temp = None
                        self._media_session = None
                        self._mounted_gamefile = None
                        raise SensorError(f"Unexpected response code: {response.status}")
                    
            self._update_done.set()
            self._update_done.clear()

        except (asyncio.TimeoutError, aiohttp.client_exceptions.ServerDisconnectedError):
            self._state = "Off"
            self._cpu_temp = None
            self._rsx_temp = None
            self._fan_speed = None
            self._fan_mode = None
            self._target_temp = None
            self._media_session = None
            self._games = None
            self._mounted_gamefile = None

            self._update_done.set()
            self._update_done.clear()
        except SensorError:
            raise

    async def _call_service(self, endpoint, timeout, **kwargs):
        try:
            endpoint_url = endpoint.format(ip = self.ip, **kwargs)
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint_url, timeout = timeout) as response:
                    if response.status == 200:
                        pass
                    else:
                        raise RequestError(f"Unexpected response code: {response.status}")
        except (asyncio.TimeoutError, aiohttp.client_exceptions.ServerDisconnectedError):
            raise DeviceOffError("Device turned off")
        except Exception:
            raise

    async def update(self):
        try:
            await self._update()
        except SensorError:
            raise
        except Exception as e:
            raise SensorError(e)

    async def send_notification(self, notification: str, icon: int = 1, sound: int = 1):
        notification_url = quote(notification)
        try:
            await self._call_service(endpoints.NOTIFICATION, timeout = 5, notification_url = notification_url, icon = icon, sound = sound)
        except Exception as e:
            raise NotificationError(e)

    async def set_fan_mode(self, fan_mode: str):
        url_substrings = {'SYSCON': 'fan=0', 'Manual': 'fan=1;/cpursx.ps3?man', 'Dynamic': 'fan=1;/cpursx.ps3?man;/cpursx.ps3?mode', 'Auto': 'fan=2'}
        try:
            fan_mode_substring = url_substrings[fan_mode]
            await self._call_service(endpoints.FAN_MODE, timeout = 5, fan_mode_substring = fan_mode_substring)
        except Exception as e:
            raise FanError(e)

    async def set_target_temp(self, target_temp: float):
        try:
            await self._call_service(endpoints.TARGET_TEMP, timeout = 5, target_temp = target_temp)
        except Exception as e:
            raise TempError(e)

    async def set_fan_speed(self, fan_speed: int):
        try:
            await self._call_service(endpoints.FAN_SPEED, timeout = 5, fan_speed = fan_speed)
        except Exception as e:
            raise FanError(e)

    @slow_server_request(evaluator = lambda self: self._media_session == None)
    async def quit_playback(self):
        try:
            await self._call_service(endpoints.QUIT_PLAYBACK, timeout = 30)
            await self._update()
        except Exception as e:
            raise PlaybackError(e)

    @slow_server_request(evaluator = lambda self: self._media_session != None)
    async def start_playback(self):
        try:
            await self._call_service(endpoints.START_PLAYBACK, timeout = 30)
        except Exception as e:
            raise PlaybackError(e)

    @slow_server_request(evaluator = lambda self, func_value: self._mounted_gamefile == self._games[func_value], func_arg_idx = 0)
    async def mount_gamefile(self, game: str):
        try:
            gamefile = self._games[game]
            await self._call_service(endpoints.MOUNT_GAMEFILE, timeout = 30, gamefile = gamefile)
        except Exception as e:
            raise PlaybackError(e)

    @slow_server_request(evaluator = lambda self: self._mounted_gamefile == None)
    async def mount_disc(self):
        try:
            await self._call_service(endpoints.MOUNT_DISC, timeout = 30)
        except Exception as e:
            raise PlaybackError(e)
    
    async def press_button(self, button: str):
        try:
            await self._call_service(endpoints.PRESS_BUTTON, timeout = 5, button = button)
        except Exception as e:
            raise RequestError(e)

    async def shutdown(self):
        try:
            await self._call_service(endpoints.SHUTDOWN, timeout = 30)
        except Exception as e:
            raise RequestError(e)

    async def wait_for_xmb(self):
        try:
            await self._call_service(endpoints.WAIT_FOR_XMB, timeout = 60)
        except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
            raise RequestError("XMB not available")
        except Exception:
            raise

    @property
    def state(self):
        return self._state

    @property
    def cpu_temp(self):
        return self._cpu_temp

    @property
    def rsx_temp(self):
        return self._rsx_temp
    
    @property
    def fan_speed(self):
        return self._fan_speed
    
    @property
    def fan_mode(self):
        return self._fan_mode
    
    @property
    def target_temp(self):
        return self._target_temp
    
    @property
    def fan_modes(self):
        return list(self._fan_modes_mapping.values())
    
    @property
    def media_session(self):
        return self._media_session
    
    @property
    def games(self):
        return self._games
    
    @property
    def mounted_gamefile(self):
        return self._mounted_gamefile