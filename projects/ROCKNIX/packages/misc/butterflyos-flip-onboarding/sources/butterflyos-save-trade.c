/*
 * SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright (C) 2026 Keaten Perkins
 *
 * Safe local prototype for ButterflyOS save trading.  It deliberately works
 * on copies supplied as output paths; the user's original save files are
 * never modified by this helper.  The UI/network layer will add discovery,
 * confirmation, and two-phase commit around this primitive.
 */

#include <pksav/gen1.h>
#include <pksav/gen2.h>
#include <pksav/gen3.h>

#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "butterflyos-gen2-gen3-items.h"

static void usage(FILE* stream) {
    fprintf(stream,
        "Usage:\n"
        "  butterflyos-save-trade inspect --save FILE\n"
        "  butterflyos-save-trade gift-gen1 --destination FILE --destination-box N\n"
        "      --destination-slot N --record FILE --national-species N\n"
        "      --nickname NAME --rom-family red-blue|yellow --output-destination FILE\n"
        "  butterflyos-save-trade swap-gen1 --left FILE --left-box N --left-slot N\n"
        "      --right FILE --right-box N --right-slot N\n"
        "      --output-left FILE --output-right FILE\n"
        "  butterflyos-save-trade copy-gen1 --source FILE --source-box N\n"
        "      --source-slot N --destination FILE --destination-box N\n"
        "      --destination-slot N --output-destination FILE\n"
        "  butterflyos-save-trade swap-gen2 --left FILE --left-box N --left-slot N\n"
        "      --right FILE --right-box N --right-slot N\n"
        "      --output-left FILE --output-right FILE\n"
        "  butterflyos-save-trade copy-gen2 --source FILE --source-box N\n"
        "      --source-slot N --destination FILE --destination-box N\n"
        "      --destination-slot N --output-destination FILE\n"
        "  butterflyos-save-trade transfer-gen1-to-gen2 --source FILE --source-box N\n"
        "      --source-slot N --national-species N --destination FILE --destination-box N\n"
        "      --destination-slot N --output-destination FILE\n"
        "  butterflyos-save-trade copy-gen2-to-gen3 --source FILE --source-box N\n"
        "      --source-slot N --national-species N --destination FILE --destination-box N\n"
        "      --destination-slot N --output-destination FILE\n"
        "  butterflyos-save-trade swap-gen3 --left FILE --left-box N --left-slot N\n"
        "      --right FILE --right-box N --right-slot N\n"
        "      --output-left FILE --output-right FILE\n"
        "  butterflyos-save-trade copy-gen3 --source FILE --source-box N\n"
        "      --source-slot N --destination FILE --destination-box N\n"
        "      --destination-slot N --output-destination FILE\n\n"
        "  butterflyos-save-trade evolve-genN --source FILE --box N --slot N\n"
        "      --evolved-species N [--nickname NAME] --output FILE\n\n"
        "Swap and copy commands only write the explicit output files.\n"
        "Cross-generation commands only write the explicit destination output.\n"
        "Gen II to Gen III is a one-way copy; the original Gen II save is unchanged.\n");
}

static const char* save_type_name(enum pksav_gen3_save_type type) {
    switch (type) {
    case PKSAV_GEN3_SAVE_TYPE_RS: return "Ruby/Sapphire";
    case PKSAV_GEN3_SAVE_TYPE_EMERALD: return "Emerald";
    case PKSAV_GEN3_SAVE_TYPE_FRLG: return "FireRed/LeafGreen";
    default: return "unknown";
    }
}

static uint16_t species_of(const struct pksav_gen3_pc_pokemon* pokemon) {
    return pksav_littleendian16(pokemon->blocks.growth.species);
}

static bool pokemon_present(const struct pksav_gen3_pc_pokemon* pokemon) {
    return species_of(pokemon) != 0;
}

static bool pokemon_is_shiny(const struct pksav_gen3_pc_pokemon* pokemon) {
    uint32_t personality = pksav_littleendian32(pokemon->personality);
    uint32_t trainer_id = pksav_littleendian32(pokemon->ot_id.id);
    uint32_t value = (personality >> 16) ^ (personality & 0xFFFFu) ^
                     (trainer_id >> 16) ^ (trainer_id & 0xFFFFu);
    return value < 8u;
}

static const char* nature_name(uint32_t personality) {
    static const char* const names[] = {
        "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
        "Bold", "Docile", "Relaxed", "Impish", "Lax",
        "Timid", "Hasty", "Serious", "Jolly", "Naive",
        "Modest", "Mild", "Quiet", "Bashful", "Rash",
        "Calm", "Gentle", "Sassy", "Careful", "Quirky"
    };
    return names[personality % (sizeof(names) / sizeof(names[0]))];
}

static void print_gen1_details(const struct pksav_gen1_pc_pokemon* pokemon) {
    printf("\tmoves=%u,%u,%u,%u\theld=0\tlevel=%u\n",
           (unsigned) pokemon->moves[0], (unsigned) pokemon->moves[1],
           (unsigned) pokemon->moves[2], (unsigned) pokemon->moves[3],
           (unsigned) pokemon->level);
}

static bool gen2_pokemon_is_shiny(const struct pksav_gen2_pc_pokemon* pokemon) {
    uint16_t dvs = pksav_bigendian16(pokemon->iv_data);
    return (dvs & 0x0FFF) == 0x0AAA && (dvs & 0x2000) != 0;
}

static void print_gen2_details(const struct pksav_gen2_pc_pokemon* pokemon) {
    printf("\tmoves=%u,%u,%u,%u\theld=%u\tlevel=%u\n",
           (unsigned) pokemon->moves[0], (unsigned) pokemon->moves[1],
           (unsigned) pokemon->moves[2], (unsigned) pokemon->moves[3],
           (unsigned) pokemon->held_item, (unsigned) pokemon->level);
}

static void print_gen3_details(const struct pksav_gen3_pc_pokemon* pokemon) {
    uint32_t personality = pksav_littleendian32(pokemon->personality);
    printf("\tmoves=%u,%u,%u,%u\theld=%u\tnature=%s\n",
           (unsigned) pksav_littleendian16(pokemon->blocks.attacks.moves[0]),
           (unsigned) pksav_littleendian16(pokemon->blocks.attacks.moves[1]),
           (unsigned) pksav_littleendian16(pokemon->blocks.attacks.moves[2]),
           (unsigned) pksav_littleendian16(pokemon->blocks.attacks.moves[3]),
           (unsigned) pksav_littleendian16(pokemon->blocks.growth.held_item),
           nature_name(personality));
}

static void decoded_text(const uint8_t* encoded, size_t characters,
                         char* output, size_t output_size) {
    char decoded[128] = {0};
    size_t length;
    size_t write_index = 0;

    if (!output_size) return;
    output[0] = '\0';
    if (!encoded || pksav_gen3_import_text(encoded, decoded, characters) !=
                       PKSAV_ERROR_NONE) {
        snprintf(output, output_size, "Unknown");
        return;
    }
    length = strnlen(decoded, sizeof(decoded));
    for (size_t i = 0; i < length && write_index + 1 < output_size; ++i) {
        unsigned char character = (unsigned char) decoded[i];
        /* Keep the inspect protocol one-record-per-line and tab-delimited. */
        if (character == '\t' || character == '\r' || character == '\n' ||
            character == ',') {
            character = ' ';
        }
        output[write_index++] = (char) character;
    }
    output[write_index] = '\0';
    if (!write_index) snprintf(output, output_size, "(none)");
}

static void decoded_gen1_text(const uint8_t* encoded, size_t characters,
                              char* output, size_t output_size) {
    char decoded[128] = {0};
    size_t length;
    size_t write_index = 0;

    if (!output_size) return;
    output[0] = '\0';
    if (!encoded || pksav_gen1_import_text(encoded, decoded, characters) !=
                       PKSAV_ERROR_NONE) {
        snprintf(output, output_size, "Unknown");
        return;
    }
    length = strnlen(decoded, sizeof(decoded));
    for (size_t i = 0; i < length && write_index + 1 < output_size; ++i) {
        unsigned char character = (unsigned char) decoded[i];
        if (character == '\t' || character == '\r' || character == '\n' ||
            character == ',') character = ' ';
        output[write_index++] = (char) character;
    }
    output[write_index] = '\0';
    if (!write_index) snprintf(output, output_size, "(none)");
}

static void decoded_gen2_text(const uint8_t* encoded, size_t characters,
                              char* output, size_t output_size) {
    char decoded[128] = {0};
    size_t length;
    size_t write_index = 0;

    if (!output_size) return;
    output[0] = '\0';
    if (!encoded || pksav_gen2_import_text(encoded, decoded, characters) !=
                       PKSAV_ERROR_NONE) {
        snprintf(output, output_size, "Unknown");
        return;
    }
    length = strnlen(decoded, sizeof(decoded));
    for (size_t i = 0; i < length && write_index + 1 < output_size; ++i) {
        unsigned char character = (unsigned char) decoded[i];
        if (character == '\t' || character == '\r' || character == '\n' ||
            character == ',') character = ' ';
        output[write_index++] = (char) character;
    }
    output[write_index] = '\0';
    if (!write_index) snprintf(output, output_size, "(none)");
}

static int parse_index(const char* text, unsigned maximum, unsigned* value) {
    char* end = NULL;
    unsigned long parsed;
    errno = 0;
    parsed = strtoul(text, &end, 10);
    if (errno || !end || *end || parsed > maximum) return 0;
    *value = (unsigned) parsed;
    return 1;
}

