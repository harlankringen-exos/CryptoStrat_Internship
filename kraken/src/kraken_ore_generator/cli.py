import click
import boto3
from kraken_ore_generator.ore import generate_ore, next_day_snapshot
from kraken_ore_generator.snapshot_check import snapshot_checker
from kraken_ore_generator.top_of_book import tob_generation

@click.group()
def cli():
    pass

@cli.command("ore")
@click.option("--query_url", "-q", type=click.STRING, help="CDM Metadata Query Service URL")
@click.option("--date", "-d", type=click.DateTime(["%Y-%m-%d"]), help="Date to process")
@click.option("--pair", "-p", type=click.STRING, help="Name of currency pair to process")
@click.option("--ore_path", "-op", type=click.STRING, help="Path to write ORE file")
@click.option("--state_path", "-sp", type=click.STRING, help="Path to write next state file")
@click.option("--extractor-license-path", "-ep", default=None, required=False, type=click.STRING, help="Path for extractor license file")
def ore(query_url, date, pair, ore_path, state_path, extractor_license_path):
    if not extractor_license_path:
        s3_client = boto3.client('s3')
        s3_client.download_file('exos-featuremine-license', 'featuremine.latest.lic', 'featuremine.latest.lic')
        extractor_license_path = 'featuremine.latest.lic'
    generate_ore(query_url, pair, date, ore_path)
    next_day_snapshot(state_path, extractor_license_path, ore_path, pair, date)
    snapshot_checker(query_url, pair, date, ore_path, extractor_license_path)

@cli.command("tob")
@click.option("--query_url", "-q", type=click.STRING, help="CDM Metadata Query Service URL")
@click.option("--pair", "-p", type=click.STRING, help="Name of currency pair to process")
@click.option("--ore_path", "-op", type=click.STRING, help="Path to write ORE file")
@click.option("--output", "-o", type=click.STRING, default='-', help="Name of file to write ('-' for stdout)")
@click.option("--extractor-license-path", "-ep", default=None, required=False, type=click.STRING, help="Path for extractor license file")
def tob(query_url: str, pair: str, ore_path: str, output='-', extractor_license_path=None):
    if not extractor_license_path:
        s3_client = boto3.client('s3')
        s3_client.download_file('exos-featuremine-license', 'featuremine.latest.lic', 'featuremine.latest.lic')
        extractor_license_path = 'featuremine.latest.lic'
    tob_generation(query_url, pair, ore_path, output=output, license_path=extractor_license_path)