Simple easy-to-use hacky matroska parser

Define your handler class:

    class MyMatroskaHandler(mkvparse.MatroskaHandler):
        def tracks_available(self):
            ...

        def segment_info_available(self):
            ...

        def frame(self, track_id, timestamp, data, more_laced_blocks, duration):
            ...

and `mkvparse.mkvparse(file, MyMatroskaHandler())`


Supports lacing and setting global timecode scale, subtitles (BlockGroup). Does not support cues, tags, chapters, seeking and so on.

Also contains example of generation of Matroska files from python

Licence=MIT
