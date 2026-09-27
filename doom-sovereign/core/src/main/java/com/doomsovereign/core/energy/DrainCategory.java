package com.doomsovereign.core.energy;

/**
 * Why armour energy is being spent. Categories decide whether a draw may dip into the emergency
 * reserve and which module multipliers apply.
 */
public enum DrainCategory {
    /** HUD, servos, sensors idling. Negligible, may use reserve. */
    PASSIVE(true),
    /** Thrusters. Cannot use the reserve (low energy forces a controlled descent instead). */
    FLIGHT(false),
    /** Force-field charge. May use the reserve: the last line of defence. */
    SHIELD(true),
    /** Gauntlet weapons. Never the reserve. */
    WEAPON(false),
    /** Scanner pulses and analysis. */
    SCANNER(false),
    /** Tractor field, remote override, tools. */
    UTILITY(false),
    /** Fall arrest and similar life-saving bursts. May use the reserve. */
    EMERGENCY(true);

    private final boolean mayUseReserve;

    DrainCategory(boolean mayUseReserve) {
        this.mayUseReserve = mayUseReserve;
    }

    public boolean mayUseReserve() {
        return mayUseReserve;
    }
}
