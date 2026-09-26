/* Exercise the actual mGBA SIO and Butterfly driver over a local socket pair.
 * ROMs and save files are not used. Only logging, GBP and IRQ delivery are
 * stubbed; register writes, transfer scheduling and completion are real. */
#include <mgba/internal/gba/sio/butterfly.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/io.h>
#include <mgba/internal/gba/sio/gbp.h>
#include <sys/socket.h>

static struct GBA boards[2];
static struct GBASIOButterfly links[2];
static unsigned irqs[2];
static int32_t cycles[2], nextEvent[2];

int mLogGenerateCategory(const char* name, const char* id) {
    (void) name; (void) id; return 0;
}
void mLog(int category, enum mLogLevel level, const char* format, ...) {
    (void) category; (void) level;
    if (getenv("BUTTERFLY_LINK_DIAGNOSTICS")) {
        va_list args;
        va_start(args, format); vfprintf(stderr, format, args); va_end(args);
        fputc('\n', stderr);
    }
}
void GBASIOPlayerInit(struct GBASIOPlayer* player) { (void) player; }
void GBASIOPlayerReset(struct GBASIOPlayer* player) { (void) player; }
void GBARaiseIRQ(struct GBA* gba, enum GBAIRQ irq, uint32_t late) {
    (void) late;
    assert(irq == GBA_IRQ_SIO);
    ++irqs[gba == &boards[1]];
}

static void setup(void) {
    int sockets[2];
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, sockets) == 0);
    for (unsigned p = 0; p < 2; ++p) {
        struct GBA* gba = &boards[p];
        memset(gba, 0, sizeof(*gba));
        irqs[p] = 0; cycles[p] = 0; nextEvent[p] = INT_MAX;
        mTimingInit(&gba->timing, &cycles[p], &nextEvent[p]);
        gba->sio.p = gba;
        GBASIOInit(&gba->sio);
        GBASIOButterflyCreate(&links[p], p);
        assert(GBASIOButterflyAttachSocket(&links[p], sockets[p]));
        GBASIOSetDriver(&gba->sio, &links[p].d);
        GBASIOWriteRCNT(&gba->sio, 0);
        GBASIOWriteSIOCNT(&gba->sio, 0x6003);
    }
}

static void teardown(void) {
    for (unsigned p = 0; p < 2; ++p) GBASIODeinit(&boards[p].sio);
}

static void checkWords(unsigned p, uint16_t master, uint16_t guest) {
    assert(boards[p].memory.io[GBA_REG(SIOMULTI0)] == master);
    assert(boards[p].memory.io[GBA_REG(SIOMULTI1)] == guest);
    assert(boards[p].memory.io[GBA_REG(SIOMULTI2)] == 0xFFFF);
    assert(boards[p].memory.io[GBA_REG(SIOMULTI3)] == 0xFFFF);
    assert(!GBASIOMultiplayerIsBusy(boards[p].sio.siocnt));
}

static void start(uint16_t master, uint16_t guest) {
    boards[0].memory.io[GBA_REG(SIOMLT_SEND)] = master;
    boards[1].memory.io[GBA_REG(SIOMLT_SEND)] = guest;
    GBASIOWriteSIOCNT(&boards[0].sio, 0x6083);
    /* The guest never writes the start bit, as in the live Emerald trace. */
}

struct WirePacket {
    uint32_t magic;
    uint16_t version, player;
    uint32_t sequence;
    uint16_t word, checksum;
};

static struct WirePacket packet(unsigned player, uint32_t sequence, uint16_t word) {
    struct WirePacket result = { htonl(0x42464C4B), htons(3), htons(player),
        htonl(sequence), htons(word), 0 };
    uint16_t sum = 0;
    const uint8_t* bytes = (const uint8_t*) &result;
    for (unsigned i = 0; i < sizeof(result) - 2; ++i) sum = (uint16_t) (sum * 33u + bytes[i]);
    result.checksum = htons(sum);
    return result;
}

static void inject(unsigned sender, const struct WirePacket* message) {
    assert(write(links[sender].socket, message, sizeof(*message)) == sizeof(*message));
}

