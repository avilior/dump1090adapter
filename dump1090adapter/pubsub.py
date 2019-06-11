import logging
import asyncio
from asyncio import Queue, QueueFull
from copy import deepcopy, Error

LOG=logging.getLogger(__name__)

_PUBLISHER  ="publisher"
_SUBSCRIBERS="subscribers"
_Q          ="queue"

_state = {}

def add_topic(topic: str):
    """
    Adds a topic to the pub/sub
    :param topic:
    :return:
    """
    if topic in _state:
        LOG.debug(F"add_topic {topic} already exists.")
        return
    _state[topic] = { _PUBLISHER: None, _SUBSCRIBERS : {}}
    LOG.info(F"Topic {topic} created successfully")

def remove_topic(topic: str):
    """
    Topic to remove.
    :param topic:
    :return:
    """
    topic_to_remove = _state[topic] if topic in _state else None
    if topic_to_remove is None:
        LOG.info(F"remove_topic: {topic} does not exist or already removed")
        return

    for id in _state[topic][_SUBSCRIBERS].keys():
        LOG.debug(F"Delete subscriber {id}")
        del _state[topic][_SUBSCRIBERS][id][_Q]
        _state[topic][_SUBSCRIBERS][id][_Q] = None
    del _state[topic]


def subscribe(id: str, topic: str) -> str:
    """
    :param id: a unique id identifying the subscriber
    :param topic: the topic to subscribe to
    :return:
    """

    topic_to_subscribe_to = _state[topic] if topic in _state else None

    if topic_to_subscribe_to is None:
        LOG.warning(F"Subscriber {id} is attemtping to subscribe to non-existent topic: {topic}")
        return

    if id in topic_to_subscribe_to[_SUBSCRIBERS]:
        LOG.debug(F"Subscriber {id} is already subscribed to topic: {topic}")
        return


    topic_to_subscribe_to[_SUBSCRIBERS][id] = {_Q : Queue()}

def unsubscribe(id: str, topic:str):

    topic_to_unsubscribe_from = _state[topic] if topic in _state else None

    if topic_to_unsubscribe_from is None:
        LOG.warning(F"Subscriber {id} is attemtping to unsubscribe from non-existent topic: {topic}")
        return

    if id not in topic_to_unsubscribe_from[_SUBSCRIBERS]:
        LOG.debug(F"Subscriber {id} is already unsubscribed from topic: {topic}")
        return

    topic_to_unsubscribe_from [_SUBSCRIBERS][id] = {_Q: None}
    del topic_to_unsubscribe_from [_SUBSCRIBERS][id]


def publish(topic: str, item: object):

    if item is None:
        return

    topic_to_publish_to = _state[topic] if topic in _state else None
    if topic_to_publish_to is None:
        LOG.warning(F"Publishing to non existant topic {topic}")

    for sid,subscriber in topic_to_publish_to[_SUBSCRIBERS].items():
        try:
            subscriber[_Q].put_nowait(deepcopy(item))
        except Error as x:
            LOG.exception(F"Deep Copy {sid}.")
        except QueueFull:
            LOG.exception(F"Queue Full exception {sid}.")

async def rx(id: str, topic: str):
    topic_to_receive_from = _state[topic] if topic in _state else None
    if topic_to_receive_from is None:
        LOG.warning(F"Subscriber {id} attemted to receive from topic {topic} that does not exist.")
        return

    subscription = topic_to_receive_from[_SUBSCRIBERS][id] if id in topic_to_receive_from[_SUBSCRIBERS] else None
    if subscription is None:
        LOG.warning(F"Subscriber {id} does not have a susbcription to topic {topic}")
        return

    return await subscription[_Q].get()

async def rx_nowait(id: str, topic: str):
    topic_to_receive_from = _state[topic] if topic in _state else None
    if topic_to_receive_from is None:
        LOG.warning(F"Subscriber {id} attemted to receive from topic {topic} that does not exist.")
        return

    subscription = topic_to_receive_from[_SUBSCRIBERS][id] if id in topic_to_receive_from[_SUBSCRIBERS] else None
    if subscription is None:
        LOG.warning(F"Subscriber {id} does not have a susbcription to topic {topic}")
        return

    return await subscription[_Q].get_nowait()


#===================================================================================================
#
#===================================================================================================

async def pub(topic, count):
    print(F"Starting publisher with topic: {topic}")

    c = 0
    while True:
        msg = {"msg": "Hello", "count":c}
        publish(topic,msg)
        await asyncio.sleep(1)
        c += 1
        if c >= count:
            break
    remove_topic(topic)



async def sub(id, topic):
    print(F"Starting subscriber {id} with topic: {topic}")
    subscribe(id,topic)
    while True:
        msg = await rx(id,topic)
        print(F"{id} rxed  msg: {msg['msg']} count: {msg['count']} ")

    print(F"Sub {id} Done")



async def main(loop):

    tasks = []

    topic = "topic1"

    add_topic(topic)

    publisher = loop.create_task(pub(topic, 10))
    tasks.append(publisher)
    for id in range(4):
        tasks.append(loop.create_task(sub(id, topic)))

    x = await asyncio.gather(*tasks)

    print("DONE")





if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()