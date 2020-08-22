
import pytest
import filecmp
import tempfile

from src.kraken_data_capture.align import AlignKraken

@pytest.fixture()
def resource():
    resource_dir = 'tests/resources/trades_before_snapshots'
    connector0 = resource_dir + '/' + 'connector_0_spotty.txt'
    connector1 = resource_dir + '/' + 'connector_1_spotty.txt'
    connector2 = resource_dir + '/' + 'connector_2_spotty.txt'
    yield [connector0, connector1, connector2]
    

class TestTradeUpdateSwap():
        
    def test_dedup_trade_update_swap(self, resource):
        '''  ensure that running align.py over the resource files
             results in a correct deduplicated stream
        '''
        c0, c1, c2 = resource
        k = AlignKraken([c0, c1, c2])
        k.dedup()
        tag, tmp = tempfile.mkstemp()
        k.write_dedup(tmp)
        
        expected_alignment = 'tests/resources/ground_truth.txt'        
        assert filecmp.cmp(tmp, expected_alignment)
