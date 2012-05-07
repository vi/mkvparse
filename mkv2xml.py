#!/usr/bin/env python

# incomplete version, wait for normal one and for "xml2mkv.py"

import mkvparse
import sys
import re

def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for start in range(0, len(s), n):
        yield s[start:start+n]


class MatroskaToText(mkvparse.MatroskaHandler):
    def tracks_available(self):
        pass;

    def segment_info_available(self):
        pass;

    def frame(self, track_id, timestamp, data, more_laced_frames, duration):
        durstr=""
        if duration:
            durstr="dur=%.6f"%duration
        print("Frame for %d ts=%.06f l=%d %s len=%d data=%s..." %
                (track_id, timestamp, more_laced_frames, durstr, len(data), data[0:10].encode("hex")))



    def printtree(self, list_, ident):
        ident_ = "  "*ident;
        for (name_, (type_, data_)) in list_:
            if type_ == mkvparse.EbmlElementType.BINARY:
                if data_:
                    data_ = data_.encode("hex")
                    if len(data_) > 40:
                        newdata=""
                        for chunk in chunks(data_, 60):
                            newdata+="\n  "+ident_;
                            newdata+=chunk;
                        newdata+="\n"+ident_;
                        data_=newdata

            if type_ == mkvparse.EbmlElementType.MASTER:
                print("%s<%s>"%(ident_,name_))
                self.printtree(data_, ident+1);
                print("%s</%s>"%(ident_, name_))
            else:
                print("%s<%s>%s</%s>"%(ident_, name_, data_, name_));
            
        

    def ebml_top_element(self, id_, name_, type_, data_):
        self.printtree([(name_, (type_, data_))], 0)



# Reads mkv input from stdin, parse it and print details to stdout
mkvparse.mkvparse(sys.stdin, MatroskaToText())


