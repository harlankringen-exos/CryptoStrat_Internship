
import requests
import logging
from kraken_ore_generator.data import stream_data_for_time_range, fetch_prev_state
from tqdm import tqdm
import msgpack as mp
from datetime import datetime, timedelta


VERSION_ORE = [1, 1, 0] # ORE version

LOG = logging.getLogger(__file__)

# Global variables
cdm_service_name = "kubepocapi.aws.aurotfp.com/cdm-metadata-query-service" # POC SWITCH TO PROD
#cdm_service_name = "kubepocapi.aws.aurotfp.com/cdm-metadata-query-service" # PROD

map_symbols = dict()
prc_dgts = dict()
sz_dgts = dict()
seconds_to_epoch = 0
n_msg = 0


def gather_symbology(list_pairs):
    global maps_symbols, prc_dgts, sz_dgts

    # Getting product details from https: // api.kraken.com / 0 / public / AssetPairs
    req = requests.get('https://api.kraken.com/0/public/AssetPairs')
    dict_products_api = req.json()['result']

    # First we transform dict_products from Kraken name to websocket name
    dict_products = dict()
    for key in dict_products_api:
        try:
            wsname = dict_products_api[key]['wsname']
        except KeyError:
            continue

        dict_products[wsname] = dict_products_api[key]
        dict_products[wsname]['api_key'] = key

    symbology = []
    for sec in list_pairs:
        pair_specs = dict_products[sec]
        wsname = pair_specs['wsname']  # websocket name
        n = len(symbology)
        map_symbols[wsname] = n

        prc_dgts[n] = int(pair_specs['pair_decimals'])
        sz_dgts[n] = int(pair_specs['lot_decimals'])

        symbology.append({'symbol': wsname, 'price_tick': 10**prc_dgts[n], 'qty_tick': 10**sz_dgts[n]})

    return symbology


def extract_nanosecs(tstamp):
    return 1000 * int(tstamp.split('.')[-1]) # time is in usec


def str_to_intfield(s, ndigits):
    assert ndigits >= 0

    x = s.find('.')
    if x == -1:
        return int(s) * int(10 ** ndigits)
    else:
        a = s.rstrip('0')
        n = len(a)
        assert n - x - 1 <= ndigits, f'{n - x},{ndigits}'
        return int(a.replace('.', '')) * int(10 ** (ndigits - n + x + 1))


def parse_lvl_update(updt, idx):
    global seconds_to_epoch, n_msg, prc_dgts, sz_dgts, \
        book_glbl

    for type_qt, qt in zip(['a', 'b'], ['ask', 'bid']):
        if type_qt in updt:
            for lvl_state in updt[type_qt]:
                prc = str_to_intfield(lvl_state[0], prc_dgts[idx])
                qty = str_to_intfield(lvl_state[1], sz_dgts[idx])

                if len(lvl_state) == 3:
                    t_ns = extract_nanosecs(lvl_state[2])
                    t_sec = int(lvl_state[2].split('.')[0])
                else:
                    # In this case I use the last updated time
                    assert len(lvl_state) == 4 and lvl_state[3] == 'r', 'Not retransmitted?!?!'

                if t_sec > seconds_to_epoch:
                    seconds_to_epoch = t_sec
                    l_msgpack.append([0, seconds_to_epoch])
                    #mp.pack([0, seconds_to_epoch], out)

                if qty > 0:
                    book_glbl[qt][prc] = qty
                elif qty == 0:
                    book_glbl[qt].pop(prc, None)
                else:
                    raise RuntimeError(f'Negative quantity not allowed {updt}')

                l_msgpack.append([14, t_ns, 0, n_msg, 0, idx, prc, qty, type_qt=='b'])
                #mp.pack([14, t_ns, 0, n_msg, 0, idx, prc, qty, type_qt=='b'], out)
                n_msg += 1


def parse_trade(trd, idx):
    global seconds_to_epoch, n_msg, prc_dgts, sz_dgts

    t_ns = extract_nanosecs(trd[2])
    t_sec = int(trd[2].split('.')[0])

    if t_sec > seconds_to_epoch:
        seconds_to_epoch = t_sec
        l_msgpack.append([0, seconds_to_epoch])
        #mp.pack([0, seconds_to_epoch], out)

    prc = str_to_intfield(trd[0], prc_dgts[idx])
    qty = str_to_intfield(trd[1], sz_dgts[idx])

    decorator = f'{trd[3]},{trd[4]},{trd[5]}'
    assert len(decorator) <= 8, 'Decorator too long!'

    l_msgpack.append([11, t_ns, 0, n_msg, 0, idx, prc, qty, decorator])
    #mp.pack([11, t_ns, 0, n_msg, 0, idx, prc, qty, decorator], out)
    n_msg += 1


def get_time_snapshot(snap):
    t_max = 0
    for type_qt in ['as', 'bs']:
        if type_qt in snap:
            for lvl in snap[type_qt]:
                assert len(lvl) == 3
                a = lvl[2].split('.')
                t_max = max(t_max, int(a[0]) * int(1e9) + int(a[1]) * 1000)

    return t_max


