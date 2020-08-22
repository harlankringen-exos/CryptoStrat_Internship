import time
import asyncio
import json
from aiohttp import web
from typing import TypedDict, Optional, TypedDict, List
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
    msgs: List[str]


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


async def start_book_listener(state: ServiceState, begin, which):
    def on_message(m):
        state["last_published_message_timestamp"] = datetime.now()
        state['msgs'].append(m)
    await run_listener(
        [SubscriptionKind.BOOK, SubscriptionKind.TRADE], BOOK_TRADE_TOPIC, begin, on_message=on_message
    )
    with open(f'snapshot_{which}.txt', 'w+') as outb:
        for line in state["msgs"]:
            outb.write(line + "\n")


async def start_trade_listener(state: ServiceState, begin, which):
    def on_message(m):
        state["last_published_message_timestamp"] = datetime.now()
        state['msgs'].append(m)
    await run_listener(
        [SubscriptionKind.BOOK, SubscriptionKind.TRADE], TRADE_SPREAD_TOPIC, begin, interval_sec=20*60, on_message=on_message
    )
    with open(f"connector_{which}.txt", "w") as outf:
        for line in state["msgs"]:
            outf.write(line + "\n")


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


def main(begin_ts, listener_type='book',identifier='prime'):
    print("listener type:", listener_type)
    state = ServiceState(
        healthy=True,
        last_published_message_timestamp=None,
        msgs = []
    )

    listeners = {'book':start_book_listener,
                 'trade':start_trade_listener
                 }
    
    async def f():
        await asyncio.gather(
            *[
                listeners[listener_type](state, begin_ts, identifier)
            ]
        )

    asyncio.run(f())

    print("totally finished")

if __name__ == "__main__":
    import sys
    begin = sys.argv[1]
    if begin == "dunno":
        begin = time.time()
    which = sys.argv[2]
    iden = sys.argv[3]
    main(begin, which, iden)