static int copy_file(const char* source, const char* destination) {
    FILE* input = NULL;
    FILE* output = NULL;
    unsigned char buffer[64 * 1024];
    size_t count;
    int result = 0;

    if (!strcmp(source, destination)) {
        fprintf(stderr, "error=output-must-differ-from-input\n");
        return 0;
    }
    input = fopen(source, "rb");
    if (!input) {
        fprintf(stderr, "error=open-input:%s:%s\n", source, strerror(errno));
        return 0;
    }
    output = fopen(destination, "wb");
    if (!output) {
        fprintf(stderr, "error=open-output:%s:%s\n", destination, strerror(errno));
        fclose(input);
        return 0;
    }
    while ((count = fread(buffer, 1, sizeof(buffer), input)) != 0) {
        if (fwrite(buffer, 1, count, output) != count) {
            fprintf(stderr, "error=write-output:%s:%s\n", destination, strerror(errno));
            goto done;
        }
    }
    if (ferror(input)) {
        fprintf(stderr, "error=read-input:%s:%s\n", source, strerror(errno));
        goto done;
    }
    if (fflush(output) != 0 || fsync(fileno(output)) != 0) {
        fprintf(stderr, "error=flush-output:%s:%s\n", destination, strerror(errno));
        goto done;
    }
    result = 1;
done:
    fclose(output);
    fclose(input);
    if (!result) unlink(destination);
    return result;
}

static int inspect_save(const char* path) {
    struct pksav_gen3_save save;
    enum pksav_error error;
    unsigned occupied = 0;
    char trainer_name[64];

    memset(&save, 0, sizeof(save));
    error = pksav_gen3_load_save_from_file(path, &save);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-save:%s:%s\n", path, pksav_strerror(error));
        return 1;
    }
    printf("save=%s\n", path);
    printf("generation=3\n");
    printf("save_type=%s\n", save_type_name(save.save_type));
    decoded_text(save.player_info.p_name, 7, trainer_name, sizeof(trainer_name));
    printf("trainer_name=%s\n", trainer_name);
    if (save.player_info.p_id) {
        printf("trainer_public_id=%u\n",
               pksav_littleendian16(save.player_info.p_id->pid));
        printf("trainer_secret_id=%u\n",
               pksav_littleendian16(save.player_info.p_id->sid));
    }
    printf("trainer_gender=%s\n", (save.player_info.p_gender &&
                                    *save.player_info.p_gender == 1) ?
                                   "female" : "male");
    printf("party_count=%" PRIu32 "\n", save.pokemon_storage.p_party->count);
    for (unsigned party_slot = 0;
         party_slot < save.pokemon_storage.p_party->count &&
         party_slot < PKSAV_GEN3_PARTY_NUM_POKEMON;
         ++party_slot) {
        const struct pksav_gen3_pc_pokemon* pokemon =
            &save.pokemon_storage.p_party->party[party_slot].pc_data;
        char nickname[64];
        decoded_text(pokemon->nickname, PKSAV_GEN3_POKEMON_NICKNAME_LENGTH,
                     nickname, sizeof(nickname));
        printf("party=slot:%u,species:%u,personality:%" PRIu32 ",shiny:%s,nickname:%s\n",
               party_slot, species_of(pokemon),
               pksav_littleendian32(pokemon->personality),
               pokemon_is_shiny(pokemon) ? "yes" : "no", nickname);
        printf("party_record\t%u\t%u\t%" PRIu32 "\t%s\t%s",
               party_slot, species_of(pokemon),
               pksav_littleendian32(pokemon->personality), nickname,
               pokemon_is_shiny(pokemon) ? "yes" : "no");
        print_gen3_details(pokemon);
    }
    for (unsigned box = 0; box < PKSAV_GEN3_NUM_POKEMON_BOXES; ++box) {
        for (unsigned slot = 0; slot < PKSAV_GEN3_BOX_NUM_POKEMON; ++slot) {
            const struct pksav_gen3_pc_pokemon* pokemon =
                &save.pokemon_storage.p_pc->boxes[box].entries[slot];
            if (!pokemon_present(pokemon)) continue;
            char nickname[64];
            decoded_text(pokemon->nickname, PKSAV_GEN3_POKEMON_NICKNAME_LENGTH,
                         nickname, sizeof(nickname));
            ++occupied;
            printf("pokemon=box:%u,slot:%u,species:%u,personality:%" PRIu32 ",shiny:%s,nickname:%s\n",
                   box, slot, species_of(pokemon),
                   pksav_littleendian32(pokemon->personality),
                   pokemon_is_shiny(pokemon) ? "yes" : "no", nickname);
            printf("box_record\t%u\t%u\t%u\t%" PRIu32 "\t%s\t%s",
                   box, slot, species_of(pokemon),
                   pksav_littleendian32(pokemon->personality), nickname,
                   pokemon_is_shiny(pokemon) ? "yes" : "no");
            print_gen3_details(pokemon);
        }
    }
    printf("box_occupied=%u\n", occupied);
    pksav_gen3_free_save(&save);
    return 0;
}

static const char* save_type_name_gen1(enum pksav_gen1_save_type type) {
    switch (type) {
    case PKSAV_GEN1_SAVE_TYPE_RED_BLUE: return "Red/Blue";
    case PKSAV_GEN1_SAVE_TYPE_YELLOW: return "Yellow";
    default: return "unknown";
    }
}

static const char* save_type_name_gen2(enum pksav_gen2_save_type type) {
    switch (type) {
    case PKSAV_GEN2_SAVE_TYPE_GS: return "Gold/Silver";
    case PKSAV_GEN2_SAVE_TYPE_CRYSTAL: return "Crystal";
    default: return "unknown";
    }
}

/*
 * Gen I/II store the currently selected PC box separately from the saved box
 * table. The library's setter flushes the OLD active box before selecting the
 * requested box; it does not flush changes made afterward. Gen II's game load
 * reads the banked table, so every Gen II writer must flush again before save.
 * These read helpers make
 * inspection agree with the game when a requested box is currently active.
 */
static const struct pksav_gen1_pokemon_box* gen1_box_for_read(
    const struct pksav_gen1_save* save, unsigned box) {
    unsigned current = *save->pokemon_storage.p_current_box_num &
                       PKSAV_GEN1_CURRENT_POKEMON_BOX_NUM_MASK;
    return box == current ? save->pokemon_storage.p_current_box :
                            save->pokemon_storage.pp_boxes[box];
}

static const struct pksav_gen2_pokemon_box* gen2_box_for_read(
    const struct pksav_gen2_save* save, unsigned box) {
    unsigned current = *save->pokemon_storage.p_current_box_num;
    return box == current ? save->pokemon_storage.p_current_box :
                            save->pokemon_storage.pp_boxes[box];
}

/* PKSav maps a Unicode NUL to character-map index 0 instead of stopping at
 * the end of a short name. GB games require 0x50; a zero byte is a text control
 * code. Write the complete storage field, including its terminator byte. */
static enum pksav_error export_gb_name(const char* text, uint8_t* field,
                                      size_t field_size, unsigned generation) {
    enum pksav_error error;
    if (!field_size) return PKSAV_ERROR_PARAM_OUT_OF_RANGE;
    memset(field, PKSAV_GEN2_TEXT_TERMINATOR, field_size);
    error = generation == 1 ?
        pksav_gen1_export_text(text, field, field_size - 1) :
        pksav_gen2_export_text(text, field, field_size - 1);
    if (error != PKSAV_ERROR_NONE) return error;
    for (size_t i = 0; i < field_size; ++i) {
        if (field[i] == 0 || field[i] == PKSAV_GEN2_TEXT_TERMINATOR) {
            memset(field + i, PKSAV_GEN2_TEXT_TERMINATOR, field_size - i);
            break;
        }
    }
    field[field_size - 1] = PKSAV_GEN2_TEXT_TERMINATOR;
    return PKSAV_ERROR_NONE;
}

static enum pksav_error save_gen2_with_synced_box(
    const char* path, struct pksav_gen2_save* save) {
    unsigned current = *save->pokemon_storage.p_current_box_num;
    if (current >= PKSAV_GEN2_NUM_POKEMON_BOXES)
        return PKSAV_ERROR_PARAM_OUT_OF_RANGE;

    /* PKSav's save routine updates checksums only. Crystal/Gold/Silver reload
     * the banked box on Continue, overwriting an edited active buffer unless
     * both representations contain the same complete record/name list. */
    *save->pokemon_storage.pp_boxes[current] =
        *save->pokemon_storage.p_current_box;
    return pksav_gen2_save_save(path, save);
}

static bool gen1_box_slot_present(const struct pksav_gen1_pokemon_box* box,
                                  unsigned slot) {
    return box && slot < box->count && box->species[slot] != 0 &&
           box->species[slot] != 0xFF;
}

static bool gen2_box_slot_present(const struct pksav_gen2_pokemon_box* box,
                                  unsigned slot) {
    return box && slot < box->count && box->species[slot] != 0 &&
           box->species[slot] != 0xFF;
}

static int inspect_gen1_save(const char* path) {
    struct pksav_gen1_save save;
    enum pksav_error error;
    unsigned occupied = 0;
    char trainer_name[64];

    memset(&save, 0, sizeof(save));
    error = pksav_gen1_load_save_from_file(path, &save);
    if (error != PKSAV_ERROR_NONE) return 1;
    printf("save=%s\n", path);
    printf("generation=1\n");
    printf("save_type=%s\n", save_type_name_gen1(save.save_type));
    decoded_gen1_text(save.trainer_info.p_name, PKSAV_GEN1_TRAINER_NAME_LENGTH,
                      trainer_name, sizeof(trainer_name));
    printf("trainer_name=%s\n", trainer_name);
    if (save.trainer_info.p_id)
        printf("trainer_public_id=%u\n", pksav_bigendian16(*save.trainer_info.p_id));
    printf("trainer_gender=unknown\n");
    printf("party_count=%u\n", (unsigned) save.pokemon_storage.p_party->count);
    for (unsigned slot = 0; slot < save.pokemon_storage.p_party->count &&
                             slot < PKSAV_GEN1_PARTY_NUM_POKEMON; ++slot) {
        const struct pksav_gen1_party_pokemon* pokemon =
            &save.pokemon_storage.p_party->party[slot];
        char nickname[64];
        decoded_gen1_text(save.pokemon_storage.p_party->nicknames[slot],
                          PKSAV_GEN1_POKEMON_NICKNAME_LENGTH,
                          nickname, sizeof(nickname));
        printf("party_record\t%u\t%u\t0\t%s\tno",
               slot, (unsigned) pokemon->pc_data.species, nickname);
        print_gen1_details(&pokemon->pc_data);
    }
    for (unsigned box = 0; box < PKSAV_GEN1_NUM_POKEMON_BOXES; ++box) {
        const struct pksav_gen1_pokemon_box* current =
            gen1_box_for_read(&save, box);
        if (!current) continue;
        for (unsigned slot = 0; slot < current->count &&
                             slot < PKSAV_GEN1_BOX_NUM_POKEMON; ++slot) {
            if (!gen1_box_slot_present(current, slot)) continue;
            char nickname[64];
            decoded_gen1_text(current->nicknames[slot],
                              PKSAV_GEN1_POKEMON_NICKNAME_LENGTH,
                              nickname, sizeof(nickname));
            ++occupied;
            printf("box_record\t%u\t%u\t%u\t0\t%s\tno",
                   box, slot, (unsigned) current->entries[slot].species,
                   nickname);
            print_gen1_details(&current->entries[slot]);
        }
    }
    printf("box_occupied=%u\n", occupied);
    pksav_gen1_free_save(&save);
    return 0;
}

