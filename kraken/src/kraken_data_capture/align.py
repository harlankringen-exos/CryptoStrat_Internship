
import functools
import itertools
import json
import math

foldl = lambda func, acc, xs: functools.reduce(func, xs, acc)

class AlignKraken():

    def __init__(self, connectors=[]):
        self.connectors = list(map(open, connectors))    
        self.deduplicated_stream = []
        self.snapshots = []

        for c in self.connectors:
            self.skip_snapshot(c, first_line=True)  # expect first line to be snapshots
        
    def check_equal_ts(self, x, acc):
        if x == acc:
            return x
        else:
            return False

    def unpack(self, connector_line):
        idx = connector_line[0]
        d = connector_line[1]
        return idx, d

    def skip_snapshot(self, connect_fobj, first_line=False):
        # ensure first line is an update
        line = connect_fobj.readline()
        tag = json.loads(line)[1]
        try:
            payload = tag['as']
        except KeyError:
            print("line read was not an update, skipping over line")
            if(first_line):
                print("moving fileptr to beginning")
                connect_fobj.seek(0)
            
    def get_timestamps(self, msg):
        # grab all timestamps from a message
        # todo: ensure doesn't return None
        ts = []
        payload = msg[1]
        if msg[0] == 270:
            if 'b' in payload:
                ts = list(map(lambda x: float(x[2]), payload['b']))   # the bid side
            elif 'a' in payload:
                ts = list(map(lambda x: float(x[2]), payload['a']))   # the ask side
            else:
                return [math.inf] # an update message, so we give it a very large number we would never take for the min

        # todo: still just taking the first
        elif msg[0] == 271:
            for i in payload:
                ts.append(float(i[2]))
        return ts

    def choose_connector(self, times):
        # assume leftmost ts in a sublist is the earliest
        mins = list(map(lambda l: min(l), times))
        min_elt = min(mins)
        min_idx = []
        # for idx,m in enumerate(mins):
        #     if m == min_elt:
        #         min_idx.append(idx)
        # for m in min_idx:
        #     if len(times[m])
        return mins.index(min(mins))
        
    def read_until_ts(self, fobj, ts):
        # readlines until scan pointer in fobj is at ts
        ts1 = self.get_timestamps(self.unpack(json.loads(fobj.readline())))
        ts1 = list(ts1)[0] # first should match
        if ts != ts1:
            self.read_until_ts(fobj, ts)
        else:
            return fobj
            
    def dedup(self):    
        cached = [False ]*len(self.connectors)

        seq_no = 0
        num_connectors_consumed = 0
        last_source = 0
        
        while True:

            # either draw a new card or use one from your hand
            line = [None]*len(self.connectors)
            for idx,fd in enumerate(self.connectors):
                if not cached[idx]:
                    try:
                        line[idx] = json.loads(fd.readline())
                    except json.decoder.JSONDecodeError as e:
                        # EOF returns empty string, which will force a decode error
                        fd.close()
                        num_connectors_consumed += 1
                    except ValueError:
                        # trying to read from a closed fd
                        pass
                else:
                    line[idx] = cached[idx]
                    cached[idx] = False   
            
            # check if done
            if num_connectors_consumed == len(self.connectors):
                break

            # consumed connectors will leave Nones in cached and lines
            # todo: figure out a better way to clean up used connectors
            line = list(filter(lambda x: x != None, line))
            
            # check if each connector agrees on timestamps
            # if we see a snapshot we can't get the timestamps, so we fill in Nones.
            # and the nremove them here; todo: brittle
            timestamps = list(map(self.get_timestamps, line))
            if not (timestamps.count(timestamps[0]) == len(timestamps)):

                # take the earliest in time as the best approximation
                # determine which feeds are starting ahead in time, cache their value
                youngest = self.choose_connector(timestamps) 
                cached = [line[idx] if ts > timestamps[youngest] else False for idx, ts in enumerate(timestamps)]
            
            else:
                # every connector agrees
                youngest = 0

            if last_source != youngest:
                seq_no += 2    # we had to switch connectors
            else:
                seq_no += 1
            
            last_source = youngest
            line[youngest].insert(1, seq_no)
            self.deduplicated_stream.append(line[youngest])

    def write_dedup(self, outf_name='connector_dedup.txt'):
        with open(outf_name, 'w') as out:
            for line in self.deduplicated_stream:
                out.write(str(line) + '\n')
        
    def write_snapshot(self, outf_name='snapshot_dedup.txt'):
        with open(outf_name, 'w') as out:
            for lin in self.deduplicated_stream:
                out.write(str(lnie) + '\n')
        
if __name__ == "__main__":
    import sys
    connector_files = sys.argv[1:]
    k = AlignKraken(connector_files)
    k.dedup()
