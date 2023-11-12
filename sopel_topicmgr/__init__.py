"""sopel-topicmgr

Extensible topic-management plugin for Sopel IRC bots.
"""
from __future__ import annotations

from sopel import plugin
from sopel.tools import memories

from . import manager


CHANNELS = {
    '#dgw': ('{welcome} | {description} | {comment}', {
        'welcome': '#dgw da!',
        'description': "dgw's private testing area for stuff that isn't even ready for other #Kaede users",
        'comment': "also dgw's place to look things up privately using Internets",
    }),
}


def setup(bot):
    # only set up the memory right now;
    # need to wait until after connection for `bot.make_identifier()` to reflect ISUPPORT
    bot.memory['topic_managers'] = memories.SopelIdentifierMemory(identifier_factory=bot.make_identifier)


@plugin.event('JOIN')
def register_topic_manager(bot, trigger):
    if trigger.nick == bot.nick and trigger.sender in CHANNELS:
        deets = CHANNELS[trigger.sender]
        bot.memory['topic_managers'][trigger.sender] = manager.TopicManager(
            bot, trigger.sender, deets[0], deets[1],
        )


@plugin.command('topicpart')
def set_topic_part(bot, trigger):
    part, value = trigger.group(2).split(' ', maxsplit=1)
    bot.memory['topic_managers'][trigger.sender].parts[part] = value


def shutdown(bot):
    del bot.memory['topic_managers']
