package com.doomsovereign.core.bot;

/**
 * Server-tunable behaviour.
 *
 * @param followDistance      start walking when further than this from the owner
 * @param teleportDistance    teleport to the owner when further than this (same dimension, loaded)
 * @param teleportCooldown    ticks between teleports
 * @param engageRange         distance at which a guarding bot engages threats
 * @param stayEngageRange     a STAY bot defends only this close to its post
 * @param maxDefendRadius     largest DEFEND_AREA radius allowed
 * @param criticalHealth      below this fraction the bot retreats for repair
 * @param targetLostTicks     ATTACK_TARGET gives up after the target is unseen this long
 * @param memoryTicks         forget threats unseen for this long
 * @param pvp                 bots may engage players who attack their owner
 */
public record BotConfig(double followDistance, double teleportDistance, int teleportCooldown, double engageRange,
                        double stayEngageRange, double maxDefendRadius, double criticalHealth, int targetLostTicks,
                        int memoryTicks, boolean pvp) {
    public static BotConfig defaults() {
        return new BotConfig(4, 28, 100, 12, 6, 48, 0.25, 200, 600, false);
    }
}
