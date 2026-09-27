package com.doomsovereign.core.module;

import java.util.Map;

/**
 * A suit chassis: how much it can carry.
 *
 * @param id              suit id
 * @param tier            1 = Royal Mk I ... 4 = prestige
 * @param capacity        power budget for modules
 * @param comfortableMass mass above this slows flight and acceleration
 * @param slots           slots per kind
 * @param base            the frame's own stat modifiers (e.g. Siege: heavy, resilient)
 */
public record SuitFrame(String id, int tier, int capacity, int comfortableMass, Map<SlotKind, Integer> slots,
                        Map<Stat, Double> base) {
    public SuitFrame {
        slots = Map.copyOf(slots);
        base = Map.copyOf(base);
    }

    public int slots(SlotKind k) {
        return slots.getOrDefault(k, 0);
    }
}
