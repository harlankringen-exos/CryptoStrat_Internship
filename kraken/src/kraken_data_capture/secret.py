import json
import sys
import asyncio
from os import getenv
from aiokafka import AIOKafkaProducer

service_name = getenv("SVC_CONFIG", "kraken-realtime")

BOOK_TRADE_TOPIC = "BOOK_TRADE_TOPIC"
TRADE_SPREAD_TOPIC = "TRADE_SPREAD_TOPIC"
PAIRS = ['XBT/USD']
SERVICE_PORT = 8765
SUBSCRIPTION_DEPTH = 100
WEBSOCKET_RECONNECT_COUNT = 1
SNAPSHOT_INTERVAL_SECONDS = 1
MESSAGE_GAP_THRESHOLD = 1


def discover_kafka():
    if "pytest" in sys.modules:
        return "kafka:9092"
    host_port = config_handler.discover("kafka")
    return f"{host_port[0]}:{host_port[1]}"


class ProducerContextManager(AIOKafkaProducer):
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, a, b, c):
        await self.stop()

producer = None
def make_producer():
    global producer
    if producer is None:
        producer = ProducerContextManager(
            loop=asyncio.get_event_loop(), enable_idempotence=True
        )
    return producer

write_lock = None
def make_write_lock():
    global write_lock
    if write_lock is None:
        write_lock = asyncio.Lock(loop=asyncio.get_event_loop())
    return write_lock

def write_message(producer: AIOKafkaProducer, topic: str):
    async def func(msg: str):
        async with make_write_lock():
            await producer.send_and_wait(topic, msg.encode("utf-8"))

    return func
