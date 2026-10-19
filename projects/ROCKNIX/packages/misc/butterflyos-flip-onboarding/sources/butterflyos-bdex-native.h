/* SPDX-License-Identifier: GPL-2.0-or-later
 * Bdex uses the same validated pksav structures as Butterfly Link.
 * Included after its shared helpers; commands only write new isolated outputs.
 */
static void bdex_free_gen1(struct pksav_gen1_save* save) {
    if (save->p_internal) pksav_gen1_free_save(save);
}

static void bdex_free_gen2(struct pksav_gen2_save* save) {
    if (save->p_internal) pksav_gen2_free_save(save);
}

static void bdex_free_gen3(struct pksav_gen3_save* save) {
    if (save->p_internal) pksav_gen3_free_save(save);
}

static void bdex_hex(const void* data, size_t size) {
    const uint8_t* bytes = data;
    for (size_t i = 0; i < size; ++i) printf("%02x", bytes[i]);
}

static void bdex_record(const char* location, int box, unsigned slot,
                        const struct pksav_gen1_pc_pokemon* pokemon,
                        const uint8_t* ot, size_t ot_size,
                        const uint8_t* nickname, size_t nickname_size) {
    char trainer[64];
    decoded_gen1_text(ot, ot_size - 1, trainer, sizeof(trainer));
    printf("bdex_record\t%s\t%d\t%u\t", location, box, slot);
    bdex_hex(pokemon, sizeof(*pokemon)); printf("\t");
    bdex_hex(ot, ot_size); printf("\t");
    bdex_hex(nickname, nickname_size);
    printf("\t%s\n", trainer);
}

static int bdex_inspect_gen1(const char* path) {
    struct pksav_gen1_save save;
    memset(&save, 0, sizeof(save));
    if (pksav_gen1_load_save_from_file(path, &save) != PKSAV_ERROR_NONE) return 1;
    if (save.save_type != PKSAV_GEN1_SAVE_TYPE_RED_BLUE &&
        save.save_type != PKSAV_GEN1_SAVE_TYPE_YELLOW) {
        bdex_free_gen1(&save); return 1;
    }
    if (inspect_gen1_save(path)) { bdex_free_gen1(&save); return 1; }
    const struct pksav_gen1_pokemon_party* party = save.pokemon_storage.p_party;
    for (unsigned slot = 0; slot < party->count && slot < PKSAV_GEN1_PARTY_NUM_POKEMON; ++slot) {
        struct pksav_gen1_pc_pokemon boxed = party->party[slot].pc_data;
        /* The game maintains the active level in party_data, not pc_data. */
        boxed.level = party->party[slot].party_data.level;
        bdex_record("party", -1, slot, &boxed,
                    party->otnames[slot], sizeof(party->otnames[slot]),
                    party->nicknames[slot], sizeof(party->nicknames[slot]));
    }
    for (unsigned box = 0; box < PKSAV_GEN1_NUM_POKEMON_BOXES; ++box) {
        const struct pksav_gen1_pokemon_box* current = gen1_box_for_read(&save, box);
        if (!current) continue;
        for (unsigned slot = 0; slot < current->count && slot < PKSAV_GEN1_BOX_NUM_POKEMON; ++slot)
            if (gen1_box_slot_present(current, slot))
                bdex_record("box", (int)box, slot, &current->entries[slot],
                            current->otnames[slot], sizeof(current->otnames[slot]),
                            current->nicknames[slot], sizeof(current->nicknames[slot]));
    }
    bdex_free_gen1(&save);
    return 0;
}