static int inspect_gen2_save(const char* path) {
    struct pksav_gen2_save save;
    enum pksav_error error;
    unsigned occupied = 0;
    char trainer_name[64];

    memset(&save, 0, sizeof(save));
    error = pksav_gen2_load_save_from_file(path, &save);
    if (error != PKSAV_ERROR_NONE) return 1;
    printf("save=%s\n", path);
    printf("generation=2\n");
    printf("save_type=%s\n", save_type_name_gen2(save.save_type));
    decoded_gen2_text(save.trainer_info.p_name, PKSAV_GEN2_TRAINER_NAME_LENGTH,
                      trainer_name, sizeof(trainer_name));
    printf("trainer_name=%s\n", trainer_name);
    if (save.trainer_info.p_id)
        printf("trainer_public_id=%u\n", pksav_bigendian16(*save.trainer_info.p_id));
    printf("trainer_gender=%s\n", save.trainer_info.p_gender &&
                                    *save.trainer_info.p_gender == PKSAV_GEN2_GENDER_FEMALE ?
                                    "female" : "male");
    printf("party_count=%u\n", (unsigned) save.pokemon_storage.p_party->count);
    for (unsigned slot = 0; slot < save.pokemon_storage.p_party->count &&
                             slot < PKSAV_GEN2_PARTY_NUM_POKEMON; ++slot) {
        const struct pksav_gen2_party_pokemon* pokemon =
            &save.pokemon_storage.p_party->party[slot];
        char nickname[64];
        decoded_gen2_text(save.pokemon_storage.p_party->nicknames[slot],
                          PKSAV_GEN2_POKEMON_NICKNAME_LENGTH,
                          nickname, sizeof(nickname));
        printf("party_record\t%u\t%u\t0\t%s\t%s",
               slot, (unsigned) pokemon->pc_data.species, nickname,
               gen2_pokemon_is_shiny(&pokemon->pc_data) ? "yes" : "no");
        printf("\tegg=%s", save.pokemon_storage.p_party->species[slot] == 0xFD ? "yes" : "no");
        print_gen2_details(&pokemon->pc_data);
    }
    for (unsigned box = 0; box < PKSAV_GEN2_NUM_POKEMON_BOXES; ++box) {
        const struct pksav_gen2_pokemon_box* current =
            gen2_box_for_read(&save, box);
        if (!current) continue;
        for (unsigned slot = 0; slot < current->count &&
                             slot < PKSAV_GEN2_BOX_NUM_POKEMON; ++slot) {
            if (!gen2_box_slot_present(current, slot)) continue;
            char nickname[64];
            decoded_gen2_text(current->nicknames[slot],
                              PKSAV_GEN2_POKEMON_NICKNAME_LENGTH,
                              nickname, sizeof(nickname));
            ++occupied;
            printf("box_record\t%u\t%u\t%u\t0\t%s\t%s",
                   box, slot, (unsigned) current->entries[slot].species,
                   nickname, gen2_pokemon_is_shiny(&current->entries[slot]) ? "yes" : "no");
            printf("\tegg=%s", current->species[slot] == 0xFD ? "yes" : "no");
            print_gen2_details(&current->entries[slot]);
        }
    }
    printf("box_occupied=%u\n", occupied);
    pksav_gen2_free_save(&save);
    return 0;
}

static int inspect_any_save(const char* path) {
    struct stat info;
    if (stat(path, &info) != 0) {
        fprintf(stderr, "error=stat-save:%s:%s\n", path, strerror(errno));
        return 1;
    }
    /* Gen I/II are both 32 KiB, so size cannot distinguish them.  Try the
     * stricter Gen II loader first: a valid Gen II save can coincidentally
     * satisfy Gen I's one-byte checksum and then be interpreted with
     * incompatible offsets.  Some valid Crystal saves have one legacy
     * checksum absent, so probing only pksav_gen2_get_file_save_type() is not
     * sufficient; the actual loader accepts that documented variant. */
    if ((size_t) info.st_size <= PKSAV_GEN1_SAVE_SIZE) {
        if (inspect_gen2_save(path) == 0) return 0;
        if (inspect_gen1_save(path) == 0) return 0;
    } else if (inspect_save(path) == 0) {
        return 0;
    }
    /* Keep the old Gen III loader as a final fallback for unusual files. */
    if ((size_t) info.st_size <= PKSAV_GEN1_SAVE_SIZE)
        return inspect_save(path);
    fprintf(stderr, "error=unsupported-save-format:%s\n", path);
    return 1;
}

static int swap_gen1(const char* left_path, unsigned left_box_num,
                     unsigned left_slot, const char* right_path,
                     unsigned right_box_num, unsigned right_slot,
                     const char* output_left, const char* output_right) {
    struct pksav_gen1_save left;
    struct pksav_gen1_save right;
    struct pksav_gen1_pokemon_box* left_box;
    struct pksav_gen1_pokemon_box* right_box;
    struct pksav_gen1_pc_pokemon entry;
    uint8_t species;
    uint8_t otname[PKSAV_GEN1_POKEMON_OTNAME_STORAGE_LENGTH + 1];
    uint8_t nickname[PKSAV_GEN1_POKEMON_NICKNAME_LENGTH + 1];
    enum pksav_error error;

    memset(&left, 0, sizeof(left));
    memset(&right, 0, sizeof(right));
    if (!strcmp(left_path, right_path) || !strcmp(output_left, output_right)) {
        fprintf(stderr, "error=gen1-swap-needs-two-different-saves\n");
        return 1;
    }
    if (!copy_file(left_path, output_left) || !copy_file(right_path, output_right)) {
        unlink(output_left);
        unlink(output_right);
        return 1;
    }
    error = pksav_gen1_load_save_from_file(output_left, &left);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-left:%s\n", pksav_strerror(error));
        goto fail;
    }
    error = pksav_gen1_load_save_from_file(output_right, &right);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-right:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen1_pokemon_storage_set_current_box(
             &left.pokemon_storage, (uint8_t) left_box_num)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen1_pokemon_storage_set_current_box(
             &right.pokemon_storage, (uint8_t) right_box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error));
        goto fail;
    }
    left_box = left.pokemon_storage.p_current_box;
    right_box = right.pokemon_storage.p_current_box;
    if (!gen1_box_slot_present(left_box, left_slot) ||
        !gen1_box_slot_present(right_box, right_slot)) {
        fprintf(stderr, "error=empty-trade-slot\n");
        goto fail;
    }
    entry = left_box->entries[left_slot];
    left_box->entries[left_slot] = right_box->entries[right_slot];
    right_box->entries[right_slot] = entry;
    species = left_box->species[left_slot];
    left_box->species[left_slot] = right_box->species[right_slot];
    right_box->species[right_slot] = species;
    memcpy(otname, left_box->otnames[left_slot], sizeof(otname));
    memcpy(left_box->otnames[left_slot], right_box->otnames[right_slot], sizeof(otname));
    memcpy(right_box->otnames[right_slot], otname, sizeof(otname));
    memcpy(nickname, left_box->nicknames[left_slot], sizeof(nickname));
    memcpy(left_box->nicknames[left_slot], right_box->nicknames[right_slot], sizeof(nickname));
    memcpy(right_box->nicknames[right_slot], nickname, sizeof(nickname));
    if ((error = pksav_gen1_save_save(output_left, &left)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen1_save_save(output_right, &right)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-output:%s\n", pksav_strerror(error));
        goto fail;
    }
    printf("generation=1\nleft_output=%s\nright_output=%s\n", output_left, output_right);
    pksav_gen1_free_save(&left);
    pksav_gen1_free_save(&right);
    return 0;
fail:
    pksav_gen1_free_save(&left);
    pksav_gen1_free_save(&right);
    unlink(output_left);
    unlink(output_right);
    return 1;
}

