package com.doomsovereign.core.flight;

/**
 * Player intent for one tick, already validated server-side (the client only sends key states).
 *
 * @param toggle  flight key pressed this tick (edge, not held)
 * @param forward -1..1
 * @param strafe  -1..1 (positive = right)
 * @param ascend  jump key held
 * @param descend sneak key held
 * @param boost   sprint/boost key held
 */
public record FlightInput(boolean toggle, double forward, double strafe, boolean ascend, boolean descend, boolean boost) {
    public static final FlightInput NONE = new FlightInput(false, 0, 0, false, false, false);

    public FlightInput {
        forward = clamp(forward);
        strafe = clamp(strafe);
    }

    private static double clamp(double v) {
        return Double.isFinite(v) ? Math.max(-1, Math.min(1, v)) : 0;
    }

    public double magnitude() {
        return Math.min(1.0, Math.hypot(forward, strafe));
    }

    public static FlightInput togglePress() {
        return new FlightInput(true, 0, 0, false, false, false);
    }

    public static FlightInput move(double forward, double strafe) {
        return new FlightInput(false, forward, strafe, false, false, false);
    }

    public FlightInput withBoost() {
        return new FlightInput(toggle, forward, strafe, ascend, descend, true);
    }

    public FlightInput withAscend() {
        return new FlightInput(toggle, forward, strafe, true, descend, boost);
    }

    public FlightInput withDescend() {
        return new FlightInput(toggle, forward, strafe, ascend, true, boost);
    }
}
