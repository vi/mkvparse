#!/usr/bin/env python
import mkvparse
import sys
import binascii
import datetime

class MatroskaUser(mkvparse.MatroskaHandler):      
    def tracks_available(self):
        print("Tracks info:")
        for k in self.tracks:
            t=self.tracks[k]
            print("    %d %s %s"%(k, t['type'][1], t['CodecID'][1]))

    def segment_info_available(self):
        print("Segment info:")
        for (k,(t_,v)) in self.segment_info:
            if t_ == mkvparse.EbmlElementType.BINARY: v = binascii.hexlify(v)
            if t_ == mkvparse.EbmlElementType.DATE: v = str(datetime.datetime.utcfromtimestamp(v))
            print("    %s: %s"%(k,v))

    def frame(self, track_id, timestamp, data, more_laced_frames, duration, keyframe, invisible, discardable):
        addstr=""
        if duration:
            addstr="dur=%.6f"%duration
        if keyframe: addstr+=" key"
        if invisible: addstr+=" invis"
        if discardable: addstr+=" disc"
        print("Frame for %d ts=%.06f l=%d %s len=%d data=%s..." %
                (track_id, timestamp, more_laced_frames, addstr, len(data), binascii.hexlify(data[0:10])))

if __name__ == '__main__':
    if sys.version >= '3':
        sys.stdin = sys.stdin.detach()

    # Reads mkv input from stdin, parse it and print details to stdout
    mkvparse.mkvparse(sys.stdin, MatroskaUser())


# Output example:
'''
Segment info:
    2ad7b1: B@
    MuxingApp: libebml v1.0.0 + libmatroska v1.0.0
    WritingApp: mkvmerge v4.0.0 ('The Stars were mine') built on Jun  6 2010 16:18:42
    4489: G6I
    4461: ......
    SegmentUID: 9d516a0f927a12d286e1502d23d0fdb0
Tracks info:
    1 video V_MPEG4/ISO/AVC
    2 audio A_AAC
    3 subtitle S_TEXT/UTF8
    4 subtitle S_TEXT/UTF8
    5 subtitle S_TEXT/UTF8
    6 subtitle S_TEXT/UTF8
    7 subtitle S_TEXT/UTF8
    8 subtitle S_TEXT/UTF8
    9 subtitle S_TEXT/UTF8
    10 audio A_AAC
    11 subtitle S_TEXT/UTF8
Frame for 1 ts=0.000000 l=0  len=85470 data=00004e1925b82001ebd3...
Frame for 10 ts=0.009000 l=7  len=145 data=01449ffe0b246a488f09...
Frame for 10 ts=0.009000 l=6  len=145 data=0144d7902c180b04c281...
Frame for 10 ts=0.009000 l=5  len=143 data=013017902c250b1102c1...
Frame for 10 ts=0.009000 l=4  len=150 data=014a17942c240b0502e1...
Frame for 10 ts=0.009000 l=3  len=140 data=014217882c240b05c2c3...
Frame for 10 ts=0.009000 l=2  len=150 data=014817882e16090588a1...
Frame for 10 ts=0.009000 l=1  len=156 data=0142179848250a05c2c1...
Frame for 10 ts=0.009000 l=0  len=140 data=014a17902c220b09c2c1...
Frame for 2 ts=0.012000 l=7  len=470 data=210b950dba9b0a638081...
Frame for 2 ts=0.012000 l=6  len=487 data=210b951db28d61a4c1d9...
Frame for 2 ts=0.012000 l=5  len=520 data=210b9505c69361873088...
Frame for 2 ts=0.012000 l=4  len=514 data=210b950dd28f08a0c118...
Frame for 2 ts=0.012000 l=3  len=459 data=210b94fdb69361a24358...
Frame for 2 ts=0.012000 l=2  len=513 data=210b94edb6991160a040...
Frame for 2 ts=0.012000 l=1  len=465 data=210b94f5b69510621040...
Frame for 2 ts=0.012000 l=0  len=468 data=210b94edb68f61a44354...
Frame for 4 ts=0.042000 l=0 dur=3.375000 len=46 data=41206a6f6262206f6c64...
Frame for 5 ts=0.042000 l=0 dur=3.375000 len=49 data=41756620646572207265...
Frame for 6 ts=0.042000 l=0 dur=3.375000 len=48 data=c38020766f7472652064...
Frame for 7 ts=0.042000 l=0 dur=3.375000 len=2 data=c3a5...
....
'''
