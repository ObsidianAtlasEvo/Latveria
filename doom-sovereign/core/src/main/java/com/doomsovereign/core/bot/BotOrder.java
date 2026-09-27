package com.doomsovereign.core.bot;

import java.util.List;
import java.util.UUID;

/**
 * A command with its parameters.
 *
 * @param command      what to do
 * @param target       GUARD_ENTITY / ATTACK_TARGET subject
 * @param anchor       STAY position, DEFEND_AREA centre
 * @param radius       DEFEND_AREA radius
 * @param patrol       PATROL waypoints (at least two)
 */
public record BotOrder(BotCommand command, UUID target, BotLocation anchor, double radius, List<BotLocation> patrol) {
    public BotOrder {
        patrol = patrol == null ? List.of() : List.copyOf(patrol);
    }

    public static BotOrder follow() { return new BotOrder(BotCommand.FOLLOW, null, null, 0, null); }

    public static BotOrder stay(BotLocation at) { return new BotOrder(BotCommand.STAY, null, at, 0, null); }

    public static BotOrder passive() { return new BotOrder(BotCommand.PASSIVE, null, null, 0, null); }

    public static BotOrder returnHome() { return new BotOrder(BotCommand.RETURN_HOME, null, null, 0, null); }

    public static BotOrder attack(UUID t) { return new BotOrder(BotCommand.ATTACK_TARGET, t, null, 0, null); }

    public static BotOrder guard(UUID t) { return new BotOrder(BotCommand.GUARD_ENTITY, t, null, 0, null); }

    public static BotOrder defend(BotLocation c, double r) { return new BotOrder(BotCommand.DEFEND_AREA, null, c, r, null); }

    public static BotOrder patrol(List<BotLocation> pts) { return new BotOrder(BotCommand.PATROL, null, null, 0, pts); }
}
