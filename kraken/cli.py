import click
import sys
import json
import asyncio
from kraken_realtime.util import subscribe, SubscriptionKind
from kraken_realtime.client import KrakenClient
from aiostream import pipe

@click.group()
def cli():
    pass


@cli.command()
@click.option("--output", "-o", default="-", type=str, help="Output path (-) for stdout")
@click.option("--subscription", "-s", multiple=True, type=SubscriptionKind, help="Name of Kraken feed to subscribe to (book/trade/spread)")
@click.option("--pair", "-p", multiple=True, type=str, help="A crypto pair to subscribe to (e.g. BTC/USD)")
@click.option("--depth", "-d", type=int, help="Depth value for book subscriptions")
@click.option("--verbose", "-v", default=False, is_flag=True)
@click.option("--reconnect", "-r", is_flag=True, default=False, help="Reconnect to Kraken WebSocket on disconnect")
def record(output, subscription, pair, depth, verbose, reconnect):
    if len(subscription) == 0:
        click.echo(
            "Please provide at least one subscription parameter (book/trade/spread)"
        )
        exit(1)
    if len(pair) == 0:
        click.echo("Please provide at least one pair (e.g. BTC/USD)")
        exit(1)

    async def listen():
        with (sys.stdout if output == "-" else open(output, "w+")) as f:
            async with KrakenClient() as client:
                for kind in subscription:
                    await subscribe(client, kind, pair, depth)

                def write_message(msg):
                    f.write(json.dumps(msg) + "\n")
                    f.flush()

                def print_status_msg(msg):
                    if verbose and not isinstance(msg, list):
                        click.echo(f"Status: {msg}")

                stream = client.stream(reconnect_count=-1 if reconnect else 0)
                
                await (
                    client.stream()
                    | pipe.action(print_status_msg)
                    | pipe.filter(lambda msg: isinstance(msg, list))
                    | pipe.action(write_message)
                )

    asyncio.run(listen())


if __name__ == "__main__":
    cli()
