package com.doomsovereign.core.api;

import com.doomsovereign.core.bot.BotLocation;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * The slice of the world a Doombot's decision logic may read. Implemented over a ServerLevel with
 * cheap, cached queries (target scans run every few ticks, never every tick).
 */
public interface BotWorldAdapter {
    long gameTime();

    BotLocation selfLocation();

    /** Owner's location if the owner is online and in a loaded chunk. */
    Optional<BotLocation> ownerLocation();

    /** Location of an arbitrary tracked entity if loaded. */
    Optional<BotLocation> locate(UUID entity);

    /** Hostile or attacking entities within sensor range, nearest first. */
    List<Contact> contacts();

    /** Current health fraction 0..1. */
    double selfHealth();

    /**
     * One sensed entity.
     *
     * @param id               entity UUID
     * @param location         where it is
     * @param hostile          a hostile mob (vanilla monster category or tagged)
     * @param attackingOwner   it has damaged, or is targeting, the bot's owner recently
     * @param attackingSelf    it has damaged this bot recently
     * @param player           it is a player (players are only engaged when explicitly permitted)
     */
    record Contact(UUID id, BotLocation location, boolean hostile, boolean attackingOwner, boolean attackingSelf,
                   boolean player) {
    }
}
