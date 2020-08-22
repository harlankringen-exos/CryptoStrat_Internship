from client import KrakenClient
from util import (
    subscribe,
    unsubscribe,
    SubscriptionKind,
    make_logger,
    is_snapshot,
)
from secret import PAIRS, SUBSCRIPTION_DEPTH

from aiostream import stream, pipe

LOGGER = make_logger(__name__)


async def handle():
    async with KrakenClient() as client:
        LOGGER.info("Subscribing")
        await subscribe(client, SubscriptionKind.BOOK, PAIRS, SUBSCRIPTION_DEPTH)

        LOGGER.info("Waiting for snapshot messages")
        snapshot = await (client.stream() | pipe.filter(is_snapshot) | pipe.take(len(PAIRS)) | pipe.list())

        LOGGER.info("Unsubscribing")
        await unsubscribe(client, SubscriptionKind.BOOK, PAIRS, SUBSCRIPTION_DEPTH)

    return snapshot
