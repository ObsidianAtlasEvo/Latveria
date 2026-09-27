package com.doomsovereign.core.api;

import java.util.UUID;

/**
 * What the core needs to know about the player wearing Doom armour. The Fabric side implements this
 * over a {@code ServerPlayer}; tests implement it with plain fields.
 */
public interface ArmorRuntimeAdapter {
    UUID playerId();

    /** Number of Royal Armor pieces worn (0..4); Doom Mode requires all four. */
    int equippedPieces();

    /** Suit durability from 0 (broken) to 1 (pristine), averaged over worn pieces. */
    double durability();

    long gameTime();
}
