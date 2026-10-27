// SPDX-License-Identifier: GPL-2.0-only
// Compile against the actual pinned/patched core; no ROMs needed.
#include "netplay_serial.h"
#include "gambatte_log.h"
#include <assert.h>
#include <time.h>
#include <string.h>
#include <stdio.h>
#include <vector>
void gambatte_log(enum retro_log_level, const char *, ...) {}
struct Packet { unsigned char type, data, clock; uint32_t id; };
static NetplaySerial *serial;
static std::vector<Packet> sent;
static int polling, polls;
static uint32_t activeId, oldId;
static void receive(unsigned char type,uint32_t id,unsigned char data=0,bool fast=false) {
    unsigned char p[8]={type,data,(unsigned char)(fast?1:0),0,(unsigned char)(id>>24),
                       (unsigned char)(id>>16),(unsigned char)(id>>8),(unsigned char)id};
    serial->netplayReceive(p,8,0);
}
static void send_packet(int flags,const void *data,size_t len,uint16_t peer) {
    assert(len==8);assert(flags & RETRO_NETPACKET_RELIABLE);assert(peer==RETRO_NETPACKET_BROADCAST);
    const unsigned char *p=static_cast<const unsigned char *>(data);
    Packet packet={p[0],p[1],p[2],(uint32_t(p[4])<<24)|(uint32_t(p[5])<<16)|(uint32_t(p[6])<<8)|p[7]};
    sent.push_back(packet);if(packet.type==1)activeId=packet.id;
}
static void poll_packet() {
    ++polls;
    if(polling==1)receive(2,activeId,0x42);
    if(polling==2)serial->netplayStop();
    if(polling==3)receive(1,77,0x55);
    if(polling==4){if(polls==1)receive(2,oldId,0x99);else receive(2,activeId,0x42);}
}
static double seconds(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
int main(){
    NetplaySerial object;serial=&object;
    assert(object.send(0x12,false)==0xFF);assert(sent.empty());
    object.netplayStart(0,send_packet,poll_packet);
    assert(object.send(0x12,false)==0xFF);assert(sent.empty());
    assert(object.netplayConnect(1));assert(!object.netplayConnect(2));
    unsigned char invalid[3]={1,2,3};unsigned char in=0;bool fast=false;
    object.netplayReceive(invalid,3,1);assert(!object.check(1,in,fast));
    receive(1,3,0x23,true);assert(object.check(0x37,in,fast));assert(in==0x23 && fast);
    assert(sent.back().type==2 && sent.back().id==3 && sent.back().data==0x37);
    receive(1,4,0x11);receive(3,4);assert(!object.check(0,in,fast));
    object.netplayDisconnect(1);assert(object.send(1,false)==0xFF);
    object.netplayStart(1,send_packet,poll_packet);polling=1;
    assert(object.send(0x14,true)==0x42);
    polling=3;assert(object.send(0x21,false)==0x55); // crossed internal clocks
    bool replied=false;
    for(unsigned i=0;i<sent.size();++i)if(sent[i].type==2 && sent[i].id==77 && sent[i].data==0x21)replied=true;
    assert(replied);
    polling=2;assert(object.send(1,false)==0xFF);
    object.netplayStart(1,send_packet,poll_packet);polling=0;
    double start=seconds();assert(object.send(1,false)==0xFF);
    double elapsed=seconds()-start;assert(elapsed>=1.9 && elapsed<3.5);
    oldId=activeId;assert(sent.back().type==3 && sent.back().id==oldId);
    // Timeout keeps callbacks/peer alive; a late reply cannot satisfy the next byte.
    polling=4;polls=0;assert(object.send(1,false)==0x42);assert(polls>=2);
    receive(1,99,0x66);assert(object.send(0x77,false)==0x66); // queued request
    object.netplayStart(0,send_packet,poll_packet);assert(object.netplayConnect(1));
    receive(1,123,0x66);object.netplayDisconnect(1);
    assert(object.netplayConnect(1));assert(!object.check(1,in,fast));
    for(unsigned i=1;i<=65;++i)receive(1,i,0x11);
    for(unsigned i=0;i<64;++i)assert(object.check(1,in,fast));
    assert(!object.check(1,in,fast));
    puts("Serial initialization, request/reply, crossed clocks, queue bounds, cancellation, recoverable timeout, stale replies and disconnect checks passed.");
}
