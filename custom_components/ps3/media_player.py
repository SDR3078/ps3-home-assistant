from __future__ import annotations

import logging
import time

from homeassistant.components.media_player import MediaPlayerEntity, MediaType, MediaPlayerState, MediaPlayerEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, ENTRIES
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
            MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.PLAY_MEDIA
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
                return media_session.get("playback_time")
        return None
    
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
    def icon(self):
        return self._icon
    
    async def async_play_media(self, media_type, media_id):
        try:
            await self.coordinator.wrapper.start_playback()
        except RequestError as e:
            _LOGGER.error(e)
        
        await self.coordinator.async_refresh()

    async def async_media_stop(self):
        try:
            await self.coordinator.wrapper.quit_playback()
        except RequestError as e:
            _LOGGER.error(e)
        
        await self.coordinator.async_refresh()