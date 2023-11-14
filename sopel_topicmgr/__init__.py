"""sopel-topicmgr

Extensible topic-management plugin for Sopel IRC bots.
"""
from __future__ import annotations

from sopel import plugin
from sopel.tools import get_logger

from .managers import TopicManager
from .providers import PropertyProvider


CHANNELS = {
    '#dgw': "#dgw da! | dgw's private testing area for really WIP stuff | Currently hacking on {wip.project}",
}

class WIPProjectProvider(PropertyProvider):
    def defaults(self):
        return {
            'project': 'sopel-topicmgr',
        }

LOGGER = get_logger('topicmgr')


def setup(bot):
    LOGGER.debug("Creating topic manager")
    bot.memory['topic_manager'] = TopicManager(bot)


@plugin.event('JOIN')
def register_channel_managers(bot, trigger):
    if trigger.nick == bot.nick and trigger.sender in CHANNELS:
        LOGGER.debug("Registering channel %r", trigger.sender)
        bot.memory['topic_manager'].register_channel(
            trigger.sender, CHANNELS[trigger.sender],
        )


@plugin.command('topicprop')
def set_topic_part(bot, trigger):
    if not trigger.group(3):
        bot.reply("I need at least a property name.")
        return

    provider, prop = trigger.group(3).split('.', maxsplit=1)

    try:
        _, value = trigger.group(2).split(' ', maxsplit=1)
    except ValueError:
        value = bot.memory['topic_manager'].get_property(provider, prop)
        bot.reply('{} = {}'.format(trigger.group(3), value))
        return

    bot.memory['topic_manager'].update_property(provider, prop, value)
    bot.reply("Updated {} value: {}".format(trigger.group(3), value))


def shutdown(bot):
    del bot.memory['topic_manager']
