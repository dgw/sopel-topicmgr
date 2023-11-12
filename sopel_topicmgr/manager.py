from __future__ import annotations

from typing import TYPE_CHECKING

from sopel.privileges import AccessLevel

if TYPE_CHECKING:
    from sopel.bot import Sopel
    from sopel.tools.identifiers import Identifier


class WatchedDict(dict):
    def __init__(self, manager: TopicManager, defaults: dict[str, str]):
        super().__init__(defaults)
        self.__manager = manager

    def __setitem__(self, item, value):
        super().__setitem__(item, value)
        self.__manager.update_topic()


class TopicManager:
    def __init__(
        self,
        bot: Sopel,
        channel: Identifier,
        format: str,
        defaults: dict[str, str],
    ):
        self.__bot = bot
        self.__channel = channel
        self.__format = format
        self.__parts = WatchedDict(self, defaults)

    def __str__(self):
        return 'TopicManager<{}>'.format(self.__channel)

    @property
    def channel(self) -> Identifier:
        return self.__channel

    @property
    def format(self) -> str:
        return self.__format

    @property
    def parts(self) -> WatchedDict:
        return self.__parts

    def update_topic(self):
        bot = self.__bot
        if not bot.has_channel_privilege(self.channel, AccessLevel.OP):
            bot.say('I need permissions in {} to update the topic.'.format(self.channel), bot.settings.core.owner)
            return

        topic = self.format.format(**self.parts)
        bot.write(('TOPIC', self.channel), topic)
