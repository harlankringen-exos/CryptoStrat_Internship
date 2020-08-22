import logging
from random import randint
from os import getenv
from enum import Enum
from typing import List, Optional


def make_logger(name):
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(name)
    logger.setLevel(level=getenv("LOG_LEVEL", "INFO"))
    return logger


LOGGER = make_logger(__name__)


class SubscriptionKind(Enum):
    BOOK = "book"
    TRADE = "trade"
    SPREAD = "spread"


async def subscribe(
    client,
    kind: SubscriptionKind,
    pairs: List[str],
    depth: Optional[int] = None,
):
    LOGGER.info("Subscribing to %s", kind.value)
    subscription = {"name": kind.value}
    if kind == SubscriptionKind.BOOK:
        subscription["depth"] = depth
    await client.send(
        {
            "pair": pairs,
            "event": "subscribe",
            "reqid": randint(0, 10000),
            "subscription": subscription,
        }
    )


async def unsubscribe(
    client,
    kind: SubscriptionKind,
    pairs: List[str],
    depth: Optional[int] = None,
):
    LOGGER.info("Unsubscribind from %s", kind.value)
    subscription = {"name": kind.value}
    if kind == SubscriptionKind.BOOK:
        subscription["depth"] = depth
    await client.send(
        {
            "event": "unsubscribe",
            "reqid": randint(0, 10000),
            "pairs": pairs,
            "subscription": subscription,
        }
    )


def is_snapshot(msg: list) -> bool:
    try:
        return "as" in msg[1]
    except:
        return False
