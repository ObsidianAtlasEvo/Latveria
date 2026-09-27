package com.doomsovereign.core.energy;

import com.doomsovereign.core.api.EnergyStorage;
import java.util.EnumMap;
import java.util.Map;

/**
 * The suit's power cell.
 *
 * <p>Design intent (directive section 13): passive functions cost almost nothing; weapons and
 * boost are expensive; flight covers useful distances; the suit regenerates slowly on its own and
 * quickly on a cradle or station; and running dry never makes the armour stop being armour. A
 * reserve band at the bottom of the cell is kept for the shield and emergency systems so that
 * spending everything on weapons cannot leave Doom unable to arrest a fatal fall.
 *
 * <p>All quantities are integer DE; every operation conserves energy exactly (verified by tests).
 */
public final class ArmorEnergy implements EnergyStorage {
    private long capacity;
    private long stored;
    private long regenPerTick;
    private double reserveFraction;
    private double lowFraction;
    private int regenDelayTicks;
    private long lastDrainTick = Long.MIN_VALUE / 2;
    private final Map<DrainCategory, Double> costMultipliers = new EnumMap<>(DrainCategory.class);

    /** Total DE ever consumed / regenerated / received; used by tests and diagnostics. */
    private long totalConsumed;
    private long totalRegenerated;
    private long totalReceived;

    public ArmorEnergy(long capacity, long regenPerTick, double reserveFraction, double lowFraction, int regenDelayTicks) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        if (regenPerTick < 0) throw new IllegalArgumentException("regen must be >= 0");
        if (reserveFraction < 0 || reserveFraction >= 1) throw new IllegalArgumentException("reserveFraction in [0,1)");
        if (lowFraction < reserveFraction || lowFraction > 1) throw new IllegalArgumentException("lowFraction in [reserve,1]");
        if (regenDelayTicks < 0) throw new IllegalArgumentException("regenDelay >= 0");
        this.capacity = capacity;
        this.regenPerTick = regenPerTick;
        this.reserveFraction = reserveFraction;
        this.lowFraction = lowFraction;
        this.regenDelayTicks = regenDelayTicks;
        for (DrainCategory c : DrainCategory.values()) costMultipliers.put(c, 1.0);
    }

    /** Royal Armor Mk I defaults: 20 000 DE, 2 DE/t regen after 3 s idle, 10 % reserve, 25 % warning. */
    public static ArmorEnergy royalMk1() {
        return new ArmorEnergy(20_000, 2, 0.10, 0.25, 60);
    }

    // ---- EnergyStorage ------------------------------------------------------------------------
    @Override public long capacity() { return capacity; }

    @Override public long stored() { return stored; }

    @Override
    public long insert(long amount, boolean simulate) {
        if (amount <= 0) return 0;
        long accepted = Math.min(amount, capacity - stored);
        if (!simulate) {
            stored += accepted;
            totalReceived += accepted;
        }
        return accepted;
    }

    @Override
    public long extract(long amount, boolean simulate) {
        if (amount <= 0) return 0;
        long removed = Math.min(amount, stored);
        if (!simulate) {
            stored -= removed;
            totalConsumed += removed;
        }
        return removed;
    }

    // ---- gameplay API -------------------------------------------------------------------------
    public long reserve() {
        return (long) Math.ceil(capacity * reserveFraction);
    }

    /** Energy a category may spend right now (reserve excluded unless the category allows it). */
    public long spendable(DrainCategory category) {
        return category.mayUseReserve() ? stored : Math.max(0, stored - reserve());
    }

    /** Cost after module multipliers, never below 0 and rounded up so nothing is ever free by rounding. */
    public long effectiveCost(DrainCategory category, long baseCost) {
        if (baseCost <= 0) return 0;
        double m = costMultipliers.get(category);
        return (long) Math.ceil(baseCost * m);
    }

    /**
     * All-or-nothing draw for discrete actions (a gauntlet shot, a scan pulse). Returns true and
     * debits the cell only if the whole effective cost is available to that category.
     */
    public boolean tryConsume(DrainCategory category, long baseCost, long now) {
        long cost = effectiveCost(category, baseCost);
        if (cost == 0) return true;
        if (spendable(category) < cost) return false;
        stored -= cost;
        totalConsumed += cost;
        if (category != DrainCategory.PASSIVE) lastDrainTick = now;
        return true;
    }

    /**
     * Partial draw for continuous systems (flight thrust, shield recharge): takes as much as is
     * allowed up to the cost and returns the fraction delivered (0..1).
     */
    public double drain(DrainCategory category, long baseCost, long now) {
        long cost = effectiveCost(category, baseCost);
        if (cost == 0) return 1.0;
        long take = Math.min(cost, spendable(category));
        stored -= take;
        totalConsumed += take;
        if (take > 0 && category != DrainCategory.PASSIVE) lastDrainTick = now;
        return (double) take / cost;
    }

    /** Per-tick upkeep: slow self-regeneration after an idle delay, plus any external charger. */
    public void tick(long now, RechargeSource charger) {
        if (charger != null && stored < capacity) {
            long got = Math.min(charger.ratePerTick(), capacity - stored);
            if (got > 0) {
                stored += got;
                totalReceived += got;
                charger.onDelivered(got);
            }
        }
        if (regenPerTick > 0 && stored < capacity && now - lastDrainTick >= regenDelayTicks) {
            long got = Math.min(regenPerTick, capacity - stored);
            stored += got;
            totalRegenerated += got;
        }
    }

    public EnergyStatus status() {
        if (stored <= 0) return EnergyStatus.DEPLETED;
        if (stored <= reserve()) return EnergyStatus.RESERVE;
        if (stored <= (long) Math.ceil(capacity * lowFraction)) return EnergyStatus.LOW;
        return EnergyStatus.NOMINAL;
    }

    /** Ticks a continuous draw of {@code perTick} could be sustained for; used for HUD estimates. */
    public long sustainTicks(DrainCategory category, long perTick) {
        long cost = effectiveCost(category, perTick);
        return cost == 0 ? Long.MAX_VALUE : spendable(category) / cost;
    }

    // ---- modules --------------------------------------------------------------------------------
    /** Replaces capacity (e.g. capacitor module). Stored energy is clamped, never created. */
    public void setCapacity(long newCapacity) {
        if (newCapacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        long lost = Math.max(0, stored - newCapacity);
        capacity = newCapacity;
        stored -= lost;
        totalConsumed += lost;
    }

    public void setRegenPerTick(long regen) {
        if (regen < 0) throw new IllegalArgumentException("regen >= 0");
        regenPerTick = regen;
    }

    public void setCostMultiplier(DrainCategory c, double m) {
        if (!(m > 0) || m > 10) throw new IllegalArgumentException("multiplier in (0,10]: " + m);
        costMultipliers.put(c, m);
    }

    public double costMultiplier(DrainCategory c) { return costMultipliers.get(c); }

    public long regenPerTick() { return regenPerTick; }

    public double reserveFraction() { return reserveFraction; }

    public int regenDelayTicks() { return regenDelayTicks; }

    public long lastDrainTick() { return lastDrainTick; }

    /** Restores persisted state; values are clamped rather than trusted. */
    public void restore(long storedValue, long lastDrain) {
        stored = Math.max(0, Math.min(capacity, storedValue));
        lastDrainTick = lastDrain;
    }

    public long totalConsumed() { return totalConsumed; }

    public long totalRegenerated() { return totalRegenerated; }

    public long totalReceived() { return totalReceived; }
}
