#define _GNU_SOURCE // memmem
#include <stdio.h>
#include <string.h>
#include <assert.h>

// Split multi-segment Matroska files to separate mkv files.
// Works by looking for 18538067 occurences
// (validating them assuming that some other non-Cluster 1-level should follow in nearest 64 kb)
// Reads standard input and writes 1.mkv, 2.mkv and so on
// Implemented by Vitaly "_Vi" Shukela in 2013; License=MIT


int cursor = 0;  // number of bytes in the buffer
unsigned char buf[655360];

int main(int argc, char* argv[]) {
    fprintf(stderr, "Reading mkv file from stdin and extracting segments to current directory\n");

    int n = 0;
    FILE* f = NULL;

    int ret;

    for(;;) {
        { 
            int ret;
            ret = fread(buf+cursor, 1, sizeof buf - cursor, stdin);
            cursor+=ret;
        }

        if(cursor == 0 || cursor==4) break;
        
        unsigned char* q = memmem(buf, cursor, "\x18\x53\x80\x67", 4);
        //fprintf(stderr, "q=%d cursor=%d\n", q-buf, cursor);


        if(q) {
            if(f) {
                fwrite(buf, 1, q-buf, f);
            }
            memmove(buf, q, cursor-(q-buf));
            cursor-=q-buf;

            // validate this 18538067 occurence: if some other level-1 element except of a cluster is nearby, then consider this as true segment start
            assert(!memcmp(buf, "\x18\x53\x80\x67", 4));

            if(cursor<65536) continue;

            if(!memmem(buf, 65536, "\x15\x49\xA9\x66", 4) &&  // SegmentInfo
               !memmem(buf, 65536, "\x16\x54\xAE\x6B", 4) &&  // Tracks
               !memmem(buf, 65536, "\x11\x4D\x9B\x74", 4) &&  // SeekHead
               !memmem(buf, 65536, "\x1C\x53\xBB\x6B", 4) &&  // Cues
               !memmem(buf, 65536, "\x19\x41\xA4\x69", 4) &&  // Attachments
               !memmem(buf, 65536, "\x10\x43\xA7\x70", 4) &&  // Chapters
               !memmem(buf, 65536, "\x12\x54\xC3\x67", 4) &&  // Tags
               1) {
                // None found
                fprintf(stderr, "Stay 18 53 80 67 occurence...\n");
                if(f) {
                    fwrite(buf, 1, 4, f);
                }
                memmove(buf, buf+4, cursor-4);
                cursor-=4;
                continue;
            }
            

            if(f) {
                fclose(f);
            }

            ++n;
            fprintf(stderr, "%d.mkv\n", n);
            char fn[4096];
            snprintf(fn, sizeof fn, "%d.mkv", n);
            f = fopen(fn, "wb");
            
            if(f) {
                fwrite("\x1a\x45\xdf\xa3\x8b\x42\x82\x88matroska",1,16,f);
                fwrite(buf, 1, 4, f);
                memmove(buf, buf+4, cursor-4);
                cursor-=4;
            }
            continue;
        }
        
        if(f) {
            int to_be_written = cursor-4;
            if(to_be_written>0) {
                ret = fwrite(buf, 1, to_be_written, f);
                assert(ret==to_be_written);
                memmove(buf, buf+to_be_written, cursor - to_be_written);
                cursor = cursor - to_be_written;
            }
        } else {
            if(cursor>4) {
                memmove(buf, buf+cursor-4, 4);
                cursor=4;
            }
        }
    }

    if(f) {
        if(cursor>0) {
            fwrite(buf, 1, cursor, f);
        }
        fclose(f);
    }

    return 0;
}
