#!/usr/bin/env python
import mkvparse
import sys
import traceback
import binascii

def pstderr(*args):
    #if sys.version < '3':
        sys.stderr.write(str(args[0])+"\n")
    #else:
    #    print(file=sys.stderr, *args)

class MatroskaConcatenator(mkvparse.MatroskaHandler):
    def __init__(self, f):
        self.f = f

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
        pass

    def begin_handling_ebml_element(self, id_, name, type_, headersize, datasize):
        pstderr("        %s %d %d"%(name, headersize, datasize))
        if type_==1:
            return 'read tree'
        return 'pass'
    
    def element_data_available(self, id_, name, type, headersize, data):
        #pstderr("        %s %d %d"%(name, headersize, data))
        if name=='EBML': return 'read tree'

if __name__ == '__main__':
    if sys.version >= '3':
        sys.stdout = sys.stdout.detach()

    concat = MatroskaConcatenator(sys.stdout)
    
    for i in sys.argv[1:]:
        pstderr("Opening %s" % i);
        with open(i,"rb") as f:
            try:
                mkvparse.mkvparse(f, concat)
            except:
                traceback.print_exc()
