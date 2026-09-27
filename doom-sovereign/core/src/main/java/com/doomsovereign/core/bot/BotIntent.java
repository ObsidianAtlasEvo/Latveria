package com.doomsovereign.core.bot;

import java.util.UUID;

/**
 * What the bot wants to do this decision cycle; the Minecraft side turns it into navigation,
 * attacks and animation.
 */
public record BotIntent(Type type, BotLocation location, UUID target, String reason) {
    public enum Type { IDLE, HOLD, MOVE_TO, ATTACK, TELEPORT_TO_OWNER, RETREAT_FOR_REPAIR }

    public static BotIntent idle(String why) { return new BotIntent(Type.IDLE, null, null, why); }

    public static BotIntent hold(BotLocation at, String why) { return new BotIntent(Type.HOLD, at, null, why); }

    public static BotIntent move(BotLocation to, String why) { return new BotIntent(Type.MOVE_TO, to, null, why); }

    public static BotIntent attack(UUID t, BotLocation at, String why) { return new BotIntent(Type.ATTACK, at, t, why); }
}
