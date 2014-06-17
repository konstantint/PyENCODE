'''
A simple cache class for downloading URLs to disk, if necessary.

Copyright 2014, Konstantin Tretyakov
Licensed under MIT.
'''
import json
import os
import os.path
import urllib

class HttpException(Exception):
    pass

class ErrorAwareURLOpener(urllib.FancyURLopener):
  def http_error_default(self, url, fp, errcode, errmsg, headers):
    raise HttpException("404")
_urlopener = ErrorAwareURLOpener()



class Cache(object):
    '''A simple disk-based URL cache. Note that it is *not* safe for any kind of multithreading or multiprocessing (i.e. you should not use several instances with the same ``root_dir`` in parallel, as no locking of files is done to ensure correct operation).'''
    
    def __init__(self, root_dir, reporthook=None):
        '''
        Create the instance of a cache.
        
        Args:
            root_dir (str): The root directory to store files. Will be created if not existing.
        KwArgs:
            reporthook (function):  A reporthook provided to ``urlopen`` for tracking download progress.
                Must be a function ``(block_count, block_size, total_bytes)``, see ``urlretrieve`` documentation.
        Raises:
            WindowsError or IOError or other system errors: if cache directory cannot be created or written to
        '''
        self.root_dir = root_dir
        self.reporthook = reporthook
        if not os.path.isdir(root_dir):
            os.mkdir(root_dir)
    
    def fetch_url(self, source_url, filename, force=False):
        '''
        Downloads the file from ``source_url`` into ``filename`` (under cache directory), unless ``filename`` already exists.
        
        Returns the absolute path of ``filename``.
        
        Args:
            source_url (str): Url to retrieve data from.
            filename (str): filename (relative to ``root_dir``) to store file to.
            force (bool): when True, the file will be redownloaded even if it is already available
        Raises:
            Any exceptions that ``urllib.urlretrieve`` may raise.
        '''
        target_file = self.local_path(filename)
        if not os.path.isfile(target_file) or force:
            target_dir = os.path.dirname(target_file)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            (downloaded_filename, headers) = _urlopener.retrieve(source_url, target_file, reporthook=self.reporthook)
        return os.path.abspath(target_file)
        
    def has_file(self, filename):
        '''Checks whether ``filename`` is present in cache.'''
        return os.path.exists(os.path.join(self.root_dir, filename))
    
    def local_path(self, filename):
        '''Return the local path (not necessarily abspath) of a file as it (or would be) is stored in cache.'''
        return os.path.join(self.root_dir, filename)
    
    def json_dump(self, obj, filename):
        '''Dump ``obj`` to the ``filename`` in cache as JSON.'''
        target_file = os.path.join(self.root_dir, filename)
        target_dir = os.path.dirname(target_file)
        if not os.path.exists(target_dir):
            os.mkdirs(target_dir)
        with open(target_file, 'wb') as f:
            json.dump(obj, f)
    
    def json_load(self, filename):
        '''Load data from ``filename`` in cache as JSON.'''
        with open(os.path.join(self.root_dir, filename), 'rb') as f:
            return json.load(f)
    
    def erase(self, filename):
        '''Deletes given file from cache. Will raise an exception, if file does not exist.'''
        os.unlink(os.path.join(self.root_dir, filename))    