static void edgeCases(void) {
    /* Delayed/duplicate/future replies cannot finish a newer request. */
    start(0xABCD, 0xDCBA);
    struct WirePacket stale = packet(1, links[0].pendingSequence - 1, 0x1111);
    struct WirePacket future = packet(1, links[0].pendingSequence + 1, 0x2222);
    inject(1, &stale); inject(1, &future);
    GBASIOButterflyPollFrame(&links[0]);
    assert(irqs[0] == 2 && GBASIOMultiplayerIsBusy(boards[0].sio.siocnt));
    GBASIOButterflyPollFrame(&links[1]);
    GBASIOButterflyPollFrame(&links[0]);
    checkWords(0, 0xABCD, 0xDCBA);
    assert(irqs[0] == 3 && irqs[1] == 3);
    struct WirePacket duplicate = packet(0, links[0].pendingSequence, 0xAAAA);
    inject(0, &duplicate);
    GBASIOButterflyPollFrame(&links[1]);
    assert(irqs[1] == 3);

    /* A zero send word is valid, not a missing-data sentinel. */
    start(0, 0);
    GBASIOButterflyPollFrame(&links[1]);
    GBASIOButterflyPollFrame(&links[0]);
    checkWords(0, 0, 0); checkWords(1, 0, 0);
    assert(irqs[0] == 4 && irqs[1] == 4);

    /* Fragment a valid reply across poll calls. No partial completion. */
    start(0x1111, 0x2222);
    struct WirePacket request;
    assert(read(links[1].socket, &request, sizeof(request)) == sizeof(request));
    struct WirePacket reply = packet(1, ntohl(request.sequence), 0x2222);
    assert(write(links[1].socket, &reply, 5) == 5);
    GBASIOButterflyPollFrame(&links[0]);
    assert(irqs[0] == 4);
    assert(write(links[1].socket, (const char*) &reply + 5, sizeof(reply) - 5) == sizeof(reply) - 5);
    GBASIOButterflyPollFrame(&links[0]);
    assert(irqs[0] == 5);
    checkWords(0, 0x1111, 0x2222);

    /* Late arrival after a timeout cannot resurrect the expired transfer. */
    start(0x1234, 0x4321);
    assert(read(links[1].socket, &request, sizeof(request)) == sizeof(request));
    for (unsigned i = 0; i < 300; ++i) GBASIOButterflyPollFrame(&links[0]);
    checkWords(0, 0x1234, 0xFFFF);
    assert(irqs[0] == 6 && links[0].connected);
    reply = packet(1, ntohl(request.sequence), 0x4321);
    inject(1, &reply);
    GBASIOButterflyPollFrame(&links[0]);
    assert(irqs[0] == 6);

    /* Peer EOF releases a pending transfer once; no SIGPIPE or busy loop. */
    start(0xAAAA, 0xBBBB);
    GBASIOButterflyDestroy(&links[1]);
    GBASIOButterflyPollFrame(&links[0]);
    checkWords(0, 0xAAAA, 0xFFFF);
    assert(irqs[0] == 7 && !links[0].connected);
    GBASIOButterflyPollFrame(&links[0]);
    assert(irqs[0] == 7);
    puts("PASS: stale/duplicate replies, zero words, fragmented reads, timeout and disconnect");
}

int main(int argc, char** argv) {
    setup();
    start(0xB9A0, 0xB9A0);
    if (argc > 1 && strcmp(argv[1], "master-delay") == 0) {
        /* Let the emulated cable duration elapse before delivering a reply. */
        mTimingTick(&boards[0].timing, 100000);
        assert(irqs[0] == 0);
        assert(GBASIOMultiplayerIsBusy(boards[0].sio.siocnt));
        puts("PASS: delayed reply does not complete the master early");
    } else {
        GBASIOButterflyPollFrame(&links[1]);
        assert(irqs[1] == 1);
        checkWords(1, 0xB9A0, 0xB9A0);
        GBASIOButterflyPollFrame(&links[0]);
        assert(irqs[0] == 1);
        checkWords(0, 0xB9A0, 0xB9A0);
        for (unsigned i = 0; i < 4; ++i) {
            GBASIOButterflyPollFrame(&links[1]);
            GBASIOButterflyPollFrame(&links[0]);
        }
        assert(irqs[0] == 1 && irqs[1] == 1);
        start(0x1234, 0x5678);
        GBASIOButterflyPollFrame(&links[1]);
        GBASIOButterflyPollFrame(&links[0]);
        assert(irqs[0] == 2 && irqs[1] == 2);
        checkWords(0, 0x1234, 0x5678);
        checkWords(1, 0x1234, 0x5678);
        puts("PASS: guest needs no start write; words match; one IRQ per transfer; no reply loop");
        edgeCases();
    }
    teardown();
    return 0;
}
