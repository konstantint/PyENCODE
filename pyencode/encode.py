'''
PyENCODE: Encode, EncodeCollection, EncodeFile classes.

Copyright 2014, Konstantin Tretyakov
Licensed under MIT.
'''
import gzip
import json
import os.path
import re
import urllib

from intervaltree_bio import GenomeIntervalTree

from .cache import Cache
from ._gzip import GzipInputStream
from .util import with_closing_contextmanager


class EncodeException(Exception):
    pass

class Encode(object):
    '''
    The root object, representing the hierarchy of ENCODE project data files.
    
    Note that due to how ``cache.Cache`` operates, the object is not safe for doing multithreading or multiprocessing, unless all the necessary files are already available in the cache.
    '''
    
    def __init__(self, cache_dir=os.path.expanduser("~/.pyencode"),
                         reporthook=None,
                         root_url="http://hgdownload.cse.ucsc.edu/goldenPath/hg19/encodeDCC"):
        '''
        Initialize the Encode root object.
        
        KwArgs:
            cache_dir (str): The root directory for keeping downloaded ENCODE files.
                Note that ENCODE files may be large, so have enough free space available (a gigabyte or so would be nice).
            reporthook (function):  A reporthook provided to ``urlopen`` for tracking download progress.
                Must be a function ``(block_count, block_size, total_bytes)``, see ``urlretrieve`` documentation.
            root_url (str): The URL root of the ENCODE data. Normally, you should not change the default value.
                Expect all kind of wrong things to happen if you provide a wrong URL here.
                
        Raises:
            HttpException: on network errors.
            WindowsError or IOError or other system errors: if cache directory cannot be created or written to
            EncodeException: on other errors
        '''
        self._cache = Cache(cache_dir, reporthook)
        self._root_url = root_url
        self._collections_names = self._read_collection_names()
        self._collections_list = [EncodeCollection(self, n) for n in self._collections_names]
        self._collections_dict = {c.name: c for c in self._collections_list}
        for c in self._collections_list:
            self.__dict__[c.name] = c
    
    def _read_collection_names(self):
        '''Read a list of collections from the page at encode_root_url.'''
        if not self._cache.has_file("collections.json"):
            file_name = self._cache.fetch_url(self._root_url, 'index.html')
            file_content = open(file_name).read()
            p = re.compile('<a href="wgEncode([^"]+)/">')
            self._cache.json_dump(p.findall(file_content), "collections.json")
        return self._cache.json_load("collections.json")
    
    def __iter__(self):
        '''Iterates over all collections.'''
        for c in self._collections_list:
            yield c

    def __getitem__(self, name):
        '''Returns the EncodeCollection for a given name. Raises KeyError if name invalid.'''
        return self._collections_dict[name]
    
    
