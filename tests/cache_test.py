'''
Copyright 2014, Konstantin Tretyakov
Licensed under MIT
'''
import os
import pytest
import shutil
from pyencode.cache import Cache

def test_root_dir(tmpdir):
    # No cachedir exists --> dir created
    CACHE_DIR = tmpdir.dirname + '/cache'
    assert not os.path.exists(CACHE_DIR)
    e = Cache(CACHE_DIR)
    assert os.path.isdir(CACHE_DIR)
    os.rmdir(CACHE_DIR)
    
    # Cache dir is a file --> Exception
    with open(CACHE_DIR, 'w') as f:
        f.write('')
    with pytest.raises(Exception) as excinfo:
        e = Cache(CACHE_DIR)
    os.unlink(CACHE_DIR)
    
    # Cache dir is a dir --> All fine
    os.mkdir(CACHE_DIR)
    e = Cache(CACHE_DIR)
    os.rmdir(CACHE_DIR)

REPORT_COUNT = 0    
def test_fetch_url_json(tmpdir):
    global REPORT_COUNT
    
    # Prepare directory
    CACHE_DIR = tmpdir.dirname + '/cache'
    TMP_FILE = CACHE_DIR + '/a.tmp'
    X_FILE = CACHE_DIR + '/x.json'
    
    def REPORT_HOOK(block_count, block_size, total_bytes):
        global REPORT_COUNT
        REPORT_COUNT = REPORT_COUNT + 1
    c = Cache(CACHE_DIR, reporthook = REPORT_HOOK)
    
    # No file exists --> file downloaded
    assert not c.has_file('a.tmp')
    result = c.fetch_url('http://www.google.com', 'a.tmp')
    assert REPORT_COUNT > 0
    REPORT_COUNT = 0
    assert os.path.exists(TMP_FILE)
    assert os.path.abspath(result) == os.path.abspath(TMP_FILE)
    assert c.has_file('a.tmp')
    
    # File exists --> no file downloaded
    result = c.fetch_url('http://www.google.com', 'a.tmp')
    assert REPORT_COUNT == 0
    assert c.has_file('a.tmp')
    
    # File exists, but force = True --> file downloaded
    result = c.fetch_url('http://www.google.com', 'a.tmp', force=True)
    assert REPORT_COUNT > 0
    assert c.has_file('a.tmp')
    REPORT_COUNT = 0
    
    # Check file creation under multiple directories
    c.fetch_url('http://www.google.com', 'a/b/c/d/e.tmp')
    assert c.has_file('a/b/c/d/e.tmp')
    
    # Check json load/save functionality
    x = ['a', 'b', 'c']
    assert not c.has_file('x.json')
    c.json_dump(x, 'x.json')
    assert c.has_file('x.json')
    assert x == c.json_load('x.json')
    
    c.erase('x.json')
    assert not c.has_file('x.json')
    c.erase('a.tmp')
