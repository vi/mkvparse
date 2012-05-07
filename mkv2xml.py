#!/usr/bin/env python

# incomplete version, wait for normal one and for "xml2mkv.py"

import mkvparse
import sys
import re

from xml.sax import saxutils

def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for start in range(0, len(s), n):
        yield s[start:start+n]


class MatroskaToText(mkvparse.MatroskaHandler):
    def __init__(self, banlist):
        self.there_was_segment=False
        self.there_was_cluster=False
        self.indent=0

        self.lb_track_id=None
        self.lb_ts=None
        self.lb_data=[]
        self.lb_duration=None
        self.banlist=banlist
        print "<mkv2xml>"

    def __del__(self):
        if self.there_was_cluster:
            print "</Cluster>"
        if self.there_was_segment:
            print "</Segment>"
        print "</mkv2xml>"

    def tracks_available(self):
        pass;

    def segment_info_available(self):
        pass;

    def frame(self, track_id, timestamp, data, more_laced_frames, duration):
        self.lb_duration=duration
        self.lb_track_id=track_id
        self.lb_ts=timestamp
        self.lb_data.append(data)

    def printtree(self, list_, ident):
        ident_ = "  "*ident;
        for (name_, (type_, data_)) in list_:
            if name_ in self.banlist:
                continue;
            if type_ == mkvparse.EbmlElementType.BINARY:
                if name_ == "SimpleBlock" or name_ == "Block":
                    newdata ="\n  "+ident_+"<track>%s</track>"%self.lb_track_id;
                    newdata+="\n  "+ident_+"<timecode>%s</timecode>"%self.lb_ts;
                    if(self.lb_duration):
                        newdata+="\n  "+ident_+"<duration>%s</duration>"%self.lb_duration;
                    for data_2 in self.lb_data:
                        newdata+="\n  "+ident_+"<data>";
                        for chunk in chunks(data_2.encode("hex"), 64):
                            newdata+="\n    "+ident_;
                            newdata+=chunk;
                        newdata+="\n  "+ident_+"</data>";
                    newdata+="\n"+ident_;
                    data_=newdata

                    self.lb_duration=None
                    self.lb_track_id=None
                    self.lb_ts=None
                    self.lb_data=[]

                elif data_:
                    data_ = data_.encode("hex")
                    if len(data_) > 40:
                        newdata=""
                        for chunk in chunks(data_, 64):
                            newdata+="\n  "+ident_;
                            newdata+=chunk;
                        newdata+="\n"+ident_;
                        data_=newdata

            if type_ == mkvparse.EbmlElementType.MASTER:
                print("%s<%s>"%(ident_,name_))
                self.printtree(data_, ident+1);
                print("%s</%s>"%(ident_, name_))
            elif type_ == mkvparse.EbmlElementType.JUST_GO_ON:
                if name_ == "Segment":
                    if self.there_was_segment:
                        print("</Segment>")
                    print("<Segment>")
                    self.there_was_segment=True
                elif name_ == "Cluster":
                    if self.there_was_cluster:
                        print("</Cluster>")
                    print("<Cluster>")
                    self.there_was_cluster=True
                    self.indent=1
                else:
                    sys.stderr.write("Unknown JUST_GO_ON element %s\n" % name_)
            else:
                if type_ == mkvparse.EbmlElementType.TEXTA or type_ == mkvparse.EbmlElementType.TEXTU:
                    data_ = saxutils.escape(str(data_))
                print("%s<%s>%s</%s>"%(ident_, name_, data_, name_));
            
        

    def ebml_top_element(self, id_, name_, type_, data_):
        self.printtree([(name_, (type_, data_))], self.indent)



# Reads mkv input from stdin, parse it and print details to stdout
banlist=["SeekHead", "CRC-32", "Void", "Cues", "PrevSize", "Position"]
if len(sys.argv)>1 and sys.argv[1]=="-v":
    banlist=[]
mkvparse.mkvparse(sys.stdin, MatroskaToText(frozenset(banlist)))


