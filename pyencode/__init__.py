'''
=======================================================================
PyENCODE: Convenience package for accessing ENCODE project data at UCSC
=======================================================================

This is a convenience package for accessing the raw data of the `ENCODE (Encyclopedia of DNA Elements) project <http://genome.ucsc.edu/ENCODE/>`_.

The basic usage examples are the following:

 * List ENCODE file collections::
 
    >>> from pyencode import Encode
    >>> e = Encode()
    >>> for collection in e:
    ...    print(collection.name)
    AffyRnaChip
    AwgDnaseUniform
    ...
    UwTfbs
    
  * List files in a single collection::

    >>> for f in e.AwgSegmentation:
    ...    print(f.name, f['cell'], f.url)
    ('ChromhmmGm12878', 'GM12878', u'http://...
    ...
    ('SegwayK562', 'K562', u'http://...
    
  * Download certain file to cache and open for reading in binary::
  
    >>> f = e.AwgSegmentation.CombinedK562.fetch().open()

Copyright 2014, Konstantin Tretyakov
Licensed under MIT.
'''

from pyencode.encode import Encode

