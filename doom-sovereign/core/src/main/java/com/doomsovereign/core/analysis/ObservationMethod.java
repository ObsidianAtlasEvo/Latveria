package com.doomsovereign.core.analysis;

/**
 * How Doom learns about a creature. Each method has a base knowledge gain and a minimum interval
 * between counted observations of the same subject, so standing next to one zombie scanning it all
 * night teaches little.
 */
public enum ObservationMethod {
    SCAN(10, 100),
    DEEP_SCAN(22, 200),
    OBSERVED_ATTACK(5, 40),
    DAMAGE_TAKEN(4, 40),
    DEFEATED(9, 0),
    SAMPLE(7, 0);

    private final double baseGain;
    private final int intervalTicks;

    ObservationMethod(double baseGain, int intervalTicks) {
        this.baseGain = baseGain;
        this.intervalTicks = intervalTicks;
    }

    public double baseGain() { return baseGain; }

    public int intervalTicks() { return intervalTicks; }
}
