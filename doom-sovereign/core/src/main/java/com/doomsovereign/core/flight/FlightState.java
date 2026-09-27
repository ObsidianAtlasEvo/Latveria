package com.doomsovereign.core.flight;

public enum FlightState {
    /** Thrusters off: standing, walking, jumping or falling normally. */
    GROUNDED,
    /** Powered lift-off burst (short, fixed). */
    TAKEOFF,
    /** Station-keeping; vertical control only. */
    HOVER,
    /** Directional powered flight at cruise speed. */
    FLIGHT,
    /** Maximum thrust. */
    BOOST,
    /** Movement released: controlled deceleration back to hover. */
    BRAKE,
    /** Thrusters disengaged in the air: controlled descent to the ground. */
    DESCENT,
    /** Touch-down; plays the landing (hard or soft) and returns to GROUNDED. */
    LANDING,
    /** Repulsor burst that stops a dangerous fall. */
    FALL_ARREST,
    /** Energy ran into the reserve mid-flight: forced gentle descent on emergency power. */
    LOW_ENERGY_DESCENT;

    public boolean powered() {
        return this != GROUNDED && this != LANDING;
    }
}
