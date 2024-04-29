from __future__ import annotations

import logging

from homeassistant.components.media_player import MediaPlayerEntity, MediaType, MediaPlayerState, MediaPlayerEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.dt import utcnow

from .const import DOMAIN, ENTRIES, XMB_SOURCE
from .API.PS3MAPI import RequestError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    async_add_entities(
        [MediaPlayer(hass.data[DOMAIN][ENTRIES][config_entry.entry_id]["coordinator"])]
    )

class MediaPlayer(MediaPlayerEntity, CoordinatorEntity):
    _attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )
     
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._icon = "mdi:controller"

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
        return self._icon
    
    async def async_media_play(self):
        try:
            await self.coordinator.wrapper.start_playback()
        except RequestError as e:
            _LOGGER.error(e)

    async def async_media_stop(self):
        try:
            await self.coordinator.wrapper.quit_playback()
        except RequestError as e:
            _LOGGER.error(e)
        
        await self.coordinator.async_refresh()

    async def async_select_source(self, source):
        try:
            if source == XMB_SOURCE:
                await self.coordinator.wrapper.mount_disc()
            else:
                await self.coordinator.wrapper.mount_gamefile(source)
            _LOGGER.info("Game mounted!")
        except RequestError as e:
            _LOGGER.error(e)