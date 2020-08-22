import asyncio
import json
from aiohttp import web
from typing import TypedDict, Optional, TypedDict
from datetime import datetime, timedelta
from listener import run as run_listener
from handler import handle
from util import make_logger, SubscriptionKind
from secret import (
    make_producer,
    write_message,
    SNAPSHOT_INTERVAL_SECONDS,
    BOOK_TRADE_TOPIC,
    TRADE_SPREAD_TOPIC,
    SERVICE_PORT,
    MESSAGE_GAP_THRESHOLD
)

LOGGER = make_logger(__name__)

class ServiceState(TypedDict):
    healthy: bool
    last_published_message_timestamp: Optional[datetime]


async def run_healthcheck_server(state: ServiceState):
    LOGGER.info("Starting healthcheck server")

    async def verify_health(request):
        if not state["healthy"]:
            raise web.HTTPServiceUnavailable
        return web.Response(text="healthy")

    app = web.Application()
    app.add_routes([web.get("/healthcheck", verify_health)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", SERVICE_PORT)
    await site.start()


async def start_book_trade_listener(state: ServiceState, which):
    with open(f'snapshot_{which}.txt', 'w+') as outb:
        
        #LOGGER.info("Starting book/trade listener")
        def on_message(m):
            #LOGGER.info("Status: %s", json.dumps(m))
            outb.write(m + "\n")
            state["last_published_message_timestamp"] = datetime.now()
        await run_listener(
            [SubscriptionKind.BOOK, SubscriptionKind.TRADE], BOOK_TRADE_TOPIC, on_message=on_message
    )


async def start_trade_spread_listener(state: ServiceState, which):
    with open(f'snapshot_{which}.txt', 'w+') as outt:
        #LOGGER.info("Starting trade/spread listener")
        def on_message(m):
            outt.write(m + "\n")
            state["last_published_message_timestamp"] = datetime.now()
        await run_listener(
            [SubscriptionKind.TRADE, SubscriptionKind.SPREAD], TRADE_SPREAD_TOPIC, on_message=on_message
    )


async def start_timer_handler(state: ServiceState, interval: int):
    LOGGER.info("Starting timer snapshot request event handler")
    async with make_producer() as producer:
        while True:
            LOGGER.info("Waiting for %d seconds", interval)
            await asyncio.sleep(interval)
            LOGGER.info("Publishing snapshot message")
            state["last_published_message_timestamp"] = datetime.now()
            for snapshot in await handle():
                await write_message(producer, BOOK_TRADE_TOPIC)(json.dumps(snapshot))

async def check_last_published_message(state: ServiceState):
    LOGGER.info("Failing healthcheck after %d seconds without a message", MESSAGE_GAP_THRESHOLD)
    while True:
        if state["last_published_message_timestamp"] is None:
            await asyncio.sleep(10)
            LOGGER.debug("last_published_message_timestamp unknown, assuming init")
            continue
        delta = datetime.now() - state["last_published_message_timestamp"]
        if delta > timedelta(seconds=MESSAGE_GAP_THRESHOLD):
            LOGGER.info("Last message published too long ago, marking self unhealthy")
            state["healthy"] = False
        await asyncio.sleep(10)


def main(which="prime"):
    #LOGGER.info("Binding to Kafka at %s", discover_kafka())
    state = ServiceState(
        healthy=True,
        last_published_message_timestamp=None
    )

    async def f():
        await asyncio.gather(
            *[
                start_book_trade_listener(state, which),
                start_trade_spread_listener(state, which),
                #run_healthcheck_server(state),
                #start_timer_handler(state, SNAPSHOT_INTERVAL_SECONDS),
                #check_last_published_message(state)
            ]
        )

    asyncio.run(f())

    print("totally finished")

if __name__ == "__main__":
    import sys
    which = sys.argv[1]
    main(which)
