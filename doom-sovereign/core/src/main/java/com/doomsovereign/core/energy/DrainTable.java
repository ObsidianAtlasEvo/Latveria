package com.doomsovereign.core.energy;

/**
 * Base energy costs (DE) for Royal Armor Mk I, before module multipliers. Balanced so a full
 * 20 000 DE cell gives roughly: 8 min of hover, 2.5 min of cruise flight (~1.6 km), 40 s of boost,
 * 80 standard bolts, 16 charged blasts, or a shield that absorbs ~110 hearts from full.
 */
public final class DrainTable {
    private DrainTable() {
    }

    public static final long PASSIVE_PER_SECOND = 1;
    public static final long HOVER_PER_TICK = 2;
    public static final long CRUISE_PER_TICK = 6;
    public static final long BOOST_PER_TICK = 25;
    public static final long TAKEOFF = 60;
    public static final long FALL_ARREST = 400;
    public static final long BOLT = 250;
    public static final long CHARGED_BLAST = 1_200;
    public static final long BEAM_PER_TICK = 40;
    public static final long PULSE = 900;
    public static final long SCAN = 150;
    public static final long SHIELD_PER_POINT = 90;
    public static final long SHIELD_RAISE = 200;
    public static final long TRACTOR_PER_TICK = 4;
    public static final long OVERRIDE = 300;

    /**
     * Continuous flight cost this tick from speed and acceleration: hovering is cheap, cruising
     * moderate, acceleration and boost expensive.
     *
     * @param speed        horizontal speed in blocks/tick
     * @param cruiseSpeed  the suit's normal max speed in blocks/tick
     * @param acceleration change of speed this tick (blocks/tick^2, magnitude)
     * @param boosting     boost engaged
     */
    public static long flightCost(double speed, double cruiseSpeed, double acceleration, boolean boosting) {
        double s = cruiseSpeed <= 0 ? 0 : Math.min(3.0, speed / cruiseSpeed);
        double cost = HOVER_PER_TICK + (CRUISE_PER_TICK - HOVER_PER_TICK) * Math.min(1.0, s)
                + 120.0 * Math.abs(acceleration);
        if (boosting) cost = Math.max(cost, BOOST_PER_TICK * Math.max(1.0, s * 0.8));
        return (long) Math.ceil(cost);
    }
}
