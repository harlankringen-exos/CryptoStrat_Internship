import json
import logging

from cdm_metadata_client import Client, ClientException
from datetime import datetime, timedelta
from sortedcollections import SortedDict
from fastavro import reader

STATE_NAMESPACE_PREFIX = "exos.tfp.kraken.book.state"
DATA_NAMESPACE = "exos.tfp.kafka.exos.tfp.kraken.L2.raw"

LOG = logging.getLogger(__file__)
logging.basicConfig()


def fetch_prev_state(query_url: str, pair: str, date: datetime):
    mds = Client(query_url)
    return json.loads(
        mds.query(
            f"""
        data where
        data_id.namespace = "{STATE_NAMESPACE_PREFIX}.{pair}.raw"
        and data_id.id = "{date.strftime('%Y-%m-%d')}"
        take newest by data_id.version
    """
        )[0]
        .download(raw=True)
        .decode()
    )


def get_records_in_range(
    query_url: str,
    namespace: str,
    start_range: datetime,
    end_range: datetime,
    origin_id_context=None,
):
    mds = Client(query_url)
    return mds.query(
        f"""
        data where
        data_id.namespace = "{namespace}"
        {f'and origin_id.context = "{origin_id_context}"' if origin_id_context else ''}
        and ((
            timestamp_ranges.effective.start >= ts"{start_range.isoformat()}"
            and timestamp_ranges.effective.end <= ts"{end_range.isoformat()}"
        ) or (
            timestamp_ranges.effective.start < ts"{start_range.isoformat()}"
            and timestamp_ranges.effective.end > ts"{end_range.isoformat()}"
        ) or (
            timestamp_ranges.effective.start < ts"{start_range.isoformat()}"
            and timestamp_ranges.effective.end >= ts"{start_range.isoformat()}"
            and timestamp_ranges.effective.end < ts"{end_range.isoformat()}"
        ) or (
            timestamp_ranges.effective.start > ts"{start_range.isoformat()}"
            and timestamp_ranges.effective.start <= ts"{end_range.isoformat()}"
            and timestamp_ranges.effective.end > ts"{end_range.isoformat()}"
        ))
        order by timestamp_ranges.effective.start asc
        take all
    """
    )


def stream_data_for_time_range(query_url: str, start_range: datetime, end_range: datetime, pair: str):
    records = get_records_in_range(query_url, L2_NAMESPACE, start_range, end_range)
    for r in records:
        for r in (json.loads(rr.decode()) for rr in reader(BytesIO(r.download(raw=True))) if rr):
            if r[-1] == pair:
                yield r

'''
def time_chunks(start_range, end_range, interval):
    start = start_range
    end = end_range
    while start + interval < end:
        yield (start, start + interval)
        start += interval
    yield (start, end)

def stream_data_for_date(
    query_url: str, date: datetime, skip_offset: int, pair: str, interval=timedelta(minutes=70)
):
    start_range = date.replace(hour=0, minute=0, second=0) - timedelta(minutes=10)
    end_range = date.replace(hour=23, minute=59, second=59)

    for (start, end) in time_chunks(start_range, end_range, interval):
        records = get_records_in_range(query_url, DATA_NAMESPACE, start, end)
        in_bounds = []
        for r in records:
            for r in (json.loads(rr.decode()) for rr in reader(r.download(raw=True)) if rr):
                in_bounds.append(r)
        yield from in_bounds
'''