# Licence==MIT; Vitaly "_Vi" Shukela 2012

# Simple easy-to-use hacky matroska parser

# Supports SimpleBlock and BlockGroup, lacing, TimecodeScale.
# Does not support seeking, cues, chapters and other features.
# No proper EOF handling unfortunately

# See "mkvuser.py" for the example

import traceback


def get_major_bit_number(n):
    '''
        Takes uint8, returns number of the most significant bit plus the number with that bit cleared.
        Examples:
        0b10010101 -> (0, 0b00010101)
        0b00010101 -> (3, 0b00000101)
        0b01111111 -> (1, 0b00111111)
    '''
    if not n:
        raise Exception("Bad number")
    i=0x80;
    r=0
    while not n&i:
        r+=1
        i>>=1
    return (r,n&~i);

def read_matroska_number(f, unmodified=False, signed=False):
    '''
        Read ebml number. Unmodified means don't clear the length bit (as in Element IDs)
        Returns the number plus it's length

        See examples in "parse_matroska_number" function
    '''
    if unmodified and signed:
        raise Exception("Contradictary arguments")
    first_byte=f.read(1)
    if(first_byte==""):
        raise StopIteration
    r = ord(first_byte)
    (n,r2) = get_major_bit_number(r)
    if not unmodified:
        r=r2
    # from now "signed" means "negative"
    i=n
    while i:
        r = r * 0x100 + ord(f.read(1))
        i-=1
    if signed:
        r-=(2**(7*n+7)-1)
    else:
        if r==2**(7*n+7)-1:
            return (-1, n+1)
    return (r,n+1)

def parse_matroska_number(data, pos, unmodified=False, signed=False):
    '''
        Parse ebml number from buffer[pos:]. Just like read_matroska_number.
        Unmodified means don't clear the length bit (as in Element IDs)
        Returns the number plus the new position in input buffer

        Examples:
        "\x81" -> (1, pos+1)
        "\x40\x01" -> (1, pos+2)
        "\x20\x00\x01" -> (1, pos+3)
        "\x3F\xFF\xFF" -> (0x1FFFFF, pos+3)
        "\x20\x00\x01" unmodified -> (0x200001, pos+3)
        "\xBF" signed -> (0, pos+1)
        "\xBE" signed -> (-1, pos+1)
        "\xC0" signed -> (1, pos+1)
        "\x5F\xEF" signed -> (-16, pos+2)
    '''
    if unmodified and signed:
        raise Exception("Contradictary arguments")
    r = ord(data[pos])
    pos+=1
    (n,r2) = get_major_bit_number(r)
    if not unmodified:
        r=r2
    # from now "signed" means "negative"
    i=n
    while i:
        r = r * 0x100 + ord(data[pos])
        pos+=1
        i-=1
    if signed:
        r-=(2**(7*n+6)-1)
    else:
        if r==2**(7*n+7)-1:
            return (-1, pos)
    return (r,pos)

def parse_xiph_number(data, pos):
    '''
        Parse the Xiph lacing number from data[pos:]
        Returns the number plus the new position

        Examples:
        "\x01" -> (1,    pos+1)
        "\x55" -> (0x55, pos+1)
        "\xFF\x04" -> (0x103,  pos+2)
        "\xFF\xFF\x04" -> (0x202,  pos+3)
        "\xFF\xFF\x00" -> (0x1FE,  pos+3)
    '''
    v = ord(data[pos])
    pos+=1

    r=0
    while v==255:
        r+=v
        v = ord(data[pos])
        pos+=1

    r+=v
    return (r, pos)


def parse_fixedlength_number(data, pos, length, signed=False):
    '''
        Read the big-endian number from data[pos:pos+length]
        Returns the number plus the new position

        Examples:
        "\x01" -> (0x1,    pos+1)
        "\x55" -> (0x55, pos+1)
        "\x55" signed -> (0x55, pos+1)
        "\xFF\x04" -> (0xFF04,  pos+2)
        "\xFF\x04" signed -> (-0x00FC,  pos+2)
    '''
    r=0
    for i in xrange(length):
        r=r*0x100+ord(data[pos+i])
    if signed:
        if ord(data[pos]) & 0x80:
            r-=2**(8*length)
    return (r, pos+length)

def read_fixedlength_number(f, length, signed=False):
    """ Read length bytes and parse (parse_fixedlength_number) it.
    Returns only the number"""
    buf = f.read(length)
    (r, pos) = parse_fixedlength_number(buf, 0, length, signed)
    return r
    
def read_ebml_element_header(f):
    '''
        Read Element ID and size
        Returns id, element size and this header size
    '''
    (id_, n) = read_matroska_number(f, unmodified=True)
    (size, n2) = read_matroska_number(f)
    return (id_, size, n+n2)

class EbmlElementType:
    VOID=0
    MASTER=1 # read all subelements and return tree. Don't use this too large things like Segment
    UNSIGNED=2
    SIGNED=3
    TEXTA=4
    TEXTU=5
    BINARY=6
    FLOAT=7

    JUST_GO_ON=10 # For "Segment". 
    # Actually MASTER, but don't build the tree for all subelements, 
    # interpreting all child elements as if they were top-level elements
    

EET=EbmlElementType

# Warning: now all elements are listed here. Add elements you need from http://matroska.org/technical/specs/index.html .
element_types_names = {
    0x1A45DFA3:  (EET.MASTER, "EBML"),
    0x4286:  (EET.UNSIGNED, "EBMLVersion"),
    0x42F7:  (EET.UNSIGNED, "EBMLReadVersion"),
    0x42F2:  (EET.UNSIGNED, "EBMLMaxIDLength"),
    0x42F3:  (EET.UNSIGNED, "EBMLMaxSizeLength"),
    0x4282:  (EET.TEXTA, "DocType"),
    0x4287:  (EET.UNSIGNED, "DocTypeVersion"),
    0x4285:  (EET.UNSIGNED, "DocTypeReadVersion"),
    0x18538067: (EET.JUST_GO_ON, "Segment"),
    0x1549A966: (EET.MASTER, "SegmentInfo"),
    0x73A4: (EET.BINARY, "SegmentUID"),
    0x7BA9: (EET.TEXTU, "Title"),
    0x4D80: (EET.TEXTA, "MuxingApp"),
    0x5741: (EET.TEXTA, "WritingApp"),
    0x2A7DB1: (EET.UNSIGNED, "TimecodeScale"),
    0x1654AE6B: (EET.MASTER, "Tracks"),
    0xAE: (EET.MASTER, "TrackEntry"),
    0xD7: (EET.UNSIGNED, "TrackNumber"),
    0x73C5: (EET.UNSIGNED, "TrackUID"),
    0x83: (EET.UNSIGNED, "TrackType"),
    0xB9: (EET.UNSIGNED, "FlagEnabled"),
    0x88: (EET.UNSIGNED, "FlagDefault"),
    0x55AA: (EET.UNSIGNED, "FlagForced"),
    0x9C: (EET.UNSIGNED, "FlagLacing"),
    0x23E383: (EET.UNSIGNED, "DefaultDuration"),
    0x6DE7: (EET.UNSIGNED, "MinCache"),
    0x6DF8: (EET.UNSIGNED, "MaxCache"),
    0x23314F: (EET.FLOAT, "TrackTimecodeScale"),
    0x537F: (EET.SIGNED, "TrackOffset"),
    0x536E: (EET.TEXTU, "Name"),
    0x22B59C: (EET.TEXTU, "Language"),
    0x86: (EET.TEXTA, "CodecID"),
    0x63A2: (EET.TEXTA, "CodecPrivate"),
    0x258688: (EET.TEXTU, "CodecName"),

    0xE0: (EET.MASTER, "Video"),
    0xB0: (EET.UNSIGNED, "PixelWidth"),
    0xBA: (EET.UNSIGNED, "PixelHeight"),

    0x1F43B675: (EET.JUST_GO_ON, "Cluster"),
    0xE7: (EET.UNSIGNED, "TimeCode"),
    0xA7: (EET.UNSIGNED, "Position"),
    0xA3: (EET.BINARY, "SimpleBlock"),
    0xA0: (EET.MASTER, "BlockGroup"),
    0xA1: (EET.BINARY, "Block"),
    0x9B: (EET.UNSIGNED, "BlockDuration"),
    0xAB: (EET.UNSIGNED, "PreviousClusterPosition"),
    
    0xEC: (EET.VOID, "Void"),
    0xBF: (EET.BINARY, "CRC-32"),

    0x114D9B74: (EET.MASTER, "SeekHead"),
    0x4DBB: (EET.MASTER, "Seek"),
    0x53AB: (EET.BINARY, "SeekID"),
    0x53AC: (EET.UNSIGNED, "SeekPosition"),
    0x1C53BB6B: (EET.MASTER, "Cues"),
    0x1941A469: (EET.MASTER, "Attachments"),
    0x1043A770: (EET.MASTER, "Chapters"),
    0x1254C367: (EET.MASTER, "Tags"),
    
    0x7373: (EET.MASTER, "Tag"),
    0x63C0: (EET.MASTER, "Targets"),
    0x67C8: (EET.MASTER, "SimpleTag"),
    
    0x63CA: (EET.TEXTU, "TargetType"),
    0x45A3: (EET.TEXTU, "TagName"),
    0x4587: (EET.TEXTU, "TagString"),
    0x4585: (EET.BINARY, "TagBinary"),


    
}



def read_ebml_element_tree(f, total_size):
    '''
        Build tree of elements, reading f until total_size reached
        Don't use for the whole segment, it's not Haskell

        Returns list of pairs (element_name, element_value).
        element_value can also be list of pairs
    '''
    childs=[]
    while(total_size>0):
        (id_, size, hsize) = read_ebml_element_header(f)
        if size == -1:
            print("Element %x without size? Damaged data? Skipping %d bytes" % (id_, size, total_size))
            f.read(total_size);
            break;
        if size>total_size:
            print("Element %x with size %d? Damaged data? Skipping %d bytes" % (id_, size, total_size))
            f.read(total_size);
            break
        type = None
        name = "%x"%id_
        if id_ in element_types_names:
            (type, name) = element_types_names[id_]
        data=None
        if type==EET.UNSIGNED:
            data=read_fixedlength_number(f, size, False)
        elif type==EET.SIGNED:
            data=read_fixedlength_number(f, size, True)
        elif type==EET.TEXTA:
            data=f.read(size)
            data = filter(lambda x: x!="\x00", data) # filter out \0, for gstreamer
        elif type==EET.TEXTU:
            data=f.read(size)
        elif type==EET.MASTER:
            data=read_ebml_element_tree(f, size)
        else:
            data=f.read(size)
        total_size-=(size+hsize)
        childs.append((name, data)) 
    return childs
                

class MatroskaHandler:
    """ User for mkvparse should override these methods """
    def tracks_available(self):
        pass
    def segment_info_available(self):
        pass
    def frame(self, track_id, timestamp, data, more_laced_frames, duration):
        pass

def handle_block(buffer, handler, cluster_timecode, timecode_scale=1000000, duration=None):
    '''
        Decode a block, handling all lacings, send it to handler with appropriate timestamp, track number
    '''
    pos=0
    (tracknum, pos) = parse_matroska_number(buffer, pos, signed=False)
    (tcode, pos) = parse_fixedlength_number(buffer, pos, 2, signed=True)
    flags = ord(buffer[pos]); pos+=1
    laceflags=flags&0x06

    block_timecode = (cluster_timecode + tcode)*(timecode_scale*0.000000001)

    if laceflags == 0x00: # no lacing
        buf = buffer[pos:]
        handler.frame(tracknum, block_timecode, buf, 0, duration)
        return
    
    numframes = ord(buffer[pos]); pos+=1
    numframes+=1

    lengths=[]

    if laceflags == 0x02: # Xiph lacing
        accumlength=0
        for i in xrange(numframes-1):
            (l, pos) = parse_xiph_number(buffer, pos)
            lengths.append(l)
            accumlength+=l
        lengths.append(len(buffer)-pos-accumlength)
    elif laceflags == 0x06: # EBML lacing
        accumlength=0
        if numframes:
            (flength, pos) = parse_matroska_number(buffer, pos, signed=False)
            lengths.append(flength)
            accumlength+=flength
        for i in xrange(numframes-2):
            (l, pos) = parse_matroska_number(buffer, pos, signed=True)
            flength+=l
            lengths.append(flength)
            accumlength+=flength
        lengths.append(len(buffer)-pos-accumlength)
    elif laceflags==0x04: # Fixed size lacing
        fl=(len(buffer)-pos)/numframes
        for i in xrange(numframes):
            lengths.append(fl)

    more_laced_frames=numframes-1
    for i in lengths:
        buf = buffer[pos:pos+i]
        pos+=i
        handler.frame(tracknum, block_timecode, buf, more_laced_frames, None)
        more_laced_frames-=1


def resync(f):
    print("Resyncing")
    while True:
        b = f.read(1);
        if b == "": return (None, None);
        if b == "\x1F":
            b2 = f.read(3);
            if b2 == "\x43\xB6\x75":
                (seglen, x) = read_matroska_number(f)
                return (0x1F43B675, seglen) # cluster
        if b == "\x18":
            b2 = f.read(3)
            if b2 == "\x53\x80\x67":
                (seglen, x) = read_matroska_number(f)
                return (0x18538067, seglen) # segment
        if b == "\x16":
            b2 = f.read(3)
            if b2 == "\x54\xAE\x6B":
                (seglen ,x )= read_matroska_number(f)
                return (0x1654AE6B, seglen) # tracks
                
                
    

def mkvparse(f, handler):
    '''
        Read mkv file f and call handler methods when track or segment information is ready or when frame is read.
        Handles lacing, timecodes (except of per-track scaling)
    '''
    timecode_scale = 1000000
    current_cluster_timecode = 0
    resync_element_id = None
    resync_element_size = None
    while f:
        (id_, size, hsize) = (None, None, None)
        tree = None
        (type, name) = (None, None)
        try:
            if not resync_element_id:
                try:
                    (id_, size, hsize) = read_ebml_element_header(f)
                except StopIteration:
                    break;
                if not (id_ in element_types_names): 
                    print("Unknown element with id %x and size %d"%(id_, size))
                    (resync_element_id, resync_element_size) = resync(f)
                    if resync_element_id:
                        continue;
                    else:
                        break;
            else: 
                id_ = resync_element_id
                size=resync_element_size
                resync_element_id = None
                resync_element_size = None

            (type, name) = element_types_names[id_]

            if type==EET.MASTER:
                tree = read_ebml_element_tree(f, size)
            elif type==EET.JUST_GO_ON:
                pass
        except Exception:
            traceback.print_exc()
            (resync_element_id, resync_element_size) = resync(f)
            if resync_element_id:
                continue;
            else:
                break;
            

        if name=="EBML":
            d = dict(tree)
            if 'EBMLReadVersion' in d:
                if d['EBMLReadVersion']>1: print("Warning: EBMLReadVersion too big")
            if 'DocTypeReadVersion' in d:
                if d['DocTypeReadVersion']>2: print("Warning: DocTypeReadVersion too big")
            dt = d['DocType']
            if dt != "matroska" and dt != "webm": print("Warning: EBML DocType is not \"matroska\" or \"webm\"")
        elif name=="SegmentInfo":
            handler.segment_info = tree
            handler.segment_info_available()
            
            d = dict(tree)
            if "TimecodeScale" in d:
                timecode_scale = d["TimecodeScale"]
        elif name=="Tracks":
            handler.tracks={}
            for (ten, track) in tree:
                if ten != "TrackEntry": continue
                d = dict(track)
                n = d['TrackNumber']
                handler.tracks[n]=d
                tt = d['TrackType']
                if   tt==0x01: d['type']='video'
                elif tt==0x02: d['type']='audio'
                elif tt==0x03: d['type']='complex'
                elif tt==0x10: d['type']='logo'
                elif tt==0x11: d['type']='subtitle'
                elif tt==0x12: d['type']='button'
                elif tt==0x20: d['type']='control'
                if 'TrackTimecodeScale' in d:
                    print("Warning: TrackTimecodeScale is not supported")
            handler.tracks_available()
        # cluster contents:
        elif name=="TimeCode":
            data=read_fixedlength_number(f, size, False)
            current_cluster_timecode = data;
        elif name=="SimpleBlock":
            data=f.read(size)
            handle_block(data, handler, current_cluster_timecode, timecode_scale)
        elif name=="BlockGroup":
            d2 = dict(tree)
            duration=None
            if 'BlockDuration' in d2:
                duration = d2['BlockDuration']
                duration = duration*0.000000001*timecode_scale
            if 'Block' in d2:
                handle_block(d2['Block'], handler, current_cluster_timecode, timecode_scale, duration)
        else:
            if size!=-1 and type!=EET.JUST_GO_ON and type!=EET.MASTER:
                f.read(size)


if __name__ == '__main__':
    print("Run mkvuser.py for the example")
