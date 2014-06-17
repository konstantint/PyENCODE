'''
A hack over the standard GzipFile implementation, which makes it possible
to use it over a stream without seek/tell (i.e. urlopen'ed stuff)

See: http://www.enricozini.org/2011/cazzeggio/python-gzip/

Copyright 2014, Konstantin Tretyakov
Licensed under MIT.
'''
import gzip
import zlib

class GzipInputStream(gzip.GzipFile):
    '''This is the same as GzipFile, with a couple of functions hacked to avoid using seek/tell of the base fileobj.
    
    You should not seek/rewind or do something similar on this object.
    '''
    
    def __repr__(self):
        s = repr(self.fileobj)
        return '<gzip-input-stream ' + s[1:-1] + ' ' + hex(id(self)) + '>'
    
    def _read(self, size=1024):
        if self.fileobj is None:
            raise EOFError, "Reached EOF"

        if self._new_member:
            # If the _new_member flag is set, we have to
            # jump to the next member, if there is one.
            #
            # First, check if we're at the end of the file;
            # if so, it's time to stop; no more members to read.
            ## XXX: This part is commented out wrt original GzipFile implementation
            #pos = self.fileobj.tell()   # Save current position
            #self.fileobj.seek(0, 2)     # Seek to end of file
            #if pos == self.fileobj.tell():
            #    raise EOFError, "Reached EOF"
            #else:
            #    self.fileobj.seek( pos ) # Return to original position
            ## XXX: End of modified block
            
            self._init_read()
            self._read_gzip_header()
            self.decompress = zlib.decompressobj(-zlib.MAX_WBITS)
            self._new_member = False

        # Read a chunk of data from the file
        buf = self.fileobj.read(size)

        # If the EOF has been reached, flush the decompression object
        # and mark this object as finished.

        if buf == "":
            uncompress = self.decompress.flush()
            self._read_eof()
            self._add_read_data( uncompress )
            raise EOFError, 'Reached EOF'

        uncompress = self.decompress.decompress(buf)
        self._add_read_data( uncompress )

        if self.decompress.unused_data != "":
            # Ending case: we've come to the end of a member in the file,
            # so seek back to the start of the unused data, finish up
            # this member, and read a new gzip header.
            # (The number of bytes to seek back is the length of the unused
            # data, minus 8 because _read_eof() will rewind a further 8 bytes)
            # XXX: Original version started reading a new member
            # XXX: We say that the file end is reached, instead
            # XXX: In general this is wrong, but we presume that all
            # XXX: ENCODE files are OK (i.e. consist of a single member only)
            #self.fileobj.seek( -len(self.decompress.unused_data)+8, 1)

            ## Check the CRC and file size, and set the flag so we read
            ## a new member on the next call
            ##self._read_eof()
            ##self._new_member = True
            raise EOFError, 'Reached EOF' # XXX: Added this line
            # XXX: End of changed block.
            
    def _read_eof(self):
        pass
        ## There was CRC & Size verification, which had to be dropped as it uses seek.
        ## We've read to the end of the file, so we have to rewind in order
        ## to reread the 8 bytes containing the CRC and the file size.
        ## We check the that the computed CRC and size of the
        ## uncompressed data matches the stored values.  Note that the size
        ## stored is the true file size mod 2**32.
        #self.fileobj.seek(-8, 1)
        #crc32 = read32(self.fileobj)
        #isize = read32(self.fileobj)  # may exceed 2GB
        #if crc32 != self.crc:
        #    raise IOError("CRC check failed %s != %s" % (hex(crc32),
        #                                                 hex(self.crc)))
        #elif isize != (self.size & 0xffffffffL):
        #    raise IOError, "Incorrect length of data produced"
        #
        ## Gzip files can be padded with zeroes and still have archives.
        ## Consume all zero bytes and set the file position to the first
        ## non-zero byte. See http://www.gzip.org/#faq8
        #c = "\x00"
        #while c == "\x00":
        #    c = self.fileobj.read(1)
        #if c:
        #    self.fileobj.seek(-1, 1)

    def seekable(self):
        return False
