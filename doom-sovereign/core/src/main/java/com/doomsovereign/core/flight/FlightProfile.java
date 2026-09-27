package com.doomsovereign.core.flight;

/**
 * What the current suit and research allow. Speeds in blocks per tick (1.0 b/t = 20 m/s).
 *
 * @param flightUnlocked     research "Repulsor Levitation" (flight is earned, not given)
 * @param boostUnlocked      thruster module Mk II or research "Afterburner Lattice"
 * @param fallArrestUnlocked kinetic dampener or research "Emergency Repulsors"
 * @param cruiseSpeed        normal top speed
 * @param boostSpeed         boost top speed
 * @param acceleration       speed gained per tick toward the target
 * @param braking            speed lost per tick when braking
 * @param climbRate          vertical speed with ascend/descend held
 * @param arrestFallDistance fall arrest triggers once the fall exceeds this many blocks
 */
public record FlightProfile(boolean flightUnlocked, boolean boostUnlocked, boolean fallArrestUnlocked, double cruiseSpeed,
                            double boostSpeed, double acceleration, double braking, double climbRate,
                            double arrestFallDistance) {
    public FlightProfile {
        if (!(cruiseSpeed > 0 && boostSpeed >= cruiseSpeed)) throw new IllegalArgumentException("speeds");
        if (!(acceleration > 0 && braking > 0 && climbRate > 0)) throw new IllegalArgumentException("rates");
    }

    /** Mk I thrusters: cruise 0.55 b/t (11 m/s), boost 1.1 b/t, gentle acceleration. */
    public static FlightProfile royalMk1() {
        return new FlightProfile(true, false, true, 0.55, 1.1, 0.035, 0.06, 0.3, 6);
    }

    public static FlightProfile locked() {
        return new FlightProfile(false, false, false, 0.55, 1.1, 0.035, 0.06, 0.3, 6);
    }

    public FlightProfile withBoost(boolean b) {
        return new FlightProfile(flightUnlocked, b, fallArrestUnlocked, cruiseSpeed, boostSpeed, acceleration, braking,
                climbRate, arrestFallDistance);
    }

    public FlightProfile withSpeeds(double cruise, double boost, double accel) {
        return new FlightProfile(flightUnlocked, boostUnlocked, fallArrestUnlocked, cruise, boost, accel, braking, climbRate,
                arrestFallDistance);
    }
}