static int bdex_export_gen1(const char* source_path, bool party_source,
                            unsigned source_box_num, unsigned source_slot,
                            const char* destination_path, unsigned box_num,
                            unsigned slot, unsigned national, const char* output) {
    struct pksav_gen1_save source, destination;
    struct stat existing;
    enum pksav_error error;
    memset(&source, 0, sizeof(source)); memset(&destination, 0, sizeof(destination));
    /* Refuse all existing outputs, including aliases to either input. */
    if (!national || national > 151 || box_num >= PKSAV_GEN1_NUM_POKEMON_BOXES ||
        lstat(output, &existing) == 0 || errno != ENOENT) return 1;
    if (pksav_gen1_load_save_from_file(source_path, &source) != PKSAV_ERROR_NONE) return 1;
    if (!copy_file(destination_path, output)) { bdex_free_gen1(&source); return 1; }
    if ((error = pksav_gen1_load_save_from_file(output, &destination)) != PKSAV_ERROR_NONE) goto fail;
    if ((source.save_type != PKSAV_GEN1_SAVE_TYPE_RED_BLUE && source.save_type != PKSAV_GEN1_SAVE_TYPE_YELLOW) ||
        (destination.save_type != PKSAV_GEN1_SAVE_TYPE_RED_BLUE && destination.save_type != PKSAV_GEN1_SAVE_TYPE_YELLOW)) goto fail;
    const struct pksav_gen1_pc_pokemon* pokemon;
    struct pksav_gen1_pc_pokemon boxed_party;
    const uint8_t *ot, *nickname;
    if (party_source) {
        const struct pksav_gen1_pokemon_party* party = source.pokemon_storage.p_party;
        if (source_slot >= party->count || source_slot >= PKSAV_GEN1_PARTY_NUM_POKEMON) goto fail;
        boxed_party = party->party[source_slot].pc_data;
        boxed_party.level = party->party[source_slot].party_data.level;
        pokemon = &boxed_party;
        ot = party->otnames[source_slot]; nickname = party->nicknames[source_slot];
    } else {
        if (source_box_num >= PKSAV_GEN1_NUM_POKEMON_BOXES) goto fail;
        const struct pksav_gen1_pokemon_box* box = gen1_box_for_read(&source, source_box_num);
        if (!box || !gen1_box_slot_present(box, source_slot)) goto fail;
        pokemon = &box->entries[source_slot]; ot = box->otnames[source_slot]; nickname = box->nicknames[source_slot];
    }
    if (!pokemon->species || pokemon->species > 190) goto fail;
    unsigned current = *destination.pokemon_storage.p_current_box_num & PKSAV_GEN1_CURRENT_POKEMON_BOX_NUM_MASK;
    if (current >= PKSAV_GEN1_NUM_POKEMON_BOXES) goto fail;
    /* Match the game's first-box initialization without losing its active box. */
    if (!(*destination.pokemon_storage.p_current_box_num & 0x80)) {
        for (unsigned i = 0; i < PKSAV_GEN1_NUM_POKEMON_BOXES; ++i) {
            destination.pokemon_storage.pp_boxes[i]->count = 0;
            destination.pokemon_storage.pp_boxes[i]->species[0] = 0xff;
        }
        *destination.pokemon_storage.p_current_box_num |= 0x80;
    }
    if ((error = pksav_gen1_pokemon_storage_set_current_box(&destination.pokemon_storage, (uint8_t)box_num)) != PKSAV_ERROR_NONE) goto fail;
    struct pksav_gen1_pokemon_box* box = destination.pokemon_storage.p_current_box;
    if (box->count >= PKSAV_GEN1_BOX_NUM_POKEMON || slot != box->count) goto fail;
    box->entries[slot] = *pokemon;
    box->species[slot] = pokemon->species;
    memcpy(box->otnames[slot], ot, sizeof(box->otnames[slot]));
    memcpy(box->nicknames[slot], nickname, sizeof(box->nicknames[slot]));
    ++box->count; box->species[box->count] = 0xff;
    *destination.pokemon_storage.pp_boxes[box_num] = *box;
    /* Same bank and per-box checksum repair used by the qualified gift writer. */
    for (unsigned half = 0; half < 2; ++half) {
        uint8_t* bank = (uint8_t*)destination.pokemon_storage.pp_boxes[half * 6];
        size_t size = sizeof(struct pksav_gen1_pokemon_box);
        unsigned sum = 0;
        for (size_t i = 0; i < size * 6; ++i) sum += bank[i];
        bank[size * 6] = (uint8_t)~sum;
        for (unsigned i = 0; i < 6; ++i) {
            sum = 0;
            for (size_t j = 0; j < size; ++j) sum += bank[i * size + j];
            bank[size * 6 + 1 + i] = (uint8_t)~sum;
        }
    }
    if ((error = pksav_set_pokedex_bit(destination.pokedex_lists.p_seen, national, true)) != PKSAV_ERROR_NONE ||
        (error = pksav_set_pokedex_bit(destination.pokedex_lists.p_owned, national, true)) != PKSAV_ERROR_NONE ||
        (error = pksav_gen1_save_save(output, &destination)) != PKSAV_ERROR_NONE) goto fail;
    bdex_free_gen1(&source); bdex_free_gen1(&destination);
    return 0;
fail:
    fprintf(stderr, "error=bdex-invalid-source-or-destination\n");
    bdex_free_gen1(&source); bdex_free_gen1(&destination);
    unlink(output);
    return 1;
}

static void bdex_record_gen2(const char* location, int box, unsigned slot,
                             const struct pksav_gen2_pc_pokemon* pokemon,
                             const uint8_t* ot, const uint8_t* nickname, bool egg) {
    char trainer[64];
    decoded_gen2_text(ot, 10, trainer, sizeof(trainer));
    printf("bdex_record\t%s\t%d\t%u\t", location, box, slot);
    bdex_hex(pokemon, sizeof(*pokemon)); printf("\t");
    bdex_hex(ot, 11); printf("\t"); bdex_hex(nickname, 11);
    printf("\t%s\t%u\n", trainer, egg ? 1u : 0u);
}

static int bdex_inspect_gen2(const char* path) {
    struct pksav_gen2_save save;
    memset(&save, 0, sizeof(save));
    if (pksav_gen2_load_save_from_file(path, &save) != PKSAV_ERROR_NONE) return 1;
    if ((save.save_type != PKSAV_GEN2_SAVE_TYPE_GS && save.save_type != PKSAV_GEN2_SAVE_TYPE_CRYSTAL) ||
        *save.pokemon_storage.p_current_box_num >= PKSAV_GEN2_NUM_POKEMON_BOXES || inspect_gen2_save(path)) {
        bdex_free_gen2(&save); return 1;
    }
    const struct pksav_gen2_pokemon_party* party = save.pokemon_storage.p_party;
    if (party->count > PKSAV_GEN2_PARTY_NUM_POKEMON) goto invalid;
    for (unsigned slot = 0; slot < party->count; ++slot) {
        const struct pksav_gen2_pc_pokemon* pokemon = &party->party[slot].pc_data;
        if (!pokemon->species || pokemon->species > 251 ||
            (party->species[slot] != pokemon->species && party->species[slot] != 0xfd)) goto invalid;
        bdex_record_gen2("party", -1, slot, pokemon, party->otnames[slot],
                         party->nicknames[slot], party->species[slot] == 0xfd);
    }
    for (unsigned box = 0; box < PKSAV_GEN2_NUM_POKEMON_BOXES; ++box) {
        const struct pksav_gen2_pokemon_box* current = gen2_box_for_read(&save, box);
        if (!current || current->count > PKSAV_GEN2_BOX_NUM_POKEMON) goto invalid;
        for (unsigned slot = 0; slot < current->count; ++slot) {
            const struct pksav_gen2_pc_pokemon* pokemon = &current->entries[slot];
            if (!pokemon->species || pokemon->species > 251 ||
                (current->species[slot] != pokemon->species && current->species[slot] != 0xfd)) goto invalid;
            bdex_record_gen2("box", (int)box, slot, pokemon, current->otnames[slot],
                             current->nicknames[slot], current->species[slot] == 0xfd);
        }
    }
    bdex_free_gen2(&save); return 0;
invalid:
    fprintf(stderr, "error=bdex-invalid-gen2-storage\n");
    bdex_free_gen2(&save); return 1;
}

/* Emulator RTC trailers belong to the destination and must survive export. */
static bool bdex_preserve_gen2_tail(const char* input, const char* output) {
    FILE* source = fopen(input, "rb");
    if (!source) return false;
    if (fseek(source, 0x8000, SEEK_SET)) { fclose(source); return false; }
    FILE* target = fopen(output, "ab");
    if (!target) { fclose(source); return false; }
    uint8_t data[4096];
    size_t count;
    bool ok = true;
    while ((count = fread(data, 1, sizeof(data), source))) {
        if (fwrite(data, 1, count, target) != count) { ok = false; break; }
    }
    if (ferror(source)) ok = false;
    if (fclose(source)) ok = false;
    if (fclose(target)) ok = false;
    return ok;
}

static int bdex_export_gen2(const char* source_path, bool party_source,
                            unsigned source_box_num, unsigned source_slot,
                            const char* destination_path, unsigned box_num,
                            unsigned slot, unsigned national, const char* output) {
    struct pksav_gen2_save source, destination;
    struct stat existing;
    memset(&source, 0, sizeof(source)); memset(&destination, 0, sizeof(destination));
    if (!national || national > 251 || box_num >= PKSAV_GEN2_NUM_POKEMON_BOXES ||
        lstat(output, &existing) == 0 || errno != ENOENT) return 1;
    if (pksav_gen2_load_save_from_file(source_path, &source) != PKSAV_ERROR_NONE) return 1;
    if (!copy_file(destination_path, output)) { bdex_free_gen2(&source); return 1; }
    if (pksav_gen2_load_save_from_file(output, &destination) != PKSAV_ERROR_NONE) goto fail2;
    if ((source.save_type != PKSAV_GEN2_SAVE_TYPE_GS && source.save_type != PKSAV_GEN2_SAVE_TYPE_CRYSTAL) ||
        (destination.save_type != PKSAV_GEN2_SAVE_TYPE_GS && destination.save_type != PKSAV_GEN2_SAVE_TYPE_CRYSTAL) ||
        *source.pokemon_storage.p_current_box_num >= 14 || *destination.pokemon_storage.p_current_box_num >= 14) goto fail2;
    const struct pksav_gen2_pc_pokemon* pokemon;
    const uint8_t *ot, *nickname;
    bool egg;
    if (party_source) {
        const struct pksav_gen2_pokemon_party* party = source.pokemon_storage.p_party;
        if (party->count > 6 || source_slot >= party->count) goto fail2;
        pokemon = &party->party[source_slot].pc_data;
        ot = party->otnames[source_slot]; nickname = party->nicknames[source_slot];
        egg = party->species[source_slot] == 0xfd;
        if (!egg && party->species[source_slot] != pokemon->species) goto fail2;
    } else {
        if (source_box_num >= PKSAV_GEN2_NUM_POKEMON_BOXES) goto fail2;
        const struct pksav_gen2_pokemon_box* box = gen2_box_for_read(&source, source_box_num);
        if (!box || box->count > 20 || source_slot >= box->count) goto fail2;
        pokemon = &box->entries[source_slot]; ot = box->otnames[source_slot]; nickname = box->nicknames[source_slot];
        egg = box->species[source_slot] == 0xfd;
        if (!egg && box->species[source_slot] != pokemon->species) goto fail2;
    }
    if (pokemon->species != national) goto fail2;
    if (pksav_gen2_pokemon_storage_set_current_box(&destination.pokemon_storage, (uint8_t)box_num) != PKSAV_ERROR_NONE) goto fail2;
    struct pksav_gen2_pokemon_box* box = destination.pokemon_storage.p_current_box;
    if (box->count >= PKSAV_GEN2_BOX_NUM_POKEMON || slot != box->count) goto fail2;
    box->entries[slot] = *pokemon;
    box->species[slot] = egg ? 0xfd : pokemon->species;
    memcpy(box->otnames[slot], ot, sizeof(box->otnames[slot]));
    memcpy(box->nicknames[slot], nickname, sizeof(box->nicknames[slot]));
    ++box->count; box->species[box->count] = 0xff;
    if (!egg && (pksav_set_pokedex_bit(destination.pokedex_lists.p_seen, national, true) != PKSAV_ERROR_NONE ||
                 pksav_set_pokedex_bit(destination.pokedex_lists.p_owned, national, true) != PKSAV_ERROR_NONE)) goto fail2;
    if (save_gen2_with_synced_box(output, &destination) != PKSAV_ERROR_NONE ||
        !bdex_preserve_gen2_tail(destination_path, output)) goto fail2;
    bdex_free_gen2(&source); bdex_free_gen2(&destination); return 0;
fail2:
    fprintf(stderr, "error=bdex-invalid-gen2-source-or-destination\n");
    bdex_free_gen2(&source); bdex_free_gen2(&destination);
    unlink(output); return 1;
}

/* Same Time Capsule conversion used by Blink, with archived party support. */
static int bdex_export_gen1_to_gen2(const char* source_path, bool party_source,
                                   unsigned source_box_num, unsigned source_slot,
                                   const char* destination_path, unsigned box_num,
                                   unsigned slot, unsigned national, const char* output) {
    struct pksav_gen1_save source;
    struct pksav_gen2_save destination;
    struct stat existing;
    memset(&source, 0, sizeof(source)); memset(&destination, 0, sizeof(destination));
    if (!national || national > 151 || box_num >= 14 ||
        lstat(output, &existing) == 0 || errno != ENOENT) return 1;
    if (pksav_gen1_load_save_from_file(source_path, &source) != PKSAV_ERROR_NONE) return 1;
    if (!copy_file(destination_path, output)) { bdex_free_gen1(&source); return 1; }
    if (pksav_gen2_load_save_from_file(output, &destination) != PKSAV_ERROR_NONE) goto fail_forward;
    if ((source.save_type != PKSAV_GEN1_SAVE_TYPE_RED_BLUE && source.save_type != PKSAV_GEN1_SAVE_TYPE_YELLOW) ||
        (destination.save_type != PKSAV_GEN2_SAVE_TYPE_GS && destination.save_type != PKSAV_GEN2_SAVE_TYPE_CRYSTAL) ||
        *destination.pokemon_storage.p_current_box_num >= 14) goto fail_forward;
    const struct pksav_gen1_pc_pokemon* pokemon;
    struct pksav_gen1_pc_pokemon boxed_party;
    const uint8_t *ot, *nickname;
    if (party_source) {
        const struct pksav_gen1_pokemon_party* party = source.pokemon_storage.p_party;
        if (party->count > 6 || source_slot >= party->count) goto fail_forward;
        boxed_party = party->party[source_slot].pc_data;
        boxed_party.level = party->party[source_slot].party_data.level;
        pokemon = &boxed_party; ot = party->otnames[source_slot]; nickname = party->nicknames[source_slot];
    } else {
        if (source_box_num >= 12) goto fail_forward;
        const struct pksav_gen1_pokemon_box* box = gen1_box_for_read(&source, source_box_num);
        if (!box || box->count > 20 || !gen1_box_slot_present(box, source_slot)) goto fail_forward;
        pokemon = &box->entries[source_slot]; ot = box->otnames[source_slot]; nickname = box->nicknames[source_slot];
    }
    if (!pokemon->species || pokemon->species > 190 ||
        pksav_gen2_pokemon_storage_set_current_box(&destination.pokemon_storage, (uint8_t)box_num) != PKSAV_ERROR_NONE) goto fail_forward;
    struct pksav_gen2_pokemon_box* box = destination.pokemon_storage.p_current_box;
    if (box->count >= 20 || slot != box->count) goto fail_forward;
    convert_gen1_pc_to_gen2(pokemon, national, &box->entries[slot]);
    char text[PKSAV_GEN1_POKEMON_NICKNAME_LENGTH + 1];
    if (pksav_gen1_import_text(ot, text, PKSAV_GEN1_POKEMON_OTNAME_LENGTH) != PKSAV_ERROR_NONE ||
        export_gb_name(text, box->otnames[slot], sizeof(box->otnames[slot]), 2) != PKSAV_ERROR_NONE ||
        pksav_gen1_import_text(nickname, text, PKSAV_GEN1_POKEMON_NICKNAME_LENGTH) != PKSAV_ERROR_NONE ||
        export_gb_name(text, box->nicknames[slot], sizeof(box->nicknames[slot]), 2) != PKSAV_ERROR_NONE) goto fail_forward;
    box->species[slot] = (uint8_t)national;
    ++box->count; box->species[box->count] = 0xff;
    if (pksav_set_pokedex_bit(destination.pokedex_lists.p_seen, national, true) != PKSAV_ERROR_NONE ||
        pksav_set_pokedex_bit(destination.pokedex_lists.p_owned, national, true) != PKSAV_ERROR_NONE ||
        save_gen2_with_synced_box(output, &destination) != PKSAV_ERROR_NONE ||
        !bdex_preserve_gen2_tail(destination_path, output)) goto fail_forward;
    bdex_free_gen1(&source); bdex_free_gen2(&destination); return 0;
fail_forward:
    fprintf(stderr, "error=bdex-invalid-gen1-to-gen2-copy\n");
    bdex_free_gen1(&source); bdex_free_gen2(&destination);
    unlink(output); return 1;
}

static bool bdex_gen3_valid(const struct pksav_gen3_pc_pokemon* pokemon) {
    const uint8_t* data = (const uint8_t*)&pokemon->blocks;
    unsigned sum = 0;
    for (size_t i = 0; i < sizeof(pokemon->blocks); i += 2)
        sum += data[i] | ((unsigned)data[i + 1] << 8);
    return (uint16_t)sum == pksav_littleendian16(pokemon->checksum) &&
           !(pksav_littleendian16(pokemon->language) & 0x0100);
}

static bool bdex_record_gen3(const char* location, int box, unsigned slot,
                             const struct pksav_gen3_pc_pokemon* pokemon) {
    if (!bdex_gen3_valid(pokemon)) return false;
    char nickname[64], trainer[64];
    decoded_text(pokemon->nickname, 10, nickname, sizeof(nickname));
    decoded_text(pokemon->otname, 7, trainer, sizeof(trainer));
    struct pksav_gen3_pc_pokemon canonical = *pokemon;
    canonical.checksum = 0; /* Derived, not identity; all native attributes remain. */
    printf("bdex_record\t%s\t%d\t%u\t", location, box, slot);
    bdex_hex(&canonical, sizeof(canonical));
    printf("\t%s\t%s\t%s\n", trainer, nickname, nature_name(pksav_littleendian32(pokemon->personality)));
    return true;
}

static int bdex_inspect_gen3(const char* path) {
    struct pksav_gen3_save save;
    memset(&save, 0, sizeof(save));
    if (pksav_gen3_load_save_from_file(path, &save) != PKSAV_ERROR_NONE) return 1;
    if (save.save_type < PKSAV_GEN3_SAVE_TYPE_RS || save.save_type > PKSAV_GEN3_SAVE_TYPE_FRLG ||
        inspect_save(path) || save.pokemon_storage.p_party->count > 6) goto invalid_gen3;
    for (unsigned slot = 0; slot < save.pokemon_storage.p_party->count; ++slot) {
        const struct pksav_gen3_pc_pokemon* pokemon = &save.pokemon_storage.p_party->party[slot].pc_data;
        if (!pokemon_present(pokemon) || !bdex_record_gen3("party", -1, slot, pokemon)) goto invalid_gen3;
    }
    for (unsigned box = 0; box < 14; ++box)
        for (unsigned slot = 0; slot < 30; ++slot) {
            const struct pksav_gen3_pc_pokemon* pokemon = &save.pokemon_storage.p_pc->boxes[box].entries[slot];
            if (pokemon_present(pokemon) && !bdex_record_gen3("box", box, slot, pokemon)) goto invalid_gen3;
        }
    bdex_free_gen3(&save); return 0;
invalid_gen3:
    fprintf(stderr, "error=bdex-invalid-gen3-record-or-save\n");
    bdex_free_gen3(&save); return 1;
}

