package com.doomsovereign.core.module;

import java.util.EnumMap;
import java.util.EnumSet;
import java.util.Map;
import java.util.Set;

/** The combined effect of a frame and its modules. */
public final class SuitStats {
    private final Map<Stat, Double> values = new EnumMap<>(Stat.class);
    private final Set<Capability> capabilities = EnumSet.noneOf(Capability.class);
    private final int mass;
    private final int capacityUsed;
    private final double massPenalty;

    SuitStats(Map<Stat, Double> values, Set<Capability> caps, int mass, int capacityUsed, double massPenalty) {
        for (Stat s : Stat.values()) this.values.put(s, values.getOrDefault(s, s.identity()));
        this.capabilities.addAll(caps);
        this.mass = mass;
        this.capacityUsed = capacityUsed;
        this.massPenalty = massPenalty;
    }

    public double get(Stat s) {
        return values.get(s);
    }

    public boolean has(Capability c) {
        return capabilities.contains(c);
    }

    public Set<Capability> capabilities() {
        return EnumSet.copyOf(capabilities.isEmpty() ? EnumSet.noneOf(Capability.class) : capabilities);
    }

    public int mass() { return mass; }

    public int capacityUsed() { return capacityUsed; }

    /** 1.0 when within comfortable mass, lower when overloaded (applied to speeds already). */
    public double massPenalty() { return massPenalty; }
}
