#!/usr/bin/env python
import mkvparse
import sys
import traceback
import binascii
import os
import io
import mkvgen

def pstderr(*args):
    #if sys.version < '3':
        sys.stderr.write(str(args[0])+"\n")
    #else:
    #    print(file=sys.stderr, *args)

class MatroskaConcatenator(mkvparse.MatroskaHandler):
    def __init__(self, f):
        self.f = f
        self.prev_uuid = None
        self.cur_uuid = os.urandom(16)
        self.next_uuid = os.urandom(16)
        self.headerpart = None
        self.info_section_size = None

    def tracks_available(self):
        pstderr("    Tracks info:")
        try:
            for k in self.tracks:
                t=self.tracks[k]
                pstderr("        %d %s %s"%(k, t['type'][1], t['CodecID'][1]))
        except:
            pstderr("        can't print")

    def segment_info_available(self):
        pstderr("    Segment info:")
        try:
            for (k,(t_,v)) in self.segment_info:
                if t_ == mkvparse.EbmlElementType.BINARY: v = binascii.hexlify(v)
                pstderr("        %s: %s"%(k,v))
        except:
            pstderr("        can't print")

    def frame(self, track_id, timestamp, data, more_laced_frames, duration, keyframe, invisible, discardable):
        pass


    def before_handling_an_element(self):
        self.headerpart = self.fin.peek(100)
        self.headerpart = self.fin.peek(100)
        pstderr("peeked %d bytes"%(len(self.headerpart)))
        pass

    def begin_handling_ebml_element(self, id_, name, type_, headersize, datasize):
        pstderr("        %s %d(%s) %d"%(name, headersize, binascii.hexlify(self.headerpart[:headersize]), datasize))
        if   name=="EBML": return type_
        elif name=="Segment": 
            remainingfilesize = self.currentfilesize - self.fin.tell()
            pstderr("           remaining file size: %d  segment data size: %s"%(remainingfilesize, str(datasize)))
            if datasize  <= 0 and remainingfilesize > 0:
                datasize = remainingfilesize
                pstderr("          fixed segment size based on file size")
            self.f.write(mkvgen.ebml_element(0x18538067,"",datasize)) # Segment header with known length

            return mkvparse.EbmlElementType.JUST_GO_ON
        #elif name=="Info":
        #    self.info_section_size = datasize
        #    return mkvparse.EbmlElementType.JUST_GO_ON
        
        self.headersize = headersize
        return mkvparse.EbmlElementType.BINARY
    
    def ebml_top_element(self, id_, name, type_, data):
        #pstderr("        %s %d %d"%(name, headersize, data))
        if   name=="EBML": return
        elif name=="Segment": return
        #elif name=="Info": return
        #elif name=="SeekHead": return # invalidated by changing the Info

        #pstderr("type:"+str(type(data)))

        # just copy this element to output
        #header = self.headerpart [ : self.headersize];
        #pstderr("writing header: %s at %s; data len: %d"%(binascii.hexlify(header), self.f.tell(), len(data)))
        #self.f.write(header)
        #self.f.write(data)
        self.f.write(mkvgen.ebml_element(id_,data))
        

if __name__ == '__main__':
    if sys.version >= '3':
        sys.stdout = sys.stdout.detach()

    mkvgen.write_ebml_header(sys.stdout, "matroska", 2, 2)

    concat = MatroskaConcatenator(sys.stdout)
    
    for i in sys.argv[1:]:
        pstderr("Opening %s" % i);
        with io.open(i,"rb", buffering=True) as f:
            try:
                concat.fin = f
                concat.currentfilesize = os.path.getsize(i)
                mkvparse.mkvparse(concat.fin, concat)
            except:
                traceback.print_exc()
