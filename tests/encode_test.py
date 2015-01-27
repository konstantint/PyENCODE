'''
PyENCODE: Test module.

Meant for use with py.test.
Write each test as a function named test_<something>.
Read more here: http://pytest.org/

Copyright 2014, Konstantin Tretyakov
Licensed under MIT
'''
from pyencode import Encode
import os
import pytest
import shutil

# If True, some tests will use ~/.pyencode as cache directory.
# This will avoid redownloading data every time the tests are run.
# When False, a clean temporary cache directory will always be created with each test run.
USE_LOCAL_CACHE = True

# NB: Encode data seems to change from time to time, tests may start failing because of that.

def test_encode():
    CACHE_DIR = 'PyEncode_cache_dir'
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    
    COLLECTIONS = ['AffyRnaChip', 'AwgDnaseUniform', 'AwgSegmentation', 'AwgTfbsUniform', 'BroadHistone', 'BroadHmm', 'BuOrchid', 'CaltechRnaSeq', 'CshlLongRnaSeq', 'CshlShortRnaSeq', 'DukeAffyExon', 'FsuRepliChip', 'GencodeV4', 'GencodeV7', 'GencodeV10', 'GencodeV11', 'GencodeV12', 'GisChiaPet', 'GisDnaPet', 'GisRnaPet', 'GisRnaSeq', 'HaibGenotype', 'HaibMethyl450', 'HaibMethylRrbs', 'HaibRnaSeq', 'HaibTfbs', 'Mapability', 'OpenChromChip', 'OpenChromDnase', 'OpenChromFaire', 'OpenChromSynth', 'RegDnaseClustered', 'RegMarkH3k4me1', 'RegMarkH3k4me3', 'RegMarkH3k27ac', 'RegTfbsClustered', 'RegTxn', 'RikenCage', 'SunyAlbanyGeneSt', 'SunyAlbanyTiling', 'SunyRipSeq', 'SunySwitchgear', 'SydhHistone', 'SydhNsome', 'SydhRnaSeq', 'SydhTfbs', 'UchicagoTfbs', 'UmassDekker5C', 'UncBsuProt', 'UncBsuProtGenc', 'Uw5C', 'UwAffyExonArray', 'UwDgf', 'UwDnase', 'UwHistone', 'UwRepliSeq', 'UwTfbs', 'AwgDnaseMasterSites']
    
    e = Encode(CACHE_DIR)
    assert sorted(e._collections_names) == sorted(COLLECTIONS)
    
    # Iteration
    names = []
    for c in e:
        names.append(c.name)
    assert sorted(names) == sorted(COLLECTIONS)
    
    # Key access
    assert e['AffyRnaChip'].name == 'AffyRnaChip'
    with pytest.raises(KeyError):
        e['AffyRna']

    # Field access
    assert e.AffyRnaChip.name == 'AffyRnaChip'
    with pytest.raises(AttributeError):
        e.AffyRna

    # Pick the smallest of the files to test things on (to avoid large downloads)
    testFile = e.AwgTfbsUniform.HaibH1hescGabpPcr1xUniPk
    assert not os.path.exists(testFile.local_path)
    
    # Test opening from URL
    with testFile.open() as f:
        assert f.read(30) == '\x1f\x8b\x08\x089}dQ\x00\x03wgEncodeAwgTfbsHaibH'
        assert not os.path.exists(testFile.local_path)
    with testFile.open() as f:
        assert len(f.read()) == 113578
        assert not os.path.exists(testFile.local_path)    
    with testFile.open_text() as f:
        ln = f.readline()
        assert ln[0:20] == 'chr13\t41345193\t41345'
        assert len(ln) == 74
        assert not os.path.exists(testFile.local_path)
    
    # Now for local file
    testFile.fetch()
    assert os.path.exists(testFile.local_path)
    with testFile.open() as f:
        assert f.read(30) == '\x1f\x8b\x08\x089}dQ\x00\x03wgEncodeAwgTfbsHaibH'
        assert len(f.name) != ''   # urlopen'ed file objects don't have the name attribute or have it ''
    with testFile.open() as f:
        assert len(f.read()) == 113578    
        assert len(f.name) != ''
    with testFile.open_text() as f:
        ln = f.readline()
        assert ln[0:20] == 'chr13\t41345193\t41345'
        assert len(ln) == 74
        assert len(f.name) != ''
    
    # Check how non-gz files are handled
    testFile = e.UncBsuProtGenc.Gm12878CytosolIngelpepMapGcFt
    
    #  - Read from URL
    assert not os.path.exists(testFile.local_path)
    with testFile.open() as f:
        assert f.read(10) == '\x87\x89\xf2\xeb\x00\x04\x00\n\x00\x00'
    with testFile.open_text() as f:
        assert f.read(10) == '\x87\x89\xf2\xeb\x00\x04\x00\n\x00\x00' # Must be the same result as with open()
    assert not os.path.exists(testFile.local_path)
    
    #  - Read from local file
    testFile.fetch()
    assert os.path.exists(testFile.local_path)
    with testFile.open() as f:
        assert f.read(10) == '\x87\x89\xf2\xeb\x00\x04\x00\n\x00\x00'
    with testFile.open_text() as f:
        assert f.read(10) == '\x87\x89\xf2\xeb\x00\x04\x00\n\x00\x00' # Must be the same result as with open()
    assert os.path.exists(testFile.local_path)
    
    # List all files
    if USE_LOCAL_CACHE:
        e = Encode()
    all_files = [_f for _c in e for _f in _c]
    assert len(all_files) == 25231  # Total number of files in ENCODE
    
    # Reading file as an interval tree:
    testFile = e.AwgTfbsUniform.HaibH1hescGabpPcr1xUniPk
    itree = testFile.read_as_intervaltree()
    result = list(itree['chr1'].search(249120565))
    assert len(result) == 1
    assert result[0].begin == 249120411
    

def _test_promotorsearch():
    # Realistic example: find a promotor of a given gene ('NANOG', for example)
    # It is slow, so you don't want to run it too much.
    
    from intervaltree_bio import GenomeIntervalTree, UCSCTable
    # Download refGene table
    refGene = GenomeIntervalTree.from_table(url='http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/refGene.txt.gz', parser=UCSCTable.REF_GENE)
    # Find the NANOG gene
    nanog = [i for chrom in refGene for i in refGene[chrom] if i.data['name2'] == 'NANOG']
    nanog = nanog[0]
    
    # Download genome segmentation table
    e = Encode()
    segments = e.AwgSegmentation.CombinedHepg2.fetch().read_as_intervaltree()
    
    # Find the segmentation of the NANOG transcript +- 10kb
    results = segments[nanog.data['chrom']].search(nanog.begin-10000, nanog.end+10000)
    
    # Leave the promotor/promotor flanking segments only
    results = [i for i in results if i.data[0] in ['PF', 'P']]
    print results
