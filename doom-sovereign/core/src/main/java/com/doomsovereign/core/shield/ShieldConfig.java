package com.doomsovereign.core.shield;

/**
 * Tunables for a shield emitter.
 *
 * @param capacity             field charge in damage points (half-hearts)
 * @param arcDegrees           width of the directional field
 * @param raiseTicks           spin-up before it absorbs
 * @param raiseChargeFraction  charge the field starts with when raised from empty
 * @param rechargeDelayTicks   ticks without hits before recharging
 * @param rechargePerTick      points per tick while recharging
 * @param rechargeCostFactor   energy multiplier for recharge compared with absorption
 * @param upkeepPerTick        DE per tick to hold a directional field
 * @param sphericalUpkeepPerTick DE per tick to hold a spherical field
 * @param sphericalCostFactor  energy per absorbed point multiplier for spherical mode
 * @param flickerFraction      below this fraction the field flickers
 * @param overloadFraction     a single hit of at least this share of capacity collapses the field
 * @param collapseLockoutTicks lockout after ordinary depletion
 * @param overloadLockoutTicks lockout after an overload
 * @param sphericalUnlocked    research/module gate for spherical mode
 */
public record ShieldConfig(double capacity, double arcDegrees, int raiseTicks, double raiseChargeFraction,
                           int rechargeDelayTicks, double rechargePerTick, double rechargeCostFactor,
                           long upkeepPerTick, long sphericalUpkeepPerTick, double sphericalCostFactor,
                           double flickerFraction, double overloadFraction, int collapseLockoutTicks,
                           int overloadLockoutTicks, boolean sphericalUnlocked) {
    public ShieldConfig {
        if (!(capacity > 0)) throw new IllegalArgumentException("capacity");
        if (!(arcDegrees > 0 && arcDegrees <= 360)) throw new IllegalArgumentException("arc");
        if (overloadFraction <= flickerFraction) throw new IllegalArgumentException("overload must exceed flicker");
    }

    public static ShieldConfig royalMk1() {
        return new ShieldConfig(40, 120, 5, 0.5, 60, 0.25, 0.6, 1, 3, 1.6, 0.25, 0.75, 100, 200, false);
    }

    public ShieldConfig withSpherical(boolean unlocked) {
        return new ShieldConfig(capacity, arcDegrees, raiseTicks, raiseChargeFraction, rechargeDelayTicks, rechargePerTick,
                rechargeCostFactor, upkeepPerTick, sphericalUpkeepPerTick, sphericalCostFactor, flickerFraction,
                overloadFraction, collapseLockoutTicks, overloadLockoutTicks, unlocked);
    }

    public ShieldConfig withCapacity(double c) {
        return new ShieldConfig(c, arcDegrees, raiseTicks, raiseChargeFraction, rechargeDelayTicks, rechargePerTick,
                rechargeCostFactor, upkeepPerTick, sphericalUpkeepPerTick, sphericalCostFactor, flickerFraction,
                overloadFraction, collapseLockoutTicks, overloadLockoutTicks, sphericalUnlocked);
    }
}
