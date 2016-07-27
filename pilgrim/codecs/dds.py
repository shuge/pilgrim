# -*- coding: utf-8 -*-
"""
A loader for (some) .DDS (DirectX8 texture) files

The DDS file format is described (somewhat) at:
 http://msdn.microsoft.com/en-us/library/ee418142(VS.85).aspx
 https://msdn.microsoft.com/en-us/library/windows/desktop/dn424129(v=vs.85).aspx

The DTX1 texture format is described at:
 http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_compression_s3tc.txt
"""

from struct import unpack, pack

from PIL import Image, ImageFile



from ..decoders import dxtc

try:
    xrange(1) # Python2
except NameError:
    xrange = range # Python 3


# dwFlags constants
DDSD_CAPS        = 1
DDSD_HEIGHT      = 2
DDSD_WIDTH       = 4
DDSD_PITCH       = 8
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE  = 0x80000
DDSD_DEPTH       = 0x800000

DDSD_EXPECTED = DDSD_CAPS + DDSD_HEIGHT + DDSD_WIDTH + DDSD_PIXELFORMAT

# ddpfPixelFormat.dwFlags constants
DDPF_ALPHAPIXELS = 1
DDPF_FOURCC      = 4
DDPF_RGB         = 0x40

# ddsCaps.dwCaps1 constants
DDSCAPS_COMPLEX  = 8
DDSCAPS_TEXTURE  = 0x1000
DDSCAPS_MIPMAP   = 0x400000

DDSCAPS_EXPECTED = DDSCAPS_TEXTURE


class DDS(ImageFile.ImageFile):
    format = "DDS"
    format_description = "DirectX8 DDS texture file"

    def _open(self):
        self._loaded = 0

        # Check header
        header = self.fp.read(128)
        if header[:4] != b"DDS ":
            raise ValueError("Not a DDS file")

        dwSize, dwFlags, dwHeight, dwWidth, dwPitchLinear, dwDepth, dwMipMapCount, ddpfPixelFormat, ddsCaps = unpack("<IIIIIII 44x 32s 16s 4x", header[4:])
        self.size = dwWidth, dwHeight

        if dwSize != 124:
            raise ValueError("Expected dwSize == 124, got %d" % (dwSize))

        if (dwFlags & DDSD_EXPECTED) != DDSD_EXPECTED:
            raise ValueError("Unsupported image flags: %08x" % (dwFlags))

        pf_dwSize, pf_dwFlags, pf_dwFourCC, pf_dwRGBBitCount, pf_dwRBitMask, pf_dwGBitMask, pf_dwBBitMask, pf_dwRGBAlphaBitMask = unpack("<II4sIIIII", ddpfPixelFormat)
        if pf_dwSize != 32:
            raise ValueError("Expected pf_dwSize == 32, got %d" % (pf_dwSize))

        caps_dwCaps1, caps_dwCaps2 = unpack("<II 8x", ddsCaps)
        if (caps_dwCaps1 & DDSCAPS_EXPECTED) != DDSCAPS_EXPECTED:
            raise ValueError("Unsupported image caps: %08x" % (caps_dwCaps1))

        # check for DXT1
        if (pf_dwFlags & DDPF_FOURCC != 0):
            if pf_dwFourCC == b"DXT1":
                if (pf_dwFlags & DDPF_ALPHAPIXELS != 0):
                    raise NotImplementedError("DXT1 with Alpha not supported yet")
                else:
                    self.mode = "RGB"
                    self.load = self._loadDXTOpaque
            else:
                raise ValueError("Unsupported FOURCC mode: %s" % (pf_dwFourCC))

        else:
            # XXX is this right? I don't have an uncompressed dds to play with
            _dwSize, _dwFlags, dwFourCC, dwRGBBitCount, dwRBitMask, dwGBitMask, dwBBitMask, dwABitMask = unpack('<IIIIIIII', ddpfPixelFormat)
            _mode = [None, None, None, None]
            for mask,channel in zip([dwRBitMask, dwGBitMask, dwBBitMask, dwABitMask],'RGBA'):
                if mask == 0x00000000: # hack no-alpha case
                    _mode[3] = channel
                elif mask == 0xff000000:
                    _mode[3] = channel
                elif mask == 0x00ff0000:
                    _mode[2] = channel
                elif mask == 0x0000ff00:
                    _mode[1] = channel
                elif mask == 0x000000ff:
                    _mode[0] = channel
                else:
                    raise Exception('Unknow mask value')
            
            if _dwFlags % 2 != 0: #DDPF_ALPHAPIXELS
                self.mode = "RGBA"
                self._mode = ''.join(_mode)
            else:
                self.mode = 'RGB'
                self._mode =''.join( _mode[:3])
            
            self.load = self._basicLoad
            # Construct the tile
            #self.tile = [("raw", (0, 0, dwWidth, dwHeight), 128, ("RGBX", dwPitchLinear - dwWidth, 1))]

    def _loadDXTOpaque(self):
        if self._loaded: return

        # one entry per Y row, we join them up at the end
        data = []
        self.fp.seek(128) # skip header

        linesize = (self.size[0] + 3) // 4 * 8 # Number of data byte per row
        
        
        baseoffset = 0
        for yb in xrange((self.size[1] + 3) // 4):
            linedata = self.fp.read(linesize)
            decoded = dxtc.decodeDXT1(linedata) # returns 4-tuple of RGB lines
            for d in decoded:
                # Make sure that if we have a texture size that's not a
                # multiple of 4 that we correctly truncate the returned data
                data.append(d[:self.size[0]*3])

        # Now build the final image from our data strings
        #data = "".join(data[:self.size[1]])
        data = b"".join(data[:self.size[1]])
        self.im = Image.core.new(self.mode, self.size)
        # self.fromstring(data)
        self.frombytes(data)
        self._loaded = 1
    def _basicLoad(self):
        if self._loaded: 
            return
        
        self.fp.seek(128)
        data = self.fp.read()
        self.im = Image.core.new(self.mode, self.size)
        self.frombytes(self._basic_decode(data, self._mode))
        self._loaded = 1
    def _basic_decode(self, data, mode='RGB'):
        # data are bytes
        #if mode in ['RGB','RGBA']: # base
        #    return data 
        len_mode = len(mode)
        block_count = len(data)//len_mode
        assert len(data) % len_mode == 0
        
        block_list = [data[i*len_mode : (i+1)*len_mode] for i in range(block_count)]
        
        r_index = mode.index('R')
        g_index = mode.index('G')
        b_index = mode.index('B')
        
        if len_mode == 3: # RBG,BRG...
            new_block_list = [b''.join([pack('B',block[r_index]), pack('B',block[g_index]), pack('B',block[b_index])]) for block in block_list]
            
        elif len_mode == 4: #ARGB,GAGB...
            a_index = mode.index('A')
            new_block_list = [b''.join([pack('B',block[r_index]), pack('B',block[g_index]), pack('B',block[b_index]), pack('B',block[a_index])]) for block in block_list]
            
        return b''.join(new_block_list)

        