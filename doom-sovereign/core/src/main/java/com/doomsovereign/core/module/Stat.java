package com.doomsovereign.core.module;

/** Numeric suit stats. {@code MULT} stats multiply (start at 1), {@code ADD} stats add (start at 0). */
public enum Stat {
    ENERGY_CAPACITY_MULT(true),
    ENERGY_REGEN_ADD(false),
    FLIGHT_COST_MULT(true),
    CRUISE_SPEED_MULT(true),
    BOOST_SPEED_MULT(true),
    ACCELERATION_MULT(true),
    SHIELD_CAPACITY_MULT(true),
    SHIELD_COST_MULT(true),
    PASSIVE_COOLING_ADD(false),
    ACTIVE_COOLING_ADD(false),
    WEAPON_COST_MULT(true),
    WEAPON_DAMAGE_MULT(true),
    CHARGE_TIME_MULT(true),
    SENSOR_RANGE_ADD(false),
    KNOCKBACK_RESIST_ADD(false),
    FALL_DAMAGE_MULT(true),
    ARCANE_INSULATION_ADD(false),
    FOCUS_RECOVERY_MULT(true),
    TELEPORT_RANGE_ADD(false);

    private final boolean multiplicative;

    Stat(boolean multiplicative) {
        this.multiplicative = multiplicative;
    }

    public boolean multiplicative() {
        return multiplicative;
    }

    public double identity() {
        return multiplicative ? 1.0 : 0.0;
    }
}
