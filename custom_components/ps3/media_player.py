from __future__ import annotations

import logging
import asyncio
import aiohttp

from homeassistant.components.media_player import MediaPlayerEntity, MediaType, MediaPlayerState, MediaPlayerEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.dt import utcnow

from .const import DOMAIN, ENTRIES, XMB_SOURCE, SCRIPT_DOMAIN, TURN_ON_SCRIPT, MEDIA_PLAYER_KEY, NAME, MANUFACTURER
from .helpers import request

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [MediaPlayer(hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"], config_entry.data.get(TURN_ON_SCRIPT), hass.services, config_entry.data.get('mac_address'))]
    )

class MediaPlayer(MediaPlayerEntity, CoordinatorEntity):
     
    def __init__(self, coordinator, turn_on_script, service_registry, mac_address):
        super().__init__(coordinator)
        self._turn_on_script = turn_on_script
        self._service_registry = service_registry
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.TURN_OFF
            | (MediaPlayerEntityFeature.TURN_ON if turn_on_script is not None else 0)
        )
        self._mac_address = mac_address

    @property
    def name(self):
        return "PS3"
    
    @property
    def media_content_id(self):
        if self.coordinator.data is not None:
            media_session = self.coordinator.data.get("media_session")
            if media_session and media_session.get("media_type") == "game":
                return media_session.get("game_id")
        return None
    
    @property
    def media_title(self):
        if self.coordinator.data is not None:
            media_session = self.coordinator.data.get("media_session")
            if media_session and media_session.get("media_type") == "game":
                return media_session.get("game_title")
        return None
    
    @property
    def content_type(self):
        if self.coordinator.data is not None:
            media_session = self.coordinator.data.get("media_session")
            if media_session:
                if media_session.get("media_type") == "game":
                    return MediaType.GAME
                elif media_session.get("media_type") == "media":
                    return MediaType.MOVIE
        return None
    
    @property
    def media_position(self):
        if self.coordinator.data is not None:
            media_session = self.coordinator.data.get("media_session")
            if media_session:
                playback_time = media_session.get("playback_time")
                h, m, s = playback_time.split(":")
                seconds = int(h) * 3600 + int(m) * 60 + int(s)
                return seconds
        return None
    
    @property
    def media_duration(self):
        if self.coordinator.data is not None:
            media_session = self.coordinator.data.get("media_session")
            if media_session:
                playback_time = media_session.get("playback_time")
                h, m, s = playback_time.split(":")
                seconds = int(h) * 3600 + int(m) * 60 + int(s)
                return seconds
        return None
    
    @property
    def media_position_updated_at(self):
        return utcnow()
    
    @property
    def state(self):
        if self.coordinator.data is not None and self.coordinator.data.get('state') == 'On':
            media_session = self.coordinator.data.get("media_session")
            if media_session:
                return MediaPlayerState.PLAYING
            else:
                return MediaPlayerState.IDLE
        return MediaPlayerState.OFF
    
    @property
    def source_list(self):
        if self.coordinator.data is not None:
            games_dict = self.coordinator.data.get("games")
            if games_dict is not None:
                games_list = list(games_dict.keys())
                games_list.append(XMB_SOURCE)
                return games_list
            else:
                return [XMB_SOURCE]
        return None
    
    @property
    def source(self):
        if self.coordinator.data is not None:
            mounted_gamefile = self.coordinator.data.get("mounted_gamefile")
            if mounted_gamefile is not None:
                games_dict = {link: name for name, link in self.coordinator.data.get("games").items()}
                return games_dict[mounted_gamefile]
            return XMB_SOURCE
        return None
    
    @property
    def media_image_url(self):
        if self.coordinator.data is not None:
            media_session = self.coordinator.data.get("media_session")
            if media_session:
                if media_session.get("media_type") == "game":
                    return f"http://{self.coordinator.ip_address}{media_session.get('image')}"
        return None
    
    @property
    def icon(self):
        if self.state == MediaPlayerState.OFF:
            return "mdi:controller-off"
        else:
            return "mdi:controller"
    
    @property
    def unique_id(self):
        return f"{self._mac_address}-{MEDIA_PLAYER_KEY}"
    
    @property
    def device_info(self):
        return DeviceInfo(
            identifiers = {
                (DOMAIN, self._mac_address)
            },
            name = NAME,
            model = NAME,
            manufacturer = MANUFACTURER,
            sw_version = self.coordinator.data.get("firmware_version")
        )
    
    @request
    async def async_media_play(self):
        await self.coordinator.wrapper.start_playback()

    @request
    async def async_media_stop(self):
        self.coordinator.update_from_memory = True
        await self.coordinator.wrapper.quit_playback()
        await self.coordinator.async_refresh()

    @request
    async def async_select_source(self, source):
        if source == XMB_SOURCE:
            await self.coordinator.wrapper.mount_disc()
        else:
            await self.coordinator.wrapper.mount_gamefile(source)
        _LOGGER.info("Game mounted!")

    @request
    async def async_turn_off(self):
        await self.coordinator.wrapper.shutdown()
        await self.coordinator.async_refresh()

    async def async_turn_on(self, timeout = 60):
        if self.coordinator.startup_lock.locked():
            raise ServiceValidationError(
                translation_domain = DOMAIN,
                translation_key = "starting_up"
            )

        else:
            async def wait_with_timeout(self):
                while True:
                    try:
                        await self.coordinator.wrapper.wait_for_xmb()
                        break
                    except Exception:
                        pass
            
            async with self.coordinator.startup_lock:
                await self._service_registry.async_call(SCRIPT_DOMAIN, self._turn_on_script, blocking = True)
                try:
                    await asyncio.wait_for(wait_with_timeout(self), timeout)
                except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as e:
                    raise HomeAssistantError(e)

            await self.coordinator.async_refresh()