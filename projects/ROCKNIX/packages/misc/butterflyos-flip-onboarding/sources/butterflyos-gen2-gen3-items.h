/* SPDX-License-Identifier: GPL-2.0-or-later
 * Verified retail Gen II -> Gen III item IDs. Unknown, unused, key, mail,
 * HM, and Gen-II-only items have no entry and are cleared on the copy.
 * TMs match by taught move, never by TM number. Berry aliases are listed
 * in documentation/BUTTERFLY_LINK.md. No runtime ROM name guessing.
 * References: pret/pokecrystal constants/item_constants.asm;
 * pret/{pokeemerald,pokefirered,pokeruby} include/constants/items.h.
 */
#ifndef BUTTERFLYOS_GEN2_GEN3_ITEMS_H
#define BUTTERFLYOS_GEN2_GEN3_ITEMS_H
#include <stdint.h>

static uint16_t gen2_held_item_to_gen3(uint8_t item, unsigned* cleared) {
    static const uint16_t equivalents[256] = {
        [0x01] = 1, /* MASTER_BALL -> MASTER_BALL */
        [0x02] = 2, /* ULTRA_BALL -> ULTRA_BALL */
        [0x03] = 179, /* BRIGHTPOWDER -> BRIGHT_POWDER */
        [0x04] = 3, /* GREAT_BALL -> GREAT_BALL */
        [0x05] = 4, /* POKE_BALL -> POKE_BALL */
        [0x08] = 94, /* MOON_STONE -> MOON_STONE */
        [0x09] = 14, /* ANTIDOTE -> ANTIDOTE */
        [0x0A] = 15, /* BURN_HEAL -> BURN_HEAL */
        [0x0B] = 16, /* ICE_HEAL -> ICE_HEAL */
        [0x0C] = 17, /* AWAKENING -> AWAKENING */
        [0x0D] = 18, /* PARLYZ_HEAL -> PARALYZE_HEAL */
        [0x0E] = 19, /* FULL_RESTORE -> FULL_RESTORE */
        [0x0F] = 20, /* MAX_POTION -> MAX_POTION */
        [0x10] = 21, /* HYPER_POTION -> HYPER_POTION */
        [0x11] = 22, /* SUPER_POTION -> SUPER_POTION */
        [0x12] = 13, /* POTION -> POTION */
        [0x13] = 85, /* ESCAPE_ROPE -> ESCAPE_ROPE */
        [0x14] = 86, /* REPEL -> REPEL */
        [0x15] = 37, /* MAX_ELIXER -> MAX_ELIXIR */
        [0x16] = 95, /* FIRE_STONE -> FIRE_STONE */
        [0x17] = 96, /* THUNDERSTONE -> THUNDER_STONE */
        [0x18] = 97, /* WATER_STONE -> WATER_STONE */
        [0x1A] = 63, /* HP_UP -> HP_UP */
        [0x1B] = 64, /* PROTEIN -> PROTEIN */
        [0x1C] = 65, /* IRON -> IRON */
        [0x1D] = 66, /* CARBOS -> CARBOS */
        [0x1E] = 222, /* LUCKY_PUNCH -> LUCKY_PUNCH */
        [0x1F] = 67, /* CALCIUM -> CALCIUM */
        [0x20] = 68, /* RARE_CANDY -> RARE_CANDY */
        [0x21] = 78, /* X_ACCURACY -> X_ACCURACY */
        [0x22] = 98, /* LEAF_STONE -> LEAF_STONE */
        [0x23] = 223, /* METAL_POWDER -> METAL_POWDER */
        [0x24] = 110, /* NUGGET -> NUGGET */
        [0x25] = 80, /* POKE_DOLL -> POKE_DOLL */
        [0x26] = 23, /* FULL_HEAL -> FULL_HEAL */
        [0x27] = 24, /* REVIVE -> REVIVE */
        [0x28] = 25, /* MAX_REVIVE -> MAX_REVIVE */
        [0x29] = 73, /* GUARD_SPEC -> GUARD_SPEC */
        [0x2A] = 83, /* SUPER_REPEL -> SUPER_REPEL */
        [0x2B] = 84, /* MAX_REPEL -> MAX_REPEL */
        [0x2C] = 74, /* DIRE_HIT -> DIRE_HIT */
        [0x2E] = 26, /* FRESH_WATER -> FRESH_WATER */
        [0x2F] = 27, /* SODA_POP -> SODA_POP */
        [0x30] = 28, /* LEMONADE -> LEMONADE */
        [0x31] = 75, /* X_ATTACK -> X_ATTACK */
        [0x33] = 76, /* X_DEFEND -> X_DEFEND */
        [0x34] = 77, /* X_SPEED -> X_SPEED */
        [0x35] = 79, /* X_SPECIAL -> X_SPECIAL */
        [0x39] = 182, /* EXP_SHARE -> EXP_SHARE */
        [0x3E] = 69, /* PP_UP -> PP_UP */
        [0x3F] = 34, /* ETHER -> ETHER */
        [0x40] = 35, /* MAX_ETHER -> MAX_ETHER */
        [0x41] = 36, /* ELIXER -> ELIXIR */
        [0x48] = 29, /* MOOMOO_MILK -> MOOMOO_MILK */
        [0x49] = 183, /* QUICK_CLAW -> QUICK_CLAW */
        [0x4A] = 135, /* PSNCUREBERRY -> PECHA_BERRY */
        [0x4C] = 203, /* SOFT_SAND -> SOFT_SAND */
        [0x4D] = 210, /* SHARP_BEAK -> SHARP_BEAK */
        [0x4E] = 133, /* PRZCUREBERRY -> CHERI_BERRY */
        [0x4F] = 136, /* BURNT_BERRY -> RAWST_BERRY */
        [0x50] = 137, /* ICE_BERRY -> ASPEAR_BERRY */
        [0x51] = 211, /* POISON_BARB -> POISON_BARB */
        [0x52] = 187, /* KINGS_ROCK -> KINGS_ROCK */
        [0x53] = 140, /* BITTER_BERRY -> PERSIM_BERRY */
        [0x54] = 134, /* MINT_BERRY -> CHESTO_BERRY */
        [0x56] = 103, /* TINYMUSHROOM -> TINY_MUSHROOM */
        [0x57] = 104, /* BIG_MUSHROOM -> BIG_MUSHROOM */
        [0x58] = 188, /* SILVERPOWDER -> SILVER_POWDER */
        [0x5B] = 189, /* AMULET_COIN -> AMULET_COIN */
        [0x5E] = 190, /* CLEANSE_TAG -> CLEANSE_TAG */
        [0x5F] = 209, /* MYSTIC_WATER -> MYSTIC_WATER */
        [0x60] = 214, /* TWISTEDSPOON -> TWISTED_SPOON */
        [0x62] = 207, /* BLACKBELT_I -> BLACK_BELT */
        [0x66] = 206, /* BLACKGLASSES -> BLACK_GLASSES */
        [0x69] = 225, /* STICK -> STICK */
        [0x6A] = 194, /* SMOKE_BALL -> SMOKE_BALL */
        [0x6B] = 212, /* NEVERMELTICE -> NEVER_MELT_ICE */
        [0x6C] = 208, /* MAGNET -> MAGNET */
        [0x6D] = 141, /* MIRACLEBERRY -> LUM_BERRY */
        [0x6E] = 106, /* PEARL -> PEARL */
        [0x6F] = 107, /* BIG_PEARL -> BIG_PEARL */
        [0x70] = 195, /* EVERSTONE -> EVERSTONE */
        [0x71] = 213, /* SPELL_TAG -> SPELL_TAG */
        [0x75] = 205, /* MIRACLE_SEED -> MIRACLE_SEED */
        [0x76] = 224, /* THICK_CLUB -> THICK_CLUB */
        [0x77] = 196, /* FOCUS_BAND -> FOCUS_BAND */
        [0x79] = 30, /* ENERGYPOWDER -> ENERGY_POWDER */
        [0x7A] = 31, /* ENERGY_ROOT -> ENERGY_ROOT */
        [0x7B] = 32, /* HEAL_POWDER -> HEAL_POWDER */
        [0x7C] = 33, /* REVIVAL_HERB -> REVIVAL_HERB */
        [0x7D] = 204, /* HARD_STONE -> HARD_STONE */
        [0x7E] = 197, /* LUCKY_EGG -> LUCKY_EGG */
        [0x83] = 108, /* STARDUST -> STARDUST */
        [0x84] = 109, /* STAR_PIECE -> STAR_PIECE */
        [0x8A] = 215, /* CHARCOAL -> CHARCOAL */
        [0x8B] = 44, /* BERRY_JUICE -> BERRY_JUICE */
        [0x8C] = 198, /* SCOPE_LENS -> SCOPE_LENS */
        [0x8F] = 199, /* METAL_COAT -> METAL_COAT */
        [0x90] = 216, /* DRAGON_FANG -> DRAGON_FANG */
        [0x92] = 200, /* LEFTOVERS -> LEFTOVERS */
        [0x96] = 138, /* MYSTERYBERRY -> LEPPA_BERRY */
        [0x97] = 201, /* DRAGON_SCALE -> DRAGON_SCALE */
        [0x9C] = 45, /* SACRED_ASH -> SACRED_ASH */
        [0xA3] = 202, /* LIGHT_BALL -> LIGHT_BALL */
        [0xA9] = 93, /* SUN_STONE -> SUN_STONE */
        [0xAC] = 218, /* UP_GRADE -> UP_GRADE */
        [0xAD] = 139, /* BERRY -> ORAN_BERRY */
        [0xAE] = 142, /* GOLD_BERRY -> SITRUS_BERRY */
        [0xC4] = 293, /* TM_ROAR -> TM05_ROAR */
        [0xC5] = 294, /* TM_TOXIC -> TM06_TOXIC */
        [0xC9] = 298, /* TM_HIDDEN_POWER -> TM10_HIDDEN_POWER */
        [0xCA] = 299, /* TM_SUNNY_DAY -> TM11_SUNNY_DAY */
        [0xCD] = 302, /* TM_BLIZZARD -> TM14_BLIZZARD */
        [0xCE] = 303, /* TM_HYPER_BEAM -> TM15_HYPER_BEAM */
        [0xD0] = 305, /* TM_PROTECT -> TM17_PROTECT */
        [0xD1] = 306, /* TM_RAIN_DANCE -> TM18_RAIN_DANCE */
        [0xD2] = 307, /* TM_GIGA_DRAIN -> TM19_GIGA_DRAIN */
        [0xD4] = 309, /* TM_FRUSTRATION -> TM21_FRUSTRATION */
        [0xD5] = 310, /* TM_SOLARBEAM -> TM22_SOLAR_BEAM */
        [0xD6] = 311, /* TM_IRON_TAIL -> TM23_IRON_TAIL */
        [0xD8] = 313, /* TM_THUNDER -> TM25_THUNDER */
        [0xD9] = 314, /* TM_EARTHQUAKE -> TM26_EARTHQUAKE */
        [0xDA] = 315, /* TM_RETURN -> TM27_RETURN */
        [0xDB] = 316, /* TM_DIG -> TM28_DIG */
        [0xDD] = 317, /* TM_PSYCHIC_M -> TM29_PSYCHIC */
        [0xDE] = 318, /* TM_SHADOW_BALL -> TM30_SHADOW_BALL */
        [0xE0] = 320, /* TM_DOUBLE_TEAM -> TM32_DOUBLE_TEAM */
        [0xE4] = 324, /* TM_SLUDGE_BOMB -> TM36_SLUDGE_BOMB */
        [0xE5] = 325, /* TM_SANDSTORM -> TM37_SANDSTORM */
        [0xE6] = 326, /* TM_FIRE_BLAST -> TM38_FIRE_BLAST */
        [0xEC] = 332, /* TM_REST -> TM44_REST */
        [0xED] = 333, /* TM_ATTRACT -> TM45_ATTRACT */
        [0xEE] = 334, /* TM_THIEF -> TM46_THIEF */
        [0xEF] = 335, /* TM_STEEL_WING -> TM47_STEEL_WING */
    };
    uint16_t equivalent = equivalents[item];
    if (cleared) *cleared = item != 0 && equivalent == 0;
    return equivalent;
}
#endif