static int copy_gen1(const char* source_path, unsigned source_box_num,
                     unsigned source_slot, const char* destination_path,
                     unsigned destination_box_num, unsigned destination_slot,
                     const char* output_destination) {
    struct pksav_gen1_save source;
    struct pksav_gen1_save destination;
    struct pksav_gen1_pokemon_box* source_box;
    struct pksav_gen1_pokemon_box* destination_box;
    enum pksav_error error;

    memset(&source, 0, sizeof(source));
    memset(&destination, 0, sizeof(destination));
    if (!strcmp(source_path, destination_path)) {
        fprintf(stderr, "error=gen1-copy-needs-two-different-saves\n");
        return 1;
    }
    if (!copy_file(destination_path, output_destination)) return 1;
    if ((error = pksav_gen1_load_save_from_file(source_path, &source)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-source:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen1_load_save_from_file(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-destination:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen1_pokemon_storage_set_current_box(
             &source.pokemon_storage, (uint8_t) source_box_num)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen1_pokemon_storage_set_current_box(
             &destination.pokemon_storage, (uint8_t) destination_box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error));
        goto fail;
    }
    source_box = source.pokemon_storage.p_current_box;
    destination_box = destination.pokemon_storage.p_current_box;
    if (!gen1_box_slot_present(source_box, source_slot)) {
        fprintf(stderr, "error=empty-source-slot\n");
        goto fail;
    }
    if (destination_box->count >= PKSAV_GEN1_BOX_NUM_POKEMON ||
        destination_slot != destination_box->count) {
        fprintf(stderr, "error=destination-box-not-ready-for-append\n");
        goto fail;
    }
    destination_box->entries[destination_slot] = source_box->entries[source_slot];
    destination_box->species[destination_slot] = source_box->species[source_slot];
    memcpy(destination_box->otnames[destination_slot], source_box->otnames[source_slot],
           sizeof(destination_box->otnames[destination_slot]));
    memcpy(destination_box->nicknames[destination_slot], source_box->nicknames[source_slot],
           sizeof(destination_box->nicknames[destination_slot]));
    ++destination_box->count;
    if (destination_box->count < PKSAV_GEN1_BOX_NUM_POKEMON)
        destination_box->species[destination_box->count] = 0xFF;
    if ((error = pksav_gen1_save_save(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-destination:%s\n", pksav_strerror(error));
        goto fail;
    }
    printf("generation=1\ncopied_species=%u\ndestination_output=%s\n",
           (unsigned) source_box->species[source_slot], output_destination);
    pksav_gen1_free_save(&source);
    pksav_gen1_free_save(&destination);
    return 0;
fail:
    pksav_gen1_free_save(&source);
    pksav_gen1_free_save(&destination);
    unlink(output_destination);
    return 1;
}

/* The ROM reader supplies a locally generated record. This writer only appends
 * a supported gift to an isolated output, never the input. */
static int gift_gen1(const char* destination_path, unsigned box_num,
                     unsigned slot, const char* record_path, unsigned national,
                     const char* nickname, const char* family, const char* output) {
    struct pksav_gen1_save save;
    struct pksav_gen1_pc_pokemon gift;
    struct pksav_gen1_pokemon_box* box;
    struct stat existing;
    enum pksav_error error;
    FILE* file;
    memset(&save, 0, sizeof(save));
    /* Numeric recipe validation; names, stats and PP are read from the ROM. */
    static const unsigned recipes[][6] = {
        {151, 21, 1, 0, 0, 0}, {25, 84, 84, 45, 57, 0},
        {25, 84, 84, 45, 19, 0}, {129, 133, 150, 82, 0, 0},
        {22, 35, 64, 45, 43, 6}, {78, 164, 52, 39, 23, 6},
        {54, 47, 10, 133, 0, 0}, {1, 153, 33, 45, 0, 0},
        {4, 176, 10, 45, 0, 0}, {7, 177, 33, 39, 0, 0},
        {106, 43, 24, 96, 0, 0}, {107, 44, 4, 97, 0, 0},
        {133, 102, 33, 28, 0, 0}, {133, 102, 33, 39, 0, 0},
        {138, 98, 55, 110, 0, 0},
        {140, 90, 10, 106, 0, 0}
    };
    if (!nickname[0] || strlen(nickname) > 10) return 2;
    if (lstat(output, &existing) == 0 || errno != ENOENT) {
        fprintf(stderr, "error=gift-output-must-be-new\n"); return 1;
    }
    file = fopen(record_path, "rb");
    if (!file) { fprintf(stderr, "error=gift-record-unreadable\n"); return 1; }
    size_t length = fread(&gift, 1, sizeof(gift), file);
    int extra = fgetc(file);
    fclose(file);
    bool supported = false;
    if (length == sizeof(gift)) {
        for (unsigned r = 0; r < sizeof(recipes) / sizeof(recipes[0]); ++r) {
            if (national != recipes[r][0] || gift.species != recipes[r][1]) continue;
            bool matches = true;
            for (unsigned i = 0; i < 4; ++i) if (gift.moves[i] != recipes[r][i + 2]) matches = false;
            if (matches) supported = true;
        }
    }
    if (length != sizeof(gift) || extra != EOF || gift.level != 5 ||
        gift.condition != 0 || !pksav_bigendian16(gift.current_hp) || !supported) {
        fprintf(stderr, "error=unsupported-gift-record\n"); return 1;
    }
    for (unsigned i = 0; i < 4; ++i) {
        if ((gift.moves[i] && (!gift.move_pps[i] || gift.move_pps[i] > 40)) ||
            (!gift.moves[i] && gift.move_pps[i])) {
            fprintf(stderr, "error=invalid-gift-pp\n"); return 1;
        }
    }
    if (!copy_file(destination_path, output)) return 1;
    if ((error = pksav_gen1_load_save_from_file(output, &save)) != PKSAV_ERROR_NONE) goto fail;
    if ((save.save_type == PKSAV_GEN1_SAVE_TYPE_YELLOW && strcmp(family, "yellow")) ||
        (save.save_type == PKSAV_GEN1_SAVE_TYPE_RED_BLUE && strcmp(family, "red-blue"))) {
        fprintf(stderr, "error=gift-rom-save-family-mismatch\n"); goto reject;
    }
    unsigned current = *save.pokemon_storage.p_current_box_num &
                       PKSAV_GEN1_CURRENT_POKEMON_BOX_NUM_MASK;
    if (current >= PKSAV_GEN1_NUM_POKEMON_BOXES) {
        fprintf(stderr, "error=gift-invalid-current-box\n"); goto reject;
    }
    /* Before the player's first box switch, SRAM box headers are uninitialized.
     * Follow the game's initialization and retain the active box contents. */
    if (!(*save.pokemon_storage.p_current_box_num & 0x80)) {
        for (unsigned i = 0; i < PKSAV_GEN1_NUM_POKEMON_BOXES; ++i) {
            save.pokemon_storage.pp_boxes[i]->count = 0;
            save.pokemon_storage.pp_boxes[i]->species[0] = 0xFF;
        }
        *save.pokemon_storage.p_current_box_num |= 0x80;
    }
    if ((error = pksav_gen1_pokemon_storage_set_current_box(&save.pokemon_storage,
                                                           (uint8_t)box_num)) != PKSAV_ERROR_NONE) goto fail;
    box = save.pokemon_storage.p_current_box;
    if (box->count >= PKSAV_GEN1_BOX_NUM_POKEMON || slot != box->count) {
        fprintf(stderr, "error=gift-box-not-ready-for-append\n"); goto reject;
    }
    gift.ot_id = *save.trainer_info.p_id;
    box->entries[slot] = gift;
    box->species[slot] = gift.species;
    memset(box->otnames[slot], 0x50, sizeof(box->otnames[slot]));
    memcpy(box->otnames[slot], save.trainer_info.p_name, PKSAV_GEN1_TRAINER_NAME_LENGTH);
    if ((error = export_gb_name(nickname, box->nicknames[slot], sizeof(box->nicknames[slot]), 1)) != PKSAV_ERROR_NONE) goto fail;
    ++box->count;
    box->species[box->count] = 0xFF;
    /* Flush the updated active box into its banked copy before saving. */
    *save.pokemon_storage.pp_boxes[box_num] = *box;
    /* Gen I SRAM has a whole-bank checksum and six individual box checksums. */
    for (unsigned half = 0; half < 2; ++half) {
        uint8_t* bank = (uint8_t*)save.pokemon_storage.pp_boxes[half * 6];
        const size_t box_size = sizeof(struct pksav_gen1_pokemon_box);
        unsigned sum = 0;
        for (size_t i = 0; i < box_size * 6; ++i) sum += bank[i];
        bank[box_size * 6] = (uint8_t)~sum;
        for (unsigned i = 0; i < 6; ++i) {
            sum = 0;
            for (size_t j = 0; j < box_size; ++j) sum += bank[i * box_size + j];
            bank[box_size * 6 + 1 + i] = (uint8_t)~sum;
        }
    }
    if ((error = pksav_set_pokedex_bit(save.pokedex_lists.p_seen, national, true)) != PKSAV_ERROR_NONE ||
        (error = pksav_set_pokedex_bit(save.pokedex_lists.p_owned, national, true)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen1_save_save(output, &save)) != PKSAV_ERROR_NONE) goto fail;
    pksav_gen1_free_save(&save);
    printf("generation=1\ngift_species=%u\ndestination_output=%s\n", national, output);
    return 0;
fail:
    fprintf(stderr, "error=gift-save:%s\n", pksav_strerror(error));
reject:
    pksav_gen1_free_save(&save);
    unlink(output);
    return 1;
}

static int swap_gen2(const char* left_path, unsigned left_box_num,
                     unsigned left_slot, const char* right_path,
                     unsigned right_box_num, unsigned right_slot,
                     const char* output_left, const char* output_right) {
    struct pksav_gen2_save left;
    struct pksav_gen2_save right;
    struct pksav_gen2_pokemon_box* left_box;
    struct pksav_gen2_pokemon_box* right_box;
    struct pksav_gen2_pc_pokemon entry;
    uint8_t species;
    uint8_t otname[PKSAV_GEN2_POKEMON_OTNAME_STORAGE_LENGTH + 1];
    uint8_t nickname[PKSAV_GEN2_POKEMON_NICKNAME_LENGTH + 1];
    enum pksav_error error;

    memset(&left, 0, sizeof(left));
    memset(&right, 0, sizeof(right));
    if (!strcmp(left_path, right_path) || !strcmp(output_left, output_right)) {
        fprintf(stderr, "error=gen2-swap-needs-two-different-saves\n");
        return 1;
    }
    if (!copy_file(left_path, output_left) || !copy_file(right_path, output_right)) {
        unlink(output_left);
        unlink(output_right);
        return 1;
    }
    if ((error = pksav_gen2_load_save_from_file(output_left, &left)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-left:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen2_load_save_from_file(output_right, &right)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-right:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen2_pokemon_storage_set_current_box(
             &left.pokemon_storage, (uint8_t) left_box_num)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen2_pokemon_storage_set_current_box(
             &right.pokemon_storage, (uint8_t) right_box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error));
        goto fail;
    }
    left_box = left.pokemon_storage.p_current_box;
    right_box = right.pokemon_storage.p_current_box;
    if (!gen2_box_slot_present(left_box, left_slot) ||
        !gen2_box_slot_present(right_box, right_slot)) {
        fprintf(stderr, "error=empty-trade-slot\n");
        goto fail;
    }
    entry = left_box->entries[left_slot];
    left_box->entries[left_slot] = right_box->entries[right_slot];
    right_box->entries[right_slot] = entry;
    species = left_box->species[left_slot];
    left_box->species[left_slot] = right_box->species[right_slot];
    right_box->species[right_slot] = species;
    memcpy(otname, left_box->otnames[left_slot], sizeof(otname));
    memcpy(left_box->otnames[left_slot], right_box->otnames[right_slot], sizeof(otname));
    memcpy(right_box->otnames[right_slot], otname, sizeof(otname));
    memcpy(nickname, left_box->nicknames[left_slot], sizeof(nickname));
    memcpy(left_box->nicknames[left_slot], right_box->nicknames[right_slot], sizeof(nickname));
    memcpy(right_box->nicknames[right_slot], nickname, sizeof(nickname));
    if ((error = save_gen2_with_synced_box(output_left, &left)) != PKSAV_ERROR_NONE ||
        (error = save_gen2_with_synced_box(output_right, &right)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-output:%s\n", pksav_strerror(error));
        goto fail;
    }
    printf("generation=2\nleft_output=%s\nright_output=%s\n", output_left, output_right);
    pksav_gen2_free_save(&left);
    pksav_gen2_free_save(&right);
    return 0;
fail:
    pksav_gen2_free_save(&left);
    pksav_gen2_free_save(&right);
    unlink(output_left);
    unlink(output_right);
    return 1;
}

static int copy_gen2(const char* source_path, unsigned source_box_num,
                     unsigned source_slot, const char* destination_path,
                     unsigned destination_box_num, unsigned destination_slot,
                     const char* output_destination) {
    struct pksav_gen2_save source;
    struct pksav_gen2_save destination;
    struct pksav_gen2_pokemon_box* source_box;
    struct pksav_gen2_pokemon_box* destination_box;
    enum pksav_error error;

    memset(&source, 0, sizeof(source));
    memset(&destination, 0, sizeof(destination));
    if (!strcmp(source_path, destination_path)) {
        fprintf(stderr, "error=gen2-copy-needs-two-different-saves\n");
        return 1;
    }
    if (!copy_file(destination_path, output_destination)) return 1;
    if ((error = pksav_gen2_load_save_from_file(source_path, &source)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-source:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen2_load_save_from_file(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-destination:%s\n", pksav_strerror(error));
        goto fail;
    }
    if ((error = pksav_gen2_pokemon_storage_set_current_box(
             &source.pokemon_storage, (uint8_t) source_box_num)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen2_pokemon_storage_set_current_box(
             &destination.pokemon_storage, (uint8_t) destination_box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error));
        goto fail;
    }
    source_box = source.pokemon_storage.p_current_box;
    destination_box = destination.pokemon_storage.p_current_box;
    if (!gen2_box_slot_present(source_box, source_slot)) {
        fprintf(stderr, "error=empty-source-slot\n");
        goto fail;
    }
    if (destination_box->count >= PKSAV_GEN2_BOX_NUM_POKEMON ||
        destination_slot != destination_box->count) {
        fprintf(stderr, "error=destination-box-not-ready-for-append\n");
        goto fail;
    }
    destination_box->entries[destination_slot] = source_box->entries[source_slot];
    destination_box->species[destination_slot] = source_box->species[source_slot];
    memcpy(destination_box->otnames[destination_slot], source_box->otnames[source_slot],
           sizeof(destination_box->otnames[destination_slot]));
    memcpy(destination_box->nicknames[destination_slot], source_box->nicknames[source_slot],
           sizeof(destination_box->nicknames[destination_slot]));
    ++destination_box->count;
    if (destination_box->count < PKSAV_GEN2_BOX_NUM_POKEMON)
        destination_box->species[destination_box->count] = 0xFF;
    if ((error = save_gen2_with_synced_box(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-destination:%s\n", pksav_strerror(error));
        goto fail;
    }
    printf("generation=2\ncopied_species=%u\ndestination_output=%s\n",
           (unsigned) source_box->species[source_slot], output_destination);
    pksav_gen2_free_save(&source);
    pksav_gen2_free_save(&destination);
    return 0;
fail:
    pksav_gen2_free_save(&source);
    pksav_gen2_free_save(&destination);
    unlink(output_destination);
    return 1;
}

/* Gold/Silver/Crystal's Time Capsule converts only these catch-rate bytes.
 * All other values are retained and interpreted as their Gen II item ID. */
static uint8_t time_capsule_held_item(uint8_t catch_rate) {
    switch (catch_rate) {
    case 0x19: return 0x92; /* LEFTOVERS */
    case 0x2d: return 0x53; /* BITTER_BERRY */
    case 0x32: return 0xae; /* GOLD_BERRY */
    case 0x5a: case 0x64: case 0x78: case 0x87:
    case 0xbe: case 0xc3: case 0xdc: case 0xfa:
        return 0xad; /* BERRY */
    default: return catch_rate;
    }
}

static int transfer_gen1_to_gen2(const char* source_path, unsigned source_box_num,
                                 unsigned source_slot, unsigned national_species,
                                 const char* destination_path, unsigned destination_box_num,
                                 unsigned destination_slot, const char* output_destination) {
    struct pksav_gen1_save source;
    struct pksav_gen2_save destination;
    struct pksav_gen1_pokemon_box* source_box;
    struct pksav_gen2_pokemon_box* destination_box;
    struct pksav_gen2_pc_pokemon converted;
    char text[PKSAV_GEN1_POKEMON_NICKNAME_LENGTH + 1];
    enum pksav_error error;

    memset(&source, 0, sizeof(source));
    memset(&destination, 0, sizeof(destination));
    memset(&converted, 0, sizeof(converted));
    if (!national_species || national_species > PKSAV_GEN1_POKEDEX_NUM_POKEMON) {
        fprintf(stderr, "error=invalid-gen1-national-species\n");
        return 1;
    }
    if (!strcmp(source_path, destination_path)) {
        fprintf(stderr, "error=time-capsule-needs-two-different-saves\n");
        return 1;
    }
    if (!copy_file(destination_path, output_destination)) return 1;
    if ((error = pksav_gen1_load_save_from_file(source_path, &source)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-source:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen2_load_save_from_file(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-destination:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen1_pokemon_storage_set_current_box(&source.pokemon_storage,
             (uint8_t) source_box_num)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen2_pokemon_storage_set_current_box(&destination.pokemon_storage,
             (uint8_t) destination_box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error)); goto fail;
    }
    source_box = source.pokemon_storage.p_current_box;
    destination_box = destination.pokemon_storage.p_current_box;
    if (!gen1_box_slot_present(source_box, source_slot)) {
        fprintf(stderr, "error=empty-source-slot\n"); goto fail;
    }
    if (destination_box->count >= PKSAV_GEN2_BOX_NUM_POKEMON ||
        destination_slot != destination_box->count) {
        fprintf(stderr, "error=destination-box-not-ready-for-append\n"); goto fail;
    }

    /* These fields are shared by the Game Boy PC record formats. The fields
     * new to Gen II intentionally use the values a Time Capsule arrival gets. */
    converted.species = (uint8_t) national_species;
    converted.held_item = time_capsule_held_item(source_box->entries[source_slot].catch_rate);
    memcpy(converted.moves, source_box->entries[source_slot].moves, sizeof(converted.moves));
    converted.ot_id = source_box->entries[source_slot].ot_id;
    memcpy(converted.exp, source_box->entries[source_slot].exp, sizeof(converted.exp));
    converted.ev_hp = source_box->entries[source_slot].ev_hp;
    converted.ev_atk = source_box->entries[source_slot].ev_atk;
    converted.ev_def = source_box->entries[source_slot].ev_def;
    converted.ev_spd = source_box->entries[source_slot].ev_spd;
    converted.ev_spcl = source_box->entries[source_slot].ev_spcl;
    converted.iv_data = source_box->entries[source_slot].iv_data;
    memcpy(converted.move_pps, source_box->entries[source_slot].move_pps, sizeof(converted.move_pps));
    converted.friendship = 70;
    converted.pokerus = 0;
    converted.caught_data = 0;
    converted.level = source_box->entries[source_slot].level;
    if ((error = pksav_gen1_import_text(source_box->otnames[source_slot], text,
             PKSAV_GEN1_POKEMON_OTNAME_LENGTH)) != PKSAV_ERROR_NONE ||
        (error = export_gb_name(text, destination_box->otnames[destination_slot],
             sizeof(destination_box->otnames[destination_slot]), 2)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen1_import_text(source_box->nicknames[source_slot], text,
             PKSAV_GEN1_POKEMON_NICKNAME_LENGTH)) != PKSAV_ERROR_NONE ||
        (error = export_gb_name(text, destination_box->nicknames[destination_slot],
             sizeof(destination_box->nicknames[destination_slot]), 2)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=convert-text:%s\n", pksav_strerror(error)); goto fail;
    }
    destination_box->entries[destination_slot] = converted;
    destination_box->species[destination_slot] = (uint8_t) national_species;
    ++destination_box->count;
    if (destination_box->count < PKSAV_GEN2_BOX_NUM_POKEMON)
        destination_box->species[destination_box->count] = 0xff;
    if ((error = save_gen2_with_synced_box(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-destination:%s\n", pksav_strerror(error)); goto fail;
    }
    printf("generation=1-to-2\nconverted_species=%u\nheld_item=%u\ndestination_output=%s\n",
           national_species, (unsigned) converted.held_item, output_destination);
    pksav_gen1_free_save(&source); pksav_gen2_free_save(&destination); return 0;
fail:
    pksav_gen1_free_save(&source); pksav_gen2_free_save(&destination);
    unlink(output_destination); return 1;
}

static uint8_t scaled_gen2_ev(uint16_t raw) {
    return (uint8_t)(((uint32_t) raw * 255u + 32767u) / 65535u);
}

static void normalize_gen3_evs(uint8_t evs[6], unsigned* reduced) {
    unsigned total = 0;
    unsigned original;
    for (unsigned i = 0; i < 6; ++i) total += evs[i];
    original = total;
    if (total > 510u) {
        for (unsigned i = 0; i < 6; ++i)
            evs[i] = (uint8_t)((evs[i] * 510u) / total);
        total = 0;
        for (unsigned i = 0; i < 6; ++i) total += evs[i];
        /* Give any rounding remainder to the first nonzero stats. */
        for (unsigned i = 0; total < 510u && i < 6; ++i) {
            if (evs[i] && evs[i] < 255u) { ++evs[i]; ++total; }
        }
    }
    if (reduced) *reduced = original > 510u ? original - total : 0u;
}

static uint32_t migration_personality(const struct pksav_gen2_pc_pokemon* source,
                                      unsigned species) {
    /* A stable, non-random PID keeps repeated previews deterministic. */
    uint32_t value = 2166136261u;
    const uint8_t* bytes = (const uint8_t*) source;
    for (size_t i = 0; i < sizeof(*source); ++i) {
        value ^= bytes[i];
        value *= 16777619u;
    }
    value ^= species * 0x9e3779b9u;
    return value ? value : 1u;
}

static int copy_gen2_to_gen3(const char* source_path, unsigned source_box_num,
                             unsigned source_slot, unsigned national_species,
                             const char* destination_path, unsigned destination_box_num,
                             unsigned destination_slot, const char* output_destination) {
    struct pksav_gen2_save source;
    struct pksav_gen3_save destination;
    struct pksav_gen2_pokemon_box* source_box;
    struct pksav_gen3_pc_pokemon* destination_pokemon;
    const struct pksav_gen2_pc_pokemon* old_pokemon;
    struct pksav_gen3_pc_pokemon converted;
    uint8_t gb_ivs[PKSAV_NUM_GB_IVS] = {0};
    uint8_t evs[6];
    char text[PKSAV_GEN2_POKEMON_NICKNAME_LENGTH + 1];
    size_t experience = 0;
    unsigned cleared_item = 0, reduced_evs = 0, cleared_moves = 0;
    enum pksav_error error;

    memset(&source, 0, sizeof(source));
    memset(&destination, 0, sizeof(destination));
    memset(&converted, 0, sizeof(converted));
    if (!national_species || national_species > 251u) {
        fprintf(stderr, "error=invalid-gen2-national-species\n"); return 1;
    }
    if (!strcmp(source_path, destination_path)) {
        fprintf(stderr, "error=gen2-to-gen3-needs-two-different-saves\n"); return 1;
    }
    if (!copy_file(destination_path, output_destination)) return 1;
    if ((error = pksav_gen2_load_save_from_file(source_path, &source)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-source:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen3_load_save_from_file(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-destination:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen2_pokemon_storage_set_current_box(&source.pokemon_storage,
             (uint8_t) source_box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-source-box:%s\n", pksav_strerror(error)); goto fail;
    }
    source_box = source.pokemon_storage.p_current_box;
    if (!gen2_box_slot_present(source_box, source_slot)) {
        fprintf(stderr, "error=empty-source-slot\n"); goto fail;
    }
    if (source_box->species[source_slot] == 0xFD) {
        fprintf(stderr, "error=hatch-gen2-egg-before-gen3-transfer\n"); goto fail;
    }
    destination_pokemon = &destination.pokemon_storage.p_pc->boxes[destination_box_num]
                               .entries[destination_slot];
    if (pokemon_present(destination_pokemon)) {
        fprintf(stderr, "error=destination-slot-not-empty\n"); goto fail;
    }
    old_pokemon = &source_box->entries[source_slot];
    converted.personality = pksav_littleendian32(migration_personality(old_pokemon, national_species));
    converted.ot_id.id = pksav_littleendian32((uint32_t)pksav_bigendian16(old_pokemon->ot_id));
    converted.language = pksav_littleendian16(PKSAV_GEN3_LANGUAGE_ENGLISH);
    converted.blocks.growth.species = pksav_littleendian16((uint16_t)national_species);
    converted.blocks.growth.held_item = pksav_littleendian16(gen2_held_item_to_gen3(old_pokemon->held_item, &cleared_item));
    if ((error = pksav_import_base256(old_pokemon->exp, sizeof(old_pokemon->exp), &experience)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=convert-exp:%s\n", pksav_strerror(error)); goto fail;
    }
    converted.blocks.growth.exp = pksav_littleendian32((uint32_t)experience);
    converted.blocks.growth.friendship = old_pokemon->friendship;
    for (unsigned i = 0; i < 4; ++i) {
        /* All defined Gen II moves are present in Gen III. Empty slots stay empty. */
        if (old_pokemon->moves[i] > 251u) { ++cleared_moves; continue; }
        converted.blocks.attacks.moves[i] = pksav_littleendian16(old_pokemon->moves[i]);
        converted.blocks.attacks.move_pps[i] = old_pokemon->move_pps[i] & PKSAV_GEN2_POKEMON_MOVE_PP_MASK;
        converted.blocks.growth.pp_up |= (uint8_t)((old_pokemon->move_pps[i] >> 6u & 3u) << (i * 2u));
    }
    evs[0] = scaled_gen2_ev(pksav_bigendian16(old_pokemon->ev_hp));
    evs[1] = scaled_gen2_ev(pksav_bigendian16(old_pokemon->ev_atk));
    evs[2] = scaled_gen2_ev(pksav_bigendian16(old_pokemon->ev_def));
    evs[3] = scaled_gen2_ev(pksav_bigendian16(old_pokemon->ev_spd));
    evs[4] = scaled_gen2_ev(pksav_bigendian16(old_pokemon->ev_spcl));
    evs[5] = evs[4];
    normalize_gen3_evs(evs, &reduced_evs);
    converted.blocks.effort.ev_hp = evs[0]; converted.blocks.effort.ev_atk = evs[1];
    converted.blocks.effort.ev_def = evs[2]; converted.blocks.effort.ev_spd = evs[3];
    converted.blocks.effort.ev_spatk = evs[4]; converted.blocks.effort.ev_spdef = evs[5];
    {
        uint16_t native_ivs = pksav_bigendian16(old_pokemon->iv_data);
        error = pksav_get_gb_IVs(&native_ivs, gb_ivs, sizeof(gb_ivs));
    }
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=convert-ivs:%s\n", pksav_strerror(error)); goto fail;
    }
    /* Expand each 0..15 DV to the middle of its corresponding Gen III range. */
    pksav_set_IV(PKSAV_IV_HP, (uint8_t)(gb_ivs[PKSAV_GB_IV_HP] * 2u + 1u), &converted.blocks.misc.iv_egg_ability);
    pksav_set_IV(PKSAV_IV_ATTACK, (uint8_t)(gb_ivs[PKSAV_GB_IV_ATTACK] * 2u + 1u), &converted.blocks.misc.iv_egg_ability);
    pksav_set_IV(PKSAV_IV_DEFENSE, (uint8_t)(gb_ivs[PKSAV_GB_IV_DEFENSE] * 2u + 1u), &converted.blocks.misc.iv_egg_ability);
    pksav_set_IV(PKSAV_IV_SPEED, (uint8_t)(gb_ivs[PKSAV_GB_IV_SPEED] * 2u + 1u), &converted.blocks.misc.iv_egg_ability);
    pksav_set_IV(PKSAV_IV_SPATK, (uint8_t)(gb_ivs[PKSAV_GB_IV_SPECIAL] * 2u + 1u), &converted.blocks.misc.iv_egg_ability);
    pksav_set_IV(PKSAV_IV_SPDEF, (uint8_t)(gb_ivs[PKSAV_GB_IV_SPECIAL] * 2u + 1u), &converted.blocks.misc.iv_egg_ability);
    if ((error = pksav_gen2_import_text(source_box->otnames[source_slot], text,
             PKSAV_GEN2_POKEMON_OTNAME_LENGTH)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen3_export_text(text, converted.otname,
             PKSAV_GEN3_POKEMON_OTNAME_LENGTH)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen2_import_text(source_box->nicknames[source_slot], text,
             PKSAV_GEN2_POKEMON_NICKNAME_LENGTH)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen3_export_text(text, converted.nickname,
             PKSAV_GEN3_POKEMON_NICKNAME_LENGTH)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=convert-text:%s\n", pksav_strerror(error)); goto fail;
    }
    *destination_pokemon = converted;
    if ((error = pksav_gen3_save_save(output_destination, &destination)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-destination:%s\n", pksav_strerror(error)); goto fail;
    }
    printf("generation=2-to-3\nconverted_species=%u\nheld_item_cleared=%u\n"
           "moves_cleared=%u\nev_points_reduced=%u\ndestination_output=%s\n",
           national_species, cleared_item, cleared_moves, reduced_evs, output_destination);
    pksav_gen2_free_save(&source); pksav_gen3_free_save(&destination); return 0;
fail:
    pksav_gen2_free_save(&source); pksav_gen3_free_save(&destination);
    unlink(output_destination); return 1;
}

/* This command only changes a caller-provided working copy. Eligibility is
 * deliberately decided by the SDL layer, which has the matching ROM's species
 * table and can explain the choice to the player. */
static int evolve_gen1(const char* source_path, unsigned box_num, unsigned slot,
                       unsigned evolved_species, const char* nickname,
                       const char* output_path) {
    struct pksav_gen1_save save;
    struct pksav_gen1_pokemon_box* box;
    enum pksav_error error;
    memset(&save, 0, sizeof(save));
    if (!copy_file(source_path, output_path)) return 1;
    if ((error = pksav_gen1_load_save_from_file(output_path, &save)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-save:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen1_pokemon_storage_set_current_box(&save.pokemon_storage,
             (uint8_t)box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error)); goto fail;
    }
    box = save.pokemon_storage.p_current_box;
    if (!gen1_box_slot_present(box, slot)) { fprintf(stderr, "error=empty-source-slot\n"); goto fail; }
    box->entries[slot].species = (uint8_t)evolved_species;
    box->species[slot] = (uint8_t)evolved_species;
    if (nickname && (error = export_gb_name(nickname,
            box->nicknames[slot], sizeof(box->nicknames[slot]), 1)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=nickname:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen1_save_save(output_path, &save)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save:%s\n", pksav_strerror(error)); goto fail;
    }
    printf("evolved_generation=1\nevolved_species=%u\noutput=%s\n", evolved_species, output_path);
    pksav_gen1_free_save(&save); return 0;
fail:
    pksav_gen1_free_save(&save); unlink(output_path); return 1;
}

static int evolve_gen2(const char* source_path, unsigned box_num, unsigned slot,
                       unsigned evolved_species, const char* nickname,
                       const char* output_path) {
    struct pksav_gen2_save save;
    struct pksav_gen2_pokemon_box* box;
    enum pksav_error error;
    memset(&save, 0, sizeof(save));
    if (!copy_file(source_path, output_path)) return 1;
    if ((error = pksav_gen2_load_save_from_file(output_path, &save)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-save:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen2_pokemon_storage_set_current_box(&save.pokemon_storage,
             (uint8_t)box_num)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=select-box:%s\n", pksav_strerror(error)); goto fail;
    }
    box = save.pokemon_storage.p_current_box;
    if (!gen2_box_slot_present(box, slot)) { fprintf(stderr, "error=empty-source-slot\n"); goto fail; }
    box->entries[slot].species = (uint8_t)evolved_species;
    box->species[slot] = (uint8_t)evolved_species;
    if (nickname && (error = export_gb_name(nickname,
            box->nicknames[slot], sizeof(box->nicknames[slot]), 2)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=nickname:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = save_gen2_with_synced_box(output_path, &save)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save:%s\n", pksav_strerror(error)); goto fail;
    }
    printf("evolved_generation=2\nevolved_species=%u\noutput=%s\n", evolved_species, output_path);
    pksav_gen2_free_save(&save); return 0;
fail:
    pksav_gen2_free_save(&save); unlink(output_path); return 1;
}

static int evolve_gen3(const char* source_path, unsigned box_num, unsigned slot,
                       unsigned evolved_species, const char* nickname,
                       const char* output_path) {
    struct pksav_gen3_save save;
    struct pksav_gen3_pc_pokemon* pokemon;
    enum pksav_error error;
    memset(&save, 0, sizeof(save));
    if (!copy_file(source_path, output_path)) return 1;
    if ((error = pksav_gen3_load_save_from_file(output_path, &save)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-save:%s\n", pksav_strerror(error)); goto fail;
    }
    pokemon = &save.pokemon_storage.p_pc->boxes[box_num].entries[slot];
    if (!pokemon_present(pokemon)) { fprintf(stderr, "error=empty-source-slot\n"); goto fail; }
    pokemon->blocks.growth.species = pksav_littleendian16((uint16_t)evolved_species);
    if (nickname && (error = pksav_gen3_export_text(nickname, pokemon->nickname,
            PKSAV_GEN3_POKEMON_NICKNAME_LENGTH)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=nickname:%s\n", pksav_strerror(error)); goto fail;
    }
    if ((error = pksav_gen3_save_save(output_path, &save)) != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save:%s\n", pksav_strerror(error)); goto fail;
    }
    printf("evolved_generation=3\nevolved_species=%u\noutput=%s\n", evolved_species, output_path);
    pksav_gen3_free_save(&save); return 0;
fail:
    pksav_gen3_free_save(&save); unlink(output_path); return 1;
}

static int swap_gen3(const char* left_path, unsigned left_box, unsigned left_slot,
                     const char* right_path, unsigned right_box, unsigned right_slot,
                     const char* output_left, const char* output_right) {
    struct pksav_gen3_save left;
    struct pksav_gen3_save right;
    struct pksav_gen3_pc_pokemon temporary;
    enum pksav_error error;
    struct pksav_gen3_pc_pokemon* left_before;
    struct pksav_gen3_pc_pokemon* right_before;
    uint16_t left_species;
    uint16_t right_species;

    memset(&left, 0, sizeof(left));
    memset(&right, 0, sizeof(right));
    if (!copy_file(left_path, output_left) || !copy_file(right_path, output_right)) {
        unlink(output_left);
        unlink(output_right);
        return 1;
    }
    error = pksav_gen3_load_save_from_file(output_left, &left);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-left:%s\n", pksav_strerror(error));
        goto fail;
    }
    error = pksav_gen3_load_save_from_file(output_right, &right);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-right:%s\n", pksav_strerror(error));
        goto fail;
    }
    if (left.save_type != right.save_type) {
        fprintf(stderr, "error=incompatible-gen3-save-types:%s:%s\n",
                save_type_name(left.save_type), save_type_name(right.save_type));
        goto fail;
    }
    left_before = &left.pokemon_storage.p_pc->boxes[left_box].entries[left_slot];
    right_before = &right.pokemon_storage.p_pc->boxes[right_box].entries[right_slot];
    left_species = species_of(left_before);
    right_species = species_of(right_before);
    if (!pokemon_present(left_before) || !pokemon_present(right_before)) {
        fprintf(stderr, "error=empty-trade-slot\n");
        goto fail;
    }
    temporary = *left_before;
    *left_before = *right_before;
    *right_before = temporary;

    error = pksav_gen3_save_save(output_left, &left);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-left:%s\n", pksav_strerror(error));
        goto fail;
    }
    error = pksav_gen3_save_save(output_right, &right);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-right:%s\n", pksav_strerror(error));
        goto fail;
    }
    printf("generation=3\n");
    printf("save_type=%s\n", save_type_name(left.save_type));
    printf("left_species_before=%u\n", left_species);
    printf("right_species_before=%u\n", right_species);
    printf("left_output=%s\n", output_left);
    printf("right_output=%s\n", output_right);
    pksav_gen3_free_save(&left);
    pksav_gen3_free_save(&right);
    return 0;

fail:
    pksav_gen3_free_save(&left);
    pksav_gen3_free_save(&right);
    unlink(output_left);
    unlink(output_right);
    return 1;
}

static int copy_gen3(const char* source_path, unsigned source_box,
                     unsigned source_slot, const char* destination_path,
                     unsigned destination_box, unsigned destination_slot,
                     const char* output_destination) {
    struct pksav_gen3_save source;
    struct pksav_gen3_save destination;
    enum pksav_error error;
    struct pksav_gen3_pc_pokemon* source_pokemon;
    struct pksav_gen3_pc_pokemon* destination_pokemon;
    uint16_t species;

    memset(&source, 0, sizeof(source));
    memset(&destination, 0, sizeof(destination));
    if (!copy_file(destination_path, output_destination)) return 1;

    error = pksav_gen3_load_save_from_file(source_path, &source);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-source:%s\n", pksav_strerror(error));
        goto fail;
    }
    error = pksav_gen3_load_save_from_file(output_destination, &destination);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=load-destination:%s\n", pksav_strerror(error));
        goto fail;
    }

    source_pokemon = &source.pokemon_storage.p_pc->boxes[source_box].entries[source_slot];
    destination_pokemon = &destination.pokemon_storage.p_pc->boxes[destination_box].entries[destination_slot];
    species = species_of(source_pokemon);
    if (!pokemon_present(source_pokemon)) {
        fprintf(stderr, "error=empty-source-slot\n");
        goto fail;
    }
    if (pokemon_present(destination_pokemon)) {
        fprintf(stderr, "error=destination-slot-not-empty\n");
        goto fail;
    }

    *destination_pokemon = *source_pokemon;
    error = pksav_gen3_save_save(output_destination, &destination);
    if (error != PKSAV_ERROR_NONE) {
        fprintf(stderr, "error=save-destination:%s\n", pksav_strerror(error));
        goto fail;
    }
    printf("generation=3\n");
    printf("copied_species=%u\n", species);
    printf("destination_output=%s\n", output_destination);
    pksav_gen3_free_save(&source);
    pksav_gen3_free_save(&destination);
    return 0;

fail:
    pksav_gen3_free_save(&source);
    pksav_gen3_free_save(&destination);
    unlink(output_destination);
    return 1;
}

int main(int argc, char** argv) {
    const char* save = NULL;
    const char* left = NULL;
    const char* right = NULL;
    const char* output_left = NULL;
    const char* output_right = NULL;
    const char* source = NULL;
    const char* destination = NULL;
    const char* output_destination = NULL;
    unsigned left_box = 0, left_slot = 0, right_box = 0, right_slot = 0;
    unsigned source_box = 0, source_slot = 0;
    unsigned destination_box = 0, destination_slot = 0;

    if (argc < 2) { usage(stderr); return 2; }
    if (!strcmp(argv[1], "gift-gen1")) {
        const char* record = NULL;
        const char* nickname = NULL;
        const char* family = NULL;
        unsigned national = 0;
        bool have_box = false, have_slot = false;
        if (argc % 2) return 2;
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--destination")) destination = value;
            else if (!strcmp(key, "--output-destination")) output_destination = value;
            else if (!strcmp(key, "--record")) record = value;
            else if (!strcmp(key, "--nickname")) nickname = value;
            else if (!strcmp(key, "--rom-family")) family = value;
            else if (!strcmp(key, "--national-species")) { if (!parse_index(value, 151, &national)) return 2; }
            else if (!strcmp(key, "--destination-box")) { if (!parse_index(value, 11, &destination_box)) return 2; have_box = true; }
            else if (!strcmp(key, "--destination-slot")) { if (!parse_index(value, 19, &destination_slot)) return 2; have_slot = true; }
            else return 2;
        }
        if (!destination || !output_destination || !record || !nickname || !family ||
            !have_box || !have_slot) { usage(stderr); return 2; }
        return gift_gen1(destination, destination_box, destination_slot, record, national,
                         nickname, family, output_destination);
    }
    if (!strcmp(argv[1], "inspect")) {
        for (int i = 2; i + 1 < argc; i += 2) {
            if (!strcmp(argv[i], "--save")) save = argv[i + 1];
        }
        if (!save) { usage(stderr); return 2; }
        return inspect_any_save(save);
    }
    if (!strcmp(argv[1], "swap-gen1") || !strcmp(argv[1], "swap-gen2")) {
        const bool gen1 = !strcmp(argv[1], "swap-gen1");
        const unsigned max_box = gen1 ? PKSAV_GEN1_NUM_POKEMON_BOXES - 1 :
                                        PKSAV_GEN2_NUM_POKEMON_BOXES - 1;
        const unsigned max_slot = gen1 ? PKSAV_GEN1_BOX_NUM_POKEMON - 1 :
                                         PKSAV_GEN2_BOX_NUM_POKEMON - 1;
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--left")) left = value;
            else if (!strcmp(key, "--right")) right = value;
            else if (!strcmp(key, "--output-left")) output_left = value;
            else if (!strcmp(key, "--output-right")) output_right = value;
            else if (!strcmp(key, "--left-box") && !parse_index(value, max_box, &left_box)) return 2;
            else if (!strcmp(key, "--left-slot") && !parse_index(value, max_slot, &left_slot)) return 2;
            else if (!strcmp(key, "--right-box") && !parse_index(value, max_box, &right_box)) return 2;
            else if (!strcmp(key, "--right-slot") && !parse_index(value, max_slot, &right_slot)) return 2;
        }
        if (!left || !right || !output_left || !output_right) { usage(stderr); return 2; }
        return gen1 ? swap_gen1(left, left_box, left_slot, right, right_box,
                                right_slot, output_left, output_right) :
                      swap_gen2(left, left_box, left_slot, right, right_box,
                                right_slot, output_left, output_right);
    }
    if (!strcmp(argv[1], "copy-gen1") || !strcmp(argv[1], "copy-gen2")) {
        const bool gen1 = !strcmp(argv[1], "copy-gen1");
        const unsigned max_box = gen1 ? PKSAV_GEN1_NUM_POKEMON_BOXES - 1 :
                                        PKSAV_GEN2_NUM_POKEMON_BOXES - 1;
        const unsigned max_slot = gen1 ? PKSAV_GEN1_BOX_NUM_POKEMON - 1 :
                                         PKSAV_GEN2_BOX_NUM_POKEMON - 1;
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--source")) source = value;
            else if (!strcmp(key, "--destination")) destination = value;
            else if (!strcmp(key, "--output-destination")) output_destination = value;
            else if (!strcmp(key, "--source-box") && !parse_index(value, max_box, &source_box)) return 2;
            else if (!strcmp(key, "--source-slot") && !parse_index(value, max_slot, &source_slot)) return 2;
            else if (!strcmp(key, "--destination-box") && !parse_index(value, max_box, &destination_box)) return 2;
            else if (!strcmp(key, "--destination-slot") && !parse_index(value, max_slot, &destination_slot)) return 2;
        }
        if (!source || !destination || !output_destination) { usage(stderr); return 2; }
        return gen1 ? copy_gen1(source, source_box, source_slot, destination,
                                destination_box, destination_slot, output_destination) :
                      copy_gen2(source, source_box, source_slot, destination,
                                destination_box, destination_slot, output_destination);
    }
    if (!strcmp(argv[1], "transfer-gen1-to-gen2")) {
        unsigned national_species = 0;
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--source")) source = value;
            else if (!strcmp(key, "--destination")) destination = value;
            else if (!strcmp(key, "--output-destination")) output_destination = value;
            else if (!strcmp(key, "--source-box") && !parse_index(value,
                     PKSAV_GEN1_NUM_POKEMON_BOXES - 1, &source_box)) return 2;
            else if (!strcmp(key, "--source-slot") && !parse_index(value,
                     PKSAV_GEN1_BOX_NUM_POKEMON - 1, &source_slot)) return 2;
            else if (!strcmp(key, "--destination-box") && !parse_index(value,
                     PKSAV_GEN2_NUM_POKEMON_BOXES - 1, &destination_box)) return 2;
            else if (!strcmp(key, "--destination-slot") && !parse_index(value,
                     PKSAV_GEN2_BOX_NUM_POKEMON - 1, &destination_slot)) return 2;
            else if (!strcmp(key, "--national-species") && !parse_index(value,
                     PKSAV_GEN1_POKEDEX_NUM_POKEMON, &national_species)) return 2;
        }
        if (!source || !destination || !output_destination || !national_species) {
            usage(stderr); return 2;
        }
        return transfer_gen1_to_gen2(source, source_box, source_slot,
                                     national_species, destination, destination_box,
                                     destination_slot, output_destination);
    }
    if (!strcmp(argv[1], "copy-gen2-to-gen3")) {
        unsigned national_species = 0;
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--source")) source = value;
            else if (!strcmp(key, "--destination")) destination = value;
            else if (!strcmp(key, "--output-destination")) output_destination = value;
            else if (!strcmp(key, "--source-box") && !parse_index(value,
                     PKSAV_GEN2_NUM_POKEMON_BOXES - 1, &source_box)) return 2;
            else if (!strcmp(key, "--source-slot") && !parse_index(value,
                     PKSAV_GEN2_BOX_NUM_POKEMON - 1, &source_slot)) return 2;
            else if (!strcmp(key, "--destination-box") && !parse_index(value,
                     PKSAV_GEN3_NUM_POKEMON_BOXES - 1, &destination_box)) return 2;
            else if (!strcmp(key, "--destination-slot") && !parse_index(value,
                     PKSAV_GEN3_BOX_NUM_POKEMON - 1, &destination_slot)) return 2;
            else if (!strcmp(key, "--national-species") && !parse_index(value,
                     251u, &national_species)) return 2;
        }
        if (!source || !destination || !output_destination || !national_species) {
            usage(stderr); return 2;
        }
        return copy_gen2_to_gen3(source, source_box, source_slot, national_species,
                                 destination, destination_box, destination_slot,
                                 output_destination);
    }
    if (!strcmp(argv[1], "evolve-gen1") || !strcmp(argv[1], "evolve-gen2") ||
        !strcmp(argv[1], "evolve-gen3")) {
        unsigned box = 0, slot = 0, evolved_species = 0;
        const char* nickname = NULL;
        const unsigned generation = (unsigned)(argv[1][10] - '0');
        const unsigned max_box = generation == 1 ? PKSAV_GEN1_NUM_POKEMON_BOXES - 1 :
                                 generation == 2 ? PKSAV_GEN2_NUM_POKEMON_BOXES - 1 :
                                                   PKSAV_GEN3_NUM_POKEMON_BOXES - 1;
        const unsigned max_slot = generation == 1 ? PKSAV_GEN1_BOX_NUM_POKEMON - 1 :
                                  generation == 2 ? PKSAV_GEN2_BOX_NUM_POKEMON - 1 :
                                                    PKSAV_GEN3_BOX_NUM_POKEMON - 1;
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--source")) source = value;
            else if (!strcmp(key, "--output")) output_destination = value;
            else if (!strcmp(key, "--box") && !parse_index(value, max_box, &box)) return 2;
            else if (!strcmp(key, "--slot") && !parse_index(value, max_slot, &slot)) return 2;
            else if (!strcmp(key, "--evolved-species") && !parse_index(value,
                     generation == 3 ? 386u : 255u, &evolved_species)) return 2;
            else if (!strcmp(key, "--nickname")) nickname = value;
        }
        if (!source || !output_destination || !evolved_species) { usage(stderr); return 2; }
        return generation == 1 ? evolve_gen1(source, box, slot, evolved_species, nickname, output_destination) :
               generation == 2 ? evolve_gen2(source, box, slot, evolved_species, nickname, output_destination) :
                                 evolve_gen3(source, box, slot, evolved_species, nickname, output_destination);
    }
    if (!strcmp(argv[1], "swap-gen3")) {
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--left")) left = value;
            else if (!strcmp(key, "--right")) right = value;
            else if (!strcmp(key, "--output-left")) output_left = value;
            else if (!strcmp(key, "--output-right")) output_right = value;
            else if (!strcmp(key, "--left-box") && !parse_index(value, 13, &left_box)) return 2;
            else if (!strcmp(key, "--left-slot") && !parse_index(value, 29, &left_slot)) return 2;
            else if (!strcmp(key, "--right-box") && !parse_index(value, 13, &right_box)) return 2;
            else if (!strcmp(key, "--right-slot") && !parse_index(value, 29, &right_slot)) return 2;
        }
        if (!left || !right || !output_left || !output_right) { usage(stderr); return 2; }
        return swap_gen3(left, left_box, left_slot, right, right_box, right_slot,
                         output_left, output_right);
    }
    if (!strcmp(argv[1], "copy-gen3")) {
        for (int i = 2; i + 1 < argc; i += 2) {
            const char* key = argv[i];
            const char* value = argv[i + 1];
            if (!strcmp(key, "--source")) source = value;
            else if (!strcmp(key, "--destination")) destination = value;
            else if (!strcmp(key, "--output-destination")) output_destination = value;
            else if (!strcmp(key, "--source-box") && !parse_index(value, 13, &source_box)) return 2;
            else if (!strcmp(key, "--source-slot") && !parse_index(value, 29, &source_slot)) return 2;
            else if (!strcmp(key, "--destination-box") && !parse_index(value, 13, &destination_box)) return 2;
            else if (!strcmp(key, "--destination-slot") && !parse_index(value, 29, &destination_slot)) return 2;
        }
        if (!source || !destination || !output_destination) { usage(stderr); return 2; }
        return copy_gen3(source, source_box, source_slot, destination,
                         destination_box, destination_slot, output_destination);
    }
    usage(stderr);
    return 2;
}
