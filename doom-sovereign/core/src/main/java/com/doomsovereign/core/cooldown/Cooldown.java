package com.doomsovereign.core.cooldown;

/**
 * A reusable cooldown with optional charges. With one charge it is an ordinary cooldown; with
 * several (e.g. two short-range teleports) charges regenerate one at a time.
 *
 * <p>Time is passed in explicitly, so the object is deterministic and safe to persist.
 */
public final class Cooldown {
    private final int baseTicks;
    private final int maxCharges;
    private int charges;
    /** Tick at which the next charge is restored; meaningful only while charges < max. */
    private long nextChargeAt;
    private double reduction;

    public Cooldown(int baseTicks, int maxCharges) {
        if (baseTicks < 0) throw new IllegalArgumentException("baseTicks >= 0");
        if (maxCharges < 1) throw new IllegalArgumentException("maxCharges >= 1");
        this.baseTicks = baseTicks;
        this.maxCharges = maxCharges;
        this.charges = maxCharges;
    }

    public static Cooldown of(int ticks) {
        return new Cooldown(ticks, 1);
    }

    private void refill(long now) {
        while (charges < maxCharges && now >= nextChargeAt) {
            charges++;
            if (charges < maxCharges) nextChargeAt += effectiveTicks();
        }
    }

    /** Duration after cooldown-reduction modifiers (never below one tick if base > 0). */
    public int effectiveTicks() {
        if (baseTicks == 0) return 0;
        return Math.max(1, (int) Math.round(baseTicks * (1.0 - reduction)));
    }

    public boolean ready(long now) {
        refill(now);
        return charges > 0;
    }

    /** Uses one charge if available; returns whether it was used. */
    public boolean tryUse(long now) {
        refill(now);
        if (charges == 0) return false;
        if (charges == maxCharges) nextChargeAt = now + effectiveTicks();
        charges--;
        return true;
    }

    /** Ticks until at least one charge is available (0 if ready). */
    public long remaining(long now) {
        refill(now);
        return charges > 0 ? 0 : Math.max(0, nextChargeAt - now);
    }

    /** Fraction of the current recharge completed, for HUD sweeps (1 when full). */
    public double progress(long now) {
        refill(now);
        if (charges == maxCharges || effectiveTicks() == 0) return 1.0;
        return 1.0 - Math.min(1.0, (nextChargeAt - now) / (double) effectiveTicks());
    }

    public int charges(long now) {
        refill(now);
        return charges;
    }

    public int maxCharges() { return maxCharges; }

    /** Cooldown reduction 0..0.75 from modules/research; applies to future recharges. */
    public void setReduction(double r) {
        if (r < 0 || r > 0.75) throw new IllegalArgumentException("reduction in [0,0.75]");
        reduction = r;
    }

    public void reset() {
        charges = maxCharges;
    }

    // persistence
    public long nextChargeAt() { return nextChargeAt; }

    public int storedCharges() { return charges; }

    public void restore(int storedCharges, long nextAt) {
        charges = Math.max(0, Math.min(maxCharges, storedCharges));
        nextChargeAt = nextAt;
    }
}
