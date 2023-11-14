from __future__ import annotations

from types import MappingProxyType, SimpleNamespace
from typing import TYPE_CHECKING

import pkg_resources

from sopel.privileges import OP
from sopel.tools import get_logger
from sopel.tools.memories import SopelIdentifierMemory

from .providers import PropertyProvider

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Optional

    from sopel.bot import Sopel
    from sopel.tools.identifiers import Identifier


PROVIDERS_ENTRY_POINT = 'sopel_topicmgr.providers'

LOGGER = get_logger('topicmgr')


class TopicManager:
    def __init__(
        self,
        bot: Sopel,
    ):
        LOGGER.debug("Initializing TopicManager for bot %r", bot.settings.core.nick)
        self.__bot = bot
        self.__channels = SopelIdentifierMemory(
            identifier_factory=bot.make_identifier)
        self.__providers: dict[str, PropertyProvider] = {}
        self.__properties: dict[str, SimpleNamespace] = {}

        self.load_providers()
        self.initialize_providers()

    def __str__(self) -> str:
        return 'TopicManager<{}>'.format(self.__bot.settings.core.nick)

    def load_providers(self):
        if not self.__providers:
            LOGGER.debug("Loading property providers")
            entry_points = pkg_resources.iter_entry_points(
                PROVIDERS_ENTRY_POINT)
            self.__providers = {
                entry_point.name: self.load_provider(entry_point.name)
                for entry_point in entry_points
            }
        else:
            raise RuntimeError("Providers already loaded")

    def load_provider(self, name: str):
        entry_points = pkg_resources.iter_entry_points(
            PROVIDERS_ENTRY_POINT, name)

        try:
            entry_point = next(entry_points)
        except StopIteration as err:
            raise RuntimeError('Provider {} not found'.format(name)) from err

        LOGGER.debug("%s loading %s provider", self, name)

        actual_loader = entry_point.load()
        return actual_loader(name)

    def initialize_providers(self):
        for name, provider in self.__providers.items():
            if name in self.__properties:
                raise RuntimeError(
                    "Provider {} already registered".format(name)
                )
            self.__properties[name] = SimpleNamespace()
            provider.setup(self)

    def register_channel(self, channel: Identifier, mask: str):
        if channel in self.__channels:
            raise RuntimeError("Channel {} already registered".format(channel))
        self.__channels[channel] = ChannelManager(self.__bot, channel, mask)

    def update_channel_topic_mask(self, channel: Identifier, mask: str):
        if channel not in self.__channels:
            raise RuntimeError("Channel {} not registered".format(channel))
        self.__channels[channel].update_mask(mask)

    def unregister_channel(self, channel: Identifier):
        if channel not in self.__channels:
            raise RuntimeError("Channel {} not registered".format(channel))
        del self.__channels[channel]

    @property
    def properties(self) -> Mapping[str, SimpleNamespace]:
        return MappingProxyType(self.__properties)

    @staticmethod
    def get_key(provider: str, name: str):
        if not all((provider, name)):
            raise ValueError("Key parts must all be non-empty")
        return provider + '.' + name

    def register_property(self, provider: str, name: str):
        if provider not in self.__properties:
            raise RuntimeError(
                "Provider '{}' not registered".format(provider)
            )
        if hasattr(self.__properties[provider], name):
            raise RuntimeError(
                "Property '{}' for provider '{}' already registered"
                .format(name, provider)
            )
        setattr(self.__properties[provider], name, '')

    def update_property(self, provider: str, name: str, value: str):
        if provider not in self.__properties:
            raise RuntimeError(
                "Provider '{}' not registered".format(provider)
            )
        if not hasattr(self.__properties[provider], name):
            raise RuntimeError(
                "Property '{}' for provider '{}' already registered"
                .format(name, provider)
            )
        setattr(self.__properties[provider], name, value)

        for channel in self.__channels.values():
            channel.handle_prop_update(
                self.properties,
                self.get_key(provider, name),
            )

    def get_property(self, provider: str, name: str) -> str:
        if provider not in self.__properties:
            raise RuntimeError(
                "Provider '{}' not registered".format(provider)
            )
        if not hasattr(self.__properties[provider], name):
            raise RuntimeError(
                "Property '{}' for provider '{}' already registered"
                .format(name, provider)
            )
        return getattr(self.__properties[provider], name)

    def clear_property(self, provider: str, name: str):
        if provider not in self.__properties:
            raise RuntimeError(
                "Provider '{}' not registered".format(provider)
            )
        if not hasattr(self.__properties[provider], name):
            raise RuntimeError(
                "Property '{}' for provider '{}' already registered"
                .format(name, provider)
            )
        setattr(self.__properties[provider], name, '')

    def unregister_property(self, provider: str, name: str):
        if provider not in self.__properties:
            raise RuntimeError(
                "Provider '{}' not registered".format(provider)
            )
        if not hasattr(self.__properties[provider], name):
            raise RuntimeError(
                "Property '{}' for provider '{}' doesn't exist"
                .format(name, provider)
            )
        delattr(self.__properties[provider], name)


class ChannelManager:
    def __init__(
        self,
        bot: Sopel,
        channel: Identifier,
        mask: Optional[str] = None,
    ):
        self.__bot = bot
        self.__channel = channel
        self.__mask = mask

    def __str__(self) -> str:
        return 'ChannelManager<{}>'.format(self.__channel)

    @property
    def bot(self) -> Sopel:
        return self.__bot

    @property
    def channel(self) -> Identifier:
        return self.__channel

    @property
    def mask(self) -> Optional[str]:
        return self.__mask

    def update_mask(self, mask: str):
        self.__mask = mask

    def update_topic(self, properties: Mapping):
        if not self.mask:
            return

        if not self.bot.has_channel_privilege(self.channel, OP):
            self.bot.say(
                'I need permissions in {} to update the topic.'.format(
                    self.channel),
                self.bot.settings.core.owner,
            )
            return

        topic = self.mask.format(**properties)
        self.bot.write(('TOPIC', self.channel), topic)

    def handle_prop_update(
        self, properties: Mapping[str, str | Mapping[str, str]], changed: str
    ):
        if self.mask and ('%s' % changed) in self.mask:
            self.update_topic(properties)
