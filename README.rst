=======================================================================
PyENCODE: Convenience package for accessing ENCODE project data at UCSC
=======================================================================

This is a convenience package for accessing the raw data of the `ENCODE (Encyclopedia of DNA Elements) project <http://genome.ucsc.edu/ENCODE/>`_.

The raw ENCODE files are organized in a fairly straightforward structure under `this URL <http://hgdownload.cse.ucsc.edu/goldenPath/hg19/encodeDCC/>`_. The files are divided into collections ("composites"), each in its own subdirectory. The subdirectory of each collection keeps the metadata of all files in a text file named ``files.txt``. For example, the `genome segmentation <http://genome.ucsc.edu/cgi-bin/hgTrackUi?db=hg19&g=wgEncodeAwgSegmentation>`_ data is kept under ``ROOT_URL/wgEncodeAwgSegmentation``. In particular, the segmentation obtained using ``Combined`` method on the ``K562`` cells is kept in a compressed ``BED``-file named ``ROOT_URL/wgEncodeAwgSegmentation/wgEncodeAwgSegmentationCombinedK562.bed.gz``.

In principle, downloading and reading the file is rather straightforward. What this package offers in addition is a slightly more streamlined way of listing files, caching them, and reading file metadata. For example, the following code will download the abovementioned file into cache, then open it and index as an interval tree::

    >> from pyencode import Encode
    >> e = Encode(cache_dir = 'wgEncode')
    >> gtree = e.AwgSegmentation.CombinedK562.fetch().read_as_intervaltree()
    
As another example, here is how to list and pre-download all files in the ``AwgSegmentation`` collection into cache::

    >> for f in e.AwgSegmentation:
    >>    print("%s-%s" % (f['cell'], f['dataType']))
    >>    f.fetch()

Installation
------------

The easiest way to install most Python packages is via ``easy_install`` or ``pip``::

    $ pip install PyENCODE

Usage
-----

The main object, provided by the package is ``pyencode.Encode``. You create an instance, specifying the root of a cache directory::

    >> from pyencode import Encode
    >> e = Encode(cache_dir = 'wgEncode')

The default value for ``cache_dir`` is ``~/.pyencode``. The resulting object works as a dictionary, with keys being the different file collections within ENCODE::

    >> c['AwgSegmentation']
    
Alternatively, you can use field names instead of dictionary keys, i.e. ``e['AwgSegmentation']`` is the same as ``e.AwgSegmentation``. To iterate over all collections, simply do::

    >> for c in e:
    >>    print(c.name)

Each element of the ``Encode`` object is a ``EncodeCollection`` object, which is acts as a collection of ``EncodeFile`` elements::

    >> for f in e.AwgSegmentation:
    >>     print(f.name)

Simiarly, dictionary-style or field name access can be used to retrieve files in a collection: ``e.AwgSegmentation['CombinedK562']`` or ``e.AwgSegmentation.CombinedK562``.

Each ``EncodeFile`` is a dictionary of file metadata fields::

    >> print(e.AwgSegmentation.CombinedK562['cell'])

In addition, ``EncodeFile`` provides a set of convenience fields and methods:

  * ``fetch(force=False)`` - Download file into cache. Returns the ``EncodeFile`` object for convenient chaining of calls. When``force`` is ``False``, file will not be redownloaded if already in cache.
  * ``keys()`` - Set of all file attributes that can be accessed via ``[]``.
  * ``url`` - Return the URL of the file online.
  * ``local_url`` - The URL of the cached copy. It is not guaranteed that the file exists, so it is often more practical to do ``.fetch().local_url``.
  * ``local_path`` - Return the path of the locally cached copy. It is not guaranteed that the file exists. 
  * ``open()`` - Open the file in binary mode for reading. If the file is not in cache, it is *not* downloaded to cache and opened from the web (so, it is often more practical to do ``.fetch().open()``).
  * ``open_text()`` - Open the file in text mode for reading. If the file is not in cache it is *not* downloaded to cache and opened from the web. If the file is a `.gz` file, it is automatically unpacked (i.e. the returned file instance is an opened `GzipFile`).
  * ``read_as_intervaltree()`` - Read a ``BED`` file into an ``intervaltree.bio.GenomeIntervalTree`` data structure. Simiarly, if the file is not in cache, it is not automatically downloaded.

Note that ``Encode`` is not safe for doing multithreading or multiprocessing, unless all the necessary files are already cached.


Copyright & License
-------------------

Copyright 2014, Konstantin Tretyakov

MIT License.