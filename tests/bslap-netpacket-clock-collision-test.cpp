// SPDX-License-Identifier: GPL-2.0-only
// Two real serial instances, with delivery held until both clocks start.
#include "netplay_serial.h"
#include "gambatte_log.h"
#include <array>
#include <deque>
#include <mutex>
#include <thread>
#include <cassert>
#include <cstring>
#include <cstdio>
void gambatte_log(enum retro_log_level,const char*,...) {}
struct Endpoint { NetplaySerial serial; std::deque<std::array<unsigned char,8> > inbox; };
static Endpoint *ends;
static std::mutex guard;
static unsigned requests;
static void send_from(unsigned from,int flags,const void *data,size_t size,uint16_t peer) {
    assert(size==8);
    std::array<unsigned char,8> packet;memcpy(packet.data(),data,8);
    std::lock_guard<std::mutex> lock(guard);
    if(packet[0]==1)++requests;
    ends[1-from].inbox.push_back(packet);
}
static void send0(int f,const void*d,size_t n,uint16_t p){send_from(0,f,d,n,p);}
static void send1(int f,const void*d,size_t n,uint16_t p){send_from(1,f,d,n,p);}
static void poll_from(unsigned from) {
    for(;;) {
        std::array<unsigned char,8> packet;
        {
            std::lock_guard<std::mutex> lock(guard);
            if(requests<2 || ends[from].inbox.empty())return;
            packet=ends[from].inbox.front();ends[from].inbox.pop_front();
        }
        ends[from].serial.netplayReceive(packet.data(),8,1-from);
    }
}
static void poll0(){poll_from(0);}
static void poll1(){poll_from(1);}
int main(){
    for(unsigned iteration=0;iteration<40;++iteration){
        Endpoint endpoints[2];ends=endpoints;requests=0;
        unsigned host=iteration%2;
        for(unsigned i=0;i<2;++i){
            ends[i].serial.netplayStart(i==host?0:1,i==0?send0:send1,i==0?poll0:poll1);
            if(i==host)assert(ends[i].serial.netplayConnect(1));
        }
        const unsigned char outgoing[2]={0x41,0x93}, prepared[2]={0xA7,0xE5};
        bool snapshots=iteration%4<2;
        if(snapshots)for(unsigned i=0;i<2;++i)ends[i].serial.externalReady(prepared[i]);
        unsigned char result[2]={0,0};
        std::thread a([&]{result[0]=ends[0].serial.send(outgoing[0],false);});
        std::thread b([&]{result[1]=ends[1].serial.send(outgoing[1],false);});
        a.join();b.join();
        if(snapshots){
            assert(result[host]==prepared[1-host]);
            assert(result[1-host]==outgoing[host]);
        }else{
            assert(result[0]==outgoing[1]);assert(result[1]==outgoing[0]);
        }
        poll0();poll1(); // cancellation drains any queued crossed request
        unsigned char in;bool fast;
        assert(!ends[0].serial.check(0,in,fast));assert(!ends[1].serial.check(0,in,fast));
    }
    puts("40 simultaneous-clock cases passed: both host orientations, staged external bytes, and ordinary byte exchanges.");
}
