import featuremine.extractor as extr
from cdm_metadata_client import Client
import msgpack as mp
from pandas import concat
from io import StringIO

VERSION_ORE = [1, 1, 0] # Ore version

def extract_symbols(ore_filename):
    global VERSION_ORE

    with open(ore_filename, "rb") as ore_file:

        unpacker = mp.Unpacker(ore_file)
        file_version = unpacker.unpack()
        symbology = unpacker.unpack()

        if file_version != VERSION_ORE:
            raise RuntimeError(f"ore_reader supports Ore {VERSION_ORE}, Input file uses", file_version)

    return symbology


def join_df_trades_tob(df_trades, df_tob, ticker, qty_tick):

    df_trades['mkt_pair'] = ticker
    df_trades['type'] = 'trd'
    df_trades.rename(columns={'Timestamp': 'time', 'trade_price': 'trd_prc', 'qty': 'trd_qty'}, inplace=True)
    df_trades['trd_qty'] /= qty_tick
    col_trades = ['time', 'mkt_pair', 'type', 'trd_prc', 'trd_qty']

    df_tob.rename(columns={'Timestamp': 'time', 'ask_prx_0': 'ask_prc', 'bid_prx_0': 'bid_prc',
                           'ask_shr_0': 'ask_qty', 'bid_shr_0': 'bid_qty'}, inplace=True)
    df_tob['ask_qty'] /= qty_tick
    df_tob['bid_qty'] /= qty_tick
    df_tob['mkt_pair'] = ticker

    # Complementing with type of quote update
    df_tob['type'] = 'to_do'

    sr_1, sr_2 = df_tob['ask_prc'], df_tob['ask_qty']
    idx = (sr_1 != sr_1.shift(1)) | (sr_2 != sr_2.shift(1))
    df_tob.loc[idx, 'type'] = 'ask'

    sr_1, sr_2 = df_tob['bid_prc'], df_tob['bid_qty']
    idx = (sr_1 != sr_1.shift(1)) | (sr_2 != sr_2.shift(1))
    df_tob.loc[idx, 'type'] = 'bid'

    col_tob = ['time', 'mkt_pair', 'type', 'bid_prc', 'bid_qty', 'ask_prc', 'ask_qty']
    df_joined = concat([df_trades[col_trades], df_tob[col_tob]], axis=0, ignore_index=True)
    df_joined.sort_values('time', kind='mergesort', inplace=True)

    # Interleaving trades with quotes
    df_joined['grp_type'] = df_joined['type'].apply(lambda x: 1 if x == 'trd' else 0)
    df_joined['order'] = 1
    tob_grouped = df_joined.groupby(['time', 'grp_type'])
    df_joined['order'] = tob_grouped['order'].transform('cumsum')
    df_joined = df_joined.sort_values(['time', 'order'], kind='mergesort')
    cols = ['bid_prc', 'bid_qty', 'ask_prc', 'ask_qty']
    df_joined[cols] = df_joined[cols].fillna(method='ffill')

    df_joined.drop(['grp_type', 'order'], axis='columns', inplace=True)
    

    return df_joined


def tob_generation(query_url: str, pair: str, ore_path: str, license_path=None, output='-'):

    file_ore = ore_path
    if ore_path.startswith('cdm://'):
        data = Client(query_url).get_record_from_cdm_uri(ore_path).download(raw=True)
        with open('file.ore', 'wb+') as f:
            f.write(data)
        file_ore = 'file.ore'
    symb = extract_symbols(file_ore)

    def maybe_decode(a):
        if isinstance(a, bytes):
            return a.decode()
        return a
    symb = [{maybe_decode(k): maybe_decode(v) for k, v in s.items()} for s in symb]

    # This handles only one market pair
    assert len(symb) == 1 and symb[0]['symbol'] == pair, f'Wrong symbology {symb} for {pair}'

    extr.set_license(license_path)
    graph = extr.system.comp_graph()
    op = graph.features

    upd_stream = op.book_play_split(file_ore, (pair,))[0]

    # Extracting top of book updates
    top_book = op.book_build(upd_stream, 1)
    same_top = op.equal(top_book, op.tick_lag(top_book, 1))
    changed_top = op.logical_not(same_top)
    changed_top_res = changed_top.ask_prx_0 | changed_top.ask_shr_0 | changed_top.bid_prx_0 | changed_top.bid_shr_0
    top_book_update = op.filter_if(changed_top_res, top_book)
    header = op.book_header(upd_stream)
    updates = op.combine(op.asof(header, top_book_update), tuple(), top_book_update, tuple())
    tob = op.accumulate(updates)

    # Extracting trades
    trades = op.book_trades(upd_stream)
    trades_aggr = op.accumulate(trades)

    graph.stream_ctx().run()

    df_trades = extr.result_as_pandas(trades_aggr)
    df_tob = extr.result_as_pandas(tob)

    _df = join_df_trades_tob(df_trades, df_tob, pair, symb[0]['qty_tick'])
    cols = ['time', 'mkt_pair', 'type', 'bid_prc', 'bid_qty', 'ask_prc', 'ask_qty', 'trd_prc', 'trd_qty']
    buf = StringIO()
    tob = _df[cols].to_csv(buf, index=False)

    if output == '-':
        print(buf.getvalue())
    else:
        with open(output, 'w+') as f:
            f.write(buf.getvalue())
