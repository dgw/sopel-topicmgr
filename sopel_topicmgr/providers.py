from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import pkg_resources

from sopel.tools import get_logger

if TYPE_CHECKING:
    from typing import Mapping

    from .managers import TopicManager


LOGGER = get_logger('topicmgr')


class PropertyProvider:
    def __init__(self, name: str):
        self.__name = name
        self.__properties: dict[str, str] = self.defaults()

    def defaults(self) -> dict[str, str]:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.__name

    @property
    def properties(self) -> Mapping[str, str]:
        return MappingProxyType(self.__properties)

    def setup(self, manager: TopicManager):
        LOGGER.info("Setting up %s property provider", self.name)
        for name, default in self.properties.items():
            LOGGER.debug("Registering %s.%s property", self.name, name)
            manager.register_property(self.name, name)
            LOGGER.debug("Setting default for %s.%s property to %r", self.name, name, default)
            manager.update_property(self.name, name, default)
