package com.doomsovereign.core.api;

/**
 * A single incoming hit, translated from Minecraft's damage source by the adapter.
 *
 * @param amount       damage in half-hearts before the shield
 * @param kind         broad family used for shield interaction
 * @param bearingDeg   direction the hit came from, relative to the wearer's facing
 *                     (0 = straight ahead, +-180 = from behind)
 */
public record ShieldDamageContext(double amount, DamageKind kind, double bearingDeg) {
    public enum DamageKind {
        /** Melee, falling blocks, mob contact. */
        KINETIC,
        /** Arrows, tridents, fireballs as objects. */
        PROJECTILE,
        /** Explosions and blasts. */
        EXPLOSIVE,
        /** Beams, lightning, Doom technology. */
        ENERGY,
        /** Sorcery, wither, evoker fangs, harming. */
        ARCANE,
        /** Fire, lava, freezing: handled by environmental systems, not the shield. */
        ENVIRONMENTAL,
        /** Void, /kill, starvation: never intercepted. */
        UNBLOCKABLE
    }

    public ShieldDamageContext {
        if (!(amount >= 0)) throw new IllegalArgumentException("amount must be >= 0: " + amount);
    }
}