static int bdex_export_gen3(const char* source_path, bool party_source,
                            unsigned source_box_num, unsigned source_slot,
                            const char* destination_path, unsigned box_num,
                            unsigned slot, unsigned national, const char* output,
                            bool migrate, uint32_t personality) {
    struct pksav_gen3_save source, destination;
    struct pksav_gen2_save old;
    struct pksav_gen3_pc_pokemon pokemon;
    struct stat existing;
    memset(&source, 0, sizeof(source)); memset(&destination, 0, sizeof(destination));
    memset(&old, 0, sizeof(old));
    if (!national || national > (migrate ? 251u : 386u) || box_num >= 14 || slot >= 30 ||
        lstat(output, &existing) == 0 || errno != ENOENT) return 1;
    if (!copy_file(destination_path, output)) return 1;
    if (pksav_gen3_load_save_from_file(output, &destination) != PKSAV_ERROR_NONE) goto fail_gen3;
    if (migrate) {
        if (pksav_gen2_load_save_from_file(source_path, &old) != PKSAV_ERROR_NONE ||
            *old.pokemon_storage.p_current_box_num >= 14) goto fail_gen3;
        const struct pksav_gen2_pc_pokemon* previous;
        const uint8_t *ot, *nickname;
        if (party_source) {
            const struct pksav_gen2_pokemon_party* party = old.pokemon_storage.p_party;
            if (party->count > 6 || source_slot >= party->count || party->species[source_slot] == 0xfd) goto fail_gen3;
            previous = &party->party[source_slot].pc_data;
            ot = party->otnames[source_slot]; nickname = party->nicknames[source_slot];
        } else {
            if (source_box_num >= 14) goto fail_gen3;
            const struct pksav_gen2_pokemon_box* box = gen2_box_for_read(&old, source_box_num);
            if (!box || box->count > 20 || !gen2_box_slot_present(box, source_slot) || box->species[source_slot] == 0xfd) goto fail_gen3;
            previous = &box->entries[source_slot]; ot = box->otnames[source_slot]; nickname = box->nicknames[source_slot];
        }
        if (previous->species != national) goto fail_gen3;
        unsigned cleared_item = 0, reduced_evs = 0, cleared_moves = 0;
        if (convert_gen2_pc_to_gen3(previous, national, &pokemon, &cleared_item, &reduced_evs, &cleared_moves) != PKSAV_ERROR_NONE) goto fail_gen3;
        pokemon.personality = pksav_littleendian32(personality);
        pokemon.language = pksav_littleendian16(0x0202); /* English, has species. */
        pokemon.blocks.misc.pokerus = previous->pokerus;
        if (national == 151) pokemon.blocks.misc.ribbons_obedience = pksav_littleendian32(PKSAV_GEN3_POKEMON_OBEDIENCE_MASK);
        if (export_gen2_text_to_gen3(ot, 10, pokemon.otname, 7) != PKSAV_ERROR_NONE ||
            export_gen2_text_to_gen3(nickname, 10, pokemon.nickname, 10) != PKSAV_ERROR_NONE) goto fail_gen3;
    } else {
        if (pksav_gen3_load_save_from_file(source_path, &source) != PKSAV_ERROR_NONE) goto fail_gen3;
        if (party_source) {
            if (source.pokemon_storage.p_party->count > 6 || source_slot >= source.pokemon_storage.p_party->count) goto fail_gen3;
            pokemon = source.pokemon_storage.p_party->party[source_slot].pc_data;
        } else {
            if (source_box_num >= 14 || source_slot >= 30) goto fail_gen3;
            pokemon = source.pokemon_storage.p_pc->boxes[source_box_num].entries[source_slot];
        }
        if (!pokemon_present(&pokemon) || !bdex_gen3_valid(&pokemon)) goto fail_gen3;
    }
    struct pksav_gen3_pc_pokemon* target = &destination.pokemon_storage.p_pc->boxes[box_num].entries[slot];
    if (pokemon_present(target)) goto fail_gen3;
    *target = pokemon;
    if (!(pksav_littleendian32(pokemon.blocks.misc.iv_egg_ability) & PKSAV_GEN3_POKEMON_EGG_MASK)) {
        if (pksav_gen3_pokedex_set_has_seen(&destination.pokedex, national, true) != PKSAV_ERROR_NONE ||
            pksav_set_pokedex_bit(destination.pokedex.p_owned, national, true) != PKSAV_ERROR_NONE) goto fail_gen3;
    }
    if (pksav_gen3_save_save(output, &destination) != PKSAV_ERROR_NONE) goto fail_gen3;
    bdex_free_gen3(&source); bdex_free_gen3(&destination); bdex_free_gen2(&old); return 0;
fail_gen3:
    fprintf(stderr, "error=bdex-invalid-gen3-source-or-destination-or-unhatched-egg\n");
    bdex_free_gen3(&source); bdex_free_gen3(&destination); bdex_free_gen2(&old);
    unlink(output); return 1;
}