class EncodeCollection(object):
    '''The object, representing a ``collection'', i.e. a subdirectory under the ENCODE root path.'''
    
    def __init__(self, encode, name):
        '''You should not create this object manually.'''
        self._encode = encode
        self._files_list = None
        self.name = name
        self.url = '%s/wgEncode%s' % (encode._root_url, name)
        self._cache_path = 'wgEncode%s' % name
    
    def _init(self):
        '''Read a list of files with metadata from the server.'''
        if self._files_list is not None:
            return
        fn = self._encode._cache.fetch_url('%s/files.txt' % self.url, '%s/files.txt' % self._cache_path)
        self._files_list = []
        self._files_dict = {}
        with open(fn) as f:
            for ln in f:
                # A line looks as follows:
                # wgEncodeAwgSegmentationChromhmmGm12878.bed.gz<tab>project=wgEncode; composite=wgEncodeAwgSegmentation; dataType=Combined; cell=GM12878; dataVersion=ENCODE Jan 2011 Freeze; tableName=wgEncodeAwgSegmentationChromhmmGm12878; type=bed; size=9.9M
                filename, attrs = ln.split('\t')
                fdata = {}
                for field in attrs.split(';'):
                    try:
                        field_name, field_value = field.strip().split('=',1)
                    except ValueError:
                        # There's one particular place where this parsing fails:
                        assert filename == 'wgEncodeCshlLongRnaSeqSknshraCellPapFastqRd2Rep1.fastq.gz'
                        assert field.strip() == 'wgEncodeCshlLongRnaSeqSknshraCellPapFastqRd2Rep1'
                    fdata[field_name] = field_value
                assert 'filename' not in fdata
                fdata['filename'] = filename
                self._files_list.append(EncodeFile(self, fdata, self._make_name_for_file(filename)))
                
        self._files_dict = {f.name: f for f in self._files_list}
        for f in self._files_list:
            self.__dict__[f.name] = f
    
    def _make_name_for_file(self, filename):
        '''Strip the wgEncodeBlabla prefix from the filename, to give a more concise "name" to a file to access it.
        This is somewhat hackish. Most collections consistently use the collection name as the file prefix,
        but there are exceptions.'''
        
        if self.name.endswith('Uniform'):
            prefix_len = len('wgEncode') + len(self.name) - 7
        elif self.name.startswith('Gencode'):
            prefix_len = len('wgEncodeGencode')
        elif self.name.endswith('Mapability') or 'RegMark' in self.name:
            prefix_len = len('wgEncode')
        elif self.name.endswith('TfbsClustered'):
            prefix_len = len('wgEncodeRegTfbs')
        elif self.name == 'Uw5C':
            prefix_len = len('wgEncodeUw5c')
        elif self.name == 'AwgDnaseMasterSites':
            prefix_len = len('AwgDnaseMaster')
        else:
            assert filename.startswith('wgEncode%s' % self.name), "Error on %s" % filename            
            prefix_len = len('wgEncode') + len(self.name)
            
        return filename[prefix_len:].split('.')[0]
    
    def __getattr__(self, name):
        self._init()
        return self.__dict__[name]
    
    def __iter__(self):
        '''Iterates over all files in a collection.'''
        self._init()  # We do not want to init a collection on constructor, do it lazily.
        for f in self._files_list:
            yield f

    def __getitem__(self, name):
        '''Returns the EncodeFile for a given name. Raises KeyError if name invalid.'''
        self._init() # Init lazily
        return self._files_dict[name]    
    
    def __lt__(self, o):
        '''Collections are compared by their names.'''
        return self.name < o
    
class EncodeFile(object):
    '''A class representing an ENCODE data file'''
    
    def __init__(self, collection, attrs, name):
        '''You should not create this object manually. Use the root Encode object to access instances of EncodeFile.'''
        self._collection = collection
        self._attrs = attrs
        self.name = name
        self.url = '%s/%s' % (collection.url, attrs['filename'])
        self._cache_path = '%s/%s' % (collection._cache_path, attrs['filename'])
        self.local_path = os.path.abspath(self._collection._encode._cache.local_path(self._cache_path))
        self.local_url = 'file://%s' % self.local_path
        
    def __getitem__(self, name):
        return self._attrs[name]
    
    def keys(self):
        return self._attrs.keys()
    
    def fetch(self, force=False):
        '''Download file into cache. Returns ``self`` for convenient chaining of calls.
        
        KwArgs:
            force (bool): When False (default), the file will not be redownloaded if already in cache.
        Raises:
            Whatever ``urllib.urlretrieve`` may raise.
        '''
        self._collection._encode._cache.fetch_url(self.url, self._cache_path)
        return self
    
    def open(self):
        '''Opens the file for reading in binary. If the file is available in cache, opens from cache. Otherwise opens via ``urlopen`` from the web without downloading to cache.'''
        if os.path.exists(self.local_path):
            return open(self.local_path, 'rb')
        else:
            return with_closing_contextmanager(urllib.urlopen(self.url))
    
    def open_text(self):
        '''Same as ``open``, but will open file in text mode. In addition, if the file is ``.gz``, will automatically unpack (i.e. will return the result of ``GzipFile.open``).'''
        if os.path.exists(self.local_path):
            if self.local_path.endswith('.gz'):
                return gzip.open(self.local_path)
            else:
                return open(self.local_path, 'r')
        else:
            f = urllib.urlopen(self.url)
            if self.url.endswith('.gz'):
                f = GzipInputStream(fileobj=f)                
            return with_closing_contextmanager(f)
    
    def read_as_intervaltree(self):
        '''
        Reads the data from a 'bed' file into an ``intervaltree_bio.GenomeIntervalTree`` data structure.
        Similarly to ``open`` and ``open_text`` it won't download file to cache, if it is not there.
        Reads the whole file to memory during its work.
        
        The file must be a `bed` or `bed.gz` file.
        The ``data`` field of each interval will contain the result of ``ln.split('\t')[3:]`` applied to the corresponding line of the ``bed`` file.
        
        Returns:
            a GenomeIntervalTree instance.
        '''
        assert self['type'] in ['bed', 'narrowPeak', 'broadPeak']
        
        with self.open_text() as f:
            gtree = GenomeIntervalTree.from_bed(fileobj=f)
        return gtree
