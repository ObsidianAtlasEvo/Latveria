package com.doomsovereign.core.api;

/** Per-tick physical context for the flight state machine, sampled server-side. */
public interface FlightEnvironment {
    boolean onGround();

    /** Blocks per tick, positive upward. */
    double verticalVelocity();

    /** Blocks fallen since last touching ground (vanilla fallDistance). */
    double fallDistance();

    boolean inFluid();

    /** Clear air below, in blocks (capped by the adapter, e.g. 32). */
    int clearanceBelow();
}
