import time
import json
from client import KrakenClient
from util import subscribe, SubscriptionKind, make_logger
from secret import (
    make_producer,
    write_message,
    PAIRS,
    SUBSCRIPTION_DEPTH,
    WEBSOCKET_RECONNECT_COUNT
)

from typing import List, Optional, Callable, Any
from aiostream import pipe

LOGGER = make_logger(__name__)


async def run(
    subscription_kinds: List[SubscriptionKind],
    topic: str,
    begin_timestamp = None,
    interval_sec = None,
    num_msgs = 10,
    on_message: Optional[Callable[[Any], Any]] = None,
):
    def log_message(msg):
        if not isinstance(msg, list):
            #LOGGER.info("Status: %s", json.dumps(msg))
           pass
        else:
            LOGGER.debug("Received message: %s", json.dumps(msg))

    def maybe_callback(m):
        if on_message:
            on_message(m)

    # the continuous version takes messages up until a time point
    if interval_sec:
        async with KrakenClient() as client:
            for kind in subscription_kinds:
                await subscribe(client, kind, PAIRS, SUBSCRIPTION_DEPTH)
            await (
                client.stream(reconnect_count=WEBSOCKET_RECONNECT_COUNT)
                | pipe.action(log_message)
                | pipe.filter(lambda msg: isinstance(msg, list))
                | pipe.map(json.dumps)
                #| pipe.print()
                | pipe.takewhile(lambda x: time.time() - begin_timestamp < interval_sec)
                | pipe.action(maybe_callback)
            )
            client.disconnect()
            
    # the discrete version takes 100 distinct messages
    else:
        async with KrakenClient() as client:
            for kind in subscription_kinds:
                await subscribe(client, kind, PAIRS, SUBSCRIPTION_DEPTH)
            await (
                client.stream(reconnect_count=WEBSOCKET_RECONNECT_COUNT)
                | pipe.action(log_message)
                | pipe.filter(lambda msg: isinstance(msg, list))
                | pipe.map(json.dumps)
                #| pipe.print()
                | pipe.take(num_msgs)
                | pipe.action(maybe_callback)
            )
            print("disconnecting")
            client.disconnect()
        
