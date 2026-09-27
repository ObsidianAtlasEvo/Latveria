package com.doomsovereign.core.suit;

/**
 * Outcome of a gauntlet action.
 *
 * @param fired    whether it fired
 * @param damage   damage to apply to what it hits (after heat throttling and modules)
 * @param refusal  why it did not fire (null when fired)
 */
public record ShotResult(boolean fired, double damage, Refusal refusal) {
    public enum Refusal { NOT_IN_DOOM_MODE, COOLDOWN, OVERHEATED, NO_ENERGY, NOT_UNLOCKED, NOT_CHARGING }

    static ShotResult refused(Refusal r) {
        return new ShotResult(false, 0, r);
    }

    static ShotResult fired(double dmg) {
        return new ShotResult(true, dmg, null);
    }
}