def book_from_snapshot(snap, idx):
    global prc_dgts, sz_dgts
    book = {'ask':{}, 'bid':{}}

    for qt, quote in zip(['as', 'bs'], ['ask', 'bid']):
        if qt in snap:
            for lvl in snap[qt]:
                prc = str_to_intfield(lvl[0], prc_dgts[idx])
                qty = str_to_intfield(lvl[1], sz_dgts[idx])

                book[quote][prc] = qty
    return book


def book_to_ore(book, t_ns, out, idx):
    for quote in ['ask', 'bid']:
        if quote in book:
            for prc, qty in book[quote].items():
                mp.pack([14, t_ns, 0, n_msg, 0, idx, prc, qty, quote == 'bid'], out)


def book_to_labels(book, nlevels):
    set_labels = set()
    # print(f"Book ask levels {len(book['ask'])}")
    # print(f"Book bid levels {len(book['bid'])}")
    for side in book:
        for price in sorted(book[side], reverse=(False if side=='ask' else True))[:nlevels]:
        #for price in sorted(book[side], reverse=True)[:nlevels]:
            lab = f'{side}-{price}-{book[side][price]}'
            set_labels.add(lab)
    return set_labels


def compare_books(book1, book2, nlevels):
    lab1 = book_to_labels(book1, nlevels)
    lab2 = book_to_labels(book2, nlevels)
    return lab1 ^ lab2


def process_flow(msg, out, idx):
    global book_glbl, l_msgpack

    if msg[-2] == 'book-1000':
        if 'as' in msg[1] or 'bs' in msg[1]:
            # When a snapshot is encountered
            # 1. the book is checked
            # 2. if checks messages are dumped in the ore file
            # 3. if it doesn't check the book is invalidated and reconstructed
            book_snap = book_from_snapshot(msg[1], idx)
            #set_diff = compare_books(book_snap, book_glbl, int(msg[-2].split('-')[-1]))
            set_diff = compare_books(book_snap, book_glbl, 1000)
            if set_diff:
                print(f'Book failed check at sequence number {msg[-3]}')
                print(set_diff)
                for lab in set_diff:
                    a = lab.split('-')
                    side, price = a[0], int(a[1])
                    in_book, in_snap = (price in book_glbl[side]), (price in book_snap[side])
                    if in_book and in_snap and book_glbl[side][price] == book_snap[side][price]:
                        continue

                    print(f'{side}, {price} in Book: {in_book}, in Snap: {in_snap}')

                #assert 0
                # Invalidate the ORE book
                # TO DO

                # Recreate the book with the new snapshot
                book_glbl = book_from_snapshot(msg[1], idx)

                # Reconstruct the book in the ore file
                # TO DO

            else:
                # Books matches perfectly we can unload the messages
                print(f'Book matches at sequence number {msg[-3]}')
                for m in l_msgpack:
                    mp.pack(m, out)

            l_msgpack = list()

        elif 'a' in msg[1] or 'b' in msg[1]:
            parse_lvl_update(msg[1], idx)
        else:
            raise RuntimeError(f'Type of message not recognized\n{msg}')

    elif msg[-2] == 'trade':
        for trd in msg[1]:
            parse_trade(trd, idx)

    else:
        raise RuntimeError(f'Type of message not recognized\n{msg}')



pair = 'XBT/USD'
t0 = datetime(2020, 7, 13)
t1 = t0 + timedelta(hours=24)

symbology = gather_symbology([pair])
state = fetch_prev_state(cdm_service_name, pair, t0)
seqnum_state = state[1]['sequence']
book_glbl = book_from_snapshot(state[1], 0)

# import json
# with open(f'./snapshots/snap_BTC-USD_027891.json', 'r') as fin:
#     snap = json.load(fin)
# book_snap = book_from_snapshot(snap[1], 0)

from copy import deepcopy


with open(f"./kraken_{pair.replace('/','-')}.ore", 'wb') as fout:
    mp.pack(VERSION_ORE, fout)
    mp.pack(symbology, fout)

    seconds_to_epoch = state[1]['time'] // int(1e9)
    mp.pack([0, seconds_to_epoch], fout)

    book_to_ore(book_glbl, state[1]['time'] % int(1e9), fout, 0)

    l_msgpack = list()
    seqnum = 0
    for r in tqdm(stream_data_for_time_range(cdm_service_name, t0, t1, pair)):
        assert r[-1] == pair, f'{r}' # Sanity check
        assert len(r) == 4 or len(r) == 5, f'{r}\nHas an unexpected length {len(r)}'

        ## Adding sequence number here, it is always the -3 argument of the list
        if len(r) == 4:
            r = [r[0], deepcopy(r[1]), seqnum, deepcopy(r[-2]), deepcopy(r[-1])]
        elif len(r) == 5:
            r = [r[0], deepcopy(r[1]), deepcopy(r[2]), seqnum, deepcopy(r[-2]), deepcopy(r[-1])]
        seqnum += 1

        # if 'as' in r[1] or 'bs' in r[1]:
        #     with open(f'./snapshots/snap_BTC-USD_{r[-3]:06d}.json', 'w') as fout_snap:
        #         json.dump(r, fout_snap)

        if r[-3] <= seqnum_state:
            continue

        process_flow(r, fout, 0)
