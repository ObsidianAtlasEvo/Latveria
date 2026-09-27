package com.doomsovereign.core.heat;

/**
 * Gauntlet/weapon heat (directive section 30). Only high-output weapons add heat; mundane systems
 * never do. Heat dissipates every tick, faster with cooling modules and in water or snow (the
 * adapter reports an environmental cooling bonus). Hitting the critical threshold locks weapons
 * until heat falls below a lower recovery threshold (hysteresis), rather than harming the suit.
 */
public final class HeatModel {
    private final double max;
    private final double warning;
    private final double throttle;
    private final double critical;
    private final double recovery;
    private final double minThrottleFactor;
    private double passivePerTick;
    private double activeCoolingPerTick;
    private double heat;
    private boolean locked;
    private int ticksSinceHeat = Integer.MAX_VALUE / 2;
    private final int activeCoolingDelay;

    public HeatModel(double max, double warning, double throttle, double critical, double recovery,
                     double minThrottleFactor, double passivePerTick, double activeCoolingPerTick, int activeCoolingDelay) {
        if (!(0 < warning && warning <= throttle && throttle < critical && critical <= max))
            throw new IllegalArgumentException("need 0 < warning <= throttle < critical <= max");
        if (!(0 <= recovery && recovery < critical)) throw new IllegalArgumentException("recovery < critical");
        if (!(minThrottleFactor > 0 && minThrottleFactor <= 1)) throw new IllegalArgumentException("minThrottleFactor");
        this.max = max;
        this.warning = warning;
        this.throttle = throttle;
        this.critical = critical;
        this.recovery = recovery;
        this.minThrottleFactor = minThrottleFactor;
        this.passivePerTick = passivePerTick;
        this.activeCoolingPerTick = activeCoolingPerTick;
        this.activeCoolingDelay = activeCoolingDelay;
    }

    /** Mk I gauntlets: 100 heat, warning 50, throttle 70, lock at 100, unlock at 40. */
    public static HeatModel royalGauntlets() {
        return new HeatModel(100, 50, 70, 100, 40, 0.35, 0.25, 0.0, 20);
    }

    /** Adds heat from firing. Heat past max is discarded; reaching critical locks. */
    public void addHeat(double amount) {
        if (amount < 0) throw new IllegalArgumentException("heat must be >= 0");
        if (amount == 0) return;
        heat = Math.min(max, heat + amount);
        ticksSinceHeat = 0;
        if (heat >= critical) locked = true;
    }

    /**
     * Per-tick dissipation. Passive cooling always applies; active cooling (modules) starts after
     * a short delay without firing; {@code environmentBonus} adds e.g. rain/water cooling.
     */
    public void tick(double environmentBonus) {
        double cool = passivePerTick + Math.max(0, environmentBonus);
        if (ticksSinceHeat >= activeCoolingDelay) cool += activeCoolingPerTick;
        heat = Math.max(0, heat - cool);
        if (ticksSinceHeat < Integer.MAX_VALUE / 2) ticksSinceHeat++;
        if (locked && heat <= recovery) locked = false;
    }

    public boolean canFire() {
        return !locked;
    }

    /** True if a shot adding {@code amount} heat is permitted now (locked weapons refuse). */
    public boolean canFire(double amount) {
        return !locked && amount >= 0;
    }

    /** Output multiplier 1.0 .. minThrottleFactor between the throttle and critical thresholds. */
    public double outputFactor() {
        if (locked) return 0;
        if (heat <= throttle) return 1.0;
        double t = (heat - throttle) / (critical - throttle);
        return 1.0 - (1.0 - minThrottleFactor) * Math.min(1.0, t);
    }

    public HeatState state() {
        if (locked) return HeatState.LOCKED;
        if (heat > throttle) return HeatState.THROTTLED;
        if (heat >= warning) return HeatState.WARNING;
        return HeatState.NOMINAL;
    }

    public void setPassivePerTick(double v) {
        if (v < 0) throw new IllegalArgumentException();
        passivePerTick = v;
    }

    public void setActiveCoolingPerTick(double v) {
        if (v < 0) throw new IllegalArgumentException();
        activeCoolingPerTick = v;
    }

    public double heat() { return heat; }

    public double fraction() { return heat / max; }

    public double max() { return max; }

    public double critical() { return critical; }

    public double recovery() { return recovery; }

    public void restore(double value, boolean wasLocked) {
        heat = Math.max(0, Math.min(max, Double.isFinite(value) ? value : 0));
        locked = wasLocked && heat > recovery;
    }

    public boolean locked() { return locked; }

    /** Ticks of continuous cooling needed to clear a lock (for the HUD), 0 if not locked. */
    public int ticksToUnlock() {
        if (!locked) return 0;
        double rate = passivePerTick + activeCoolingPerTick;
        return rate <= 0 ? Integer.MAX_VALUE : (int) Math.ceil((heat - recovery) / rate);
    }
}
