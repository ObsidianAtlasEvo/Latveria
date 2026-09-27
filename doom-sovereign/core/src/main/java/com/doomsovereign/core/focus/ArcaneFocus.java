package com.doomsovereign.core.focus;

import java.util.EnumMap;
import java.util.Map;

/**
 * Mystical concentration, independent of armour energy.
 *
 * <p>Instant spells spend focus at once. Channelled spells and rituals <em>reserve</em> their cost
 * when casting begins; the reservation is spent when the channel completes. If the caster is
 * interrupted (hit hard, moved out of the circle, silenced) the reserved focus is partly lost:
 * interruption must hurt, but not so much that one arrow wipes a ten-minute ritual's worth.
 * Recovery stops while channelling and for a short delay after any cast.
 */
public final class ArcaneFocus {
    private double capacity;
    private double current;
    private double reserved;
    private double baseRecoveryPerTick;
    private final int recoveryDelayTicks;
    private final double interruptLoss;
    private long lastCastTick = Long.MIN_VALUE / 2;
    private Channel channel;
    private final Map<FocusSource, Double> bonuses = new EnumMap<>(FocusSource.class);

    /** An active channel. */
    public record Channel(String spellId, double cost, long startedTick, int durationTicks) {
        public long completesAt() {
            return startedTick + durationTicks;
        }
    }

    public ArcaneFocus(double capacity, double baseRecoveryPerTick, int recoveryDelayTicks, double interruptLoss) {
        if (!(capacity > 0)) throw new IllegalArgumentException("capacity > 0");
        if (baseRecoveryPerTick < 0) throw new IllegalArgumentException("recovery >= 0");
        if (interruptLoss < 0 || interruptLoss > 1) throw new IllegalArgumentException("interruptLoss in [0,1]");
        this.capacity = capacity;
        this.current = capacity;
        this.baseRecoveryPerTick = baseRecoveryPerTick;
        this.recoveryDelayTicks = recoveryDelayTicks;
        this.interruptLoss = interruptLoss;
    }

    /** Apprentice sorcerer: 100 focus, full in ~4 minutes idle, 5 s delay, half lost on interruption. */
    public static ArcaneFocus apprentice() {
        return new ArcaneFocus(100, 100.0 / (240 * 20), 100, 0.5);
    }

    public double available() {
        return current - reserved;
    }

    /** Instant cast: spends the cost now if available. */
    public CastResult castInstant(double cost, long now) {
        if (cost < 0) throw new IllegalArgumentException("cost >= 0");
        if (available() + 1e-9 < cost) return CastResult.INSUFFICIENT_FOCUS;
        current -= cost;
        lastCastTick = now;
        return CastResult.COMPLETED;
    }

    /** Begins a channel, reserving its full cost. Only one channel at a time. */
    public CastResult beginChannel(String spellId, double cost, int durationTicks, long now) {
        if (cost < 0 || durationTicks <= 0) throw new IllegalArgumentException("cost >= 0, duration > 0");
        if (channel != null) return CastResult.ALREADY_CHANNELING;
        if (available() + 1e-9 < cost) return CastResult.INSUFFICIENT_FOCUS;
        reserved += cost;
        channel = new Channel(spellId, cost, now, durationTicks);
        lastCastTick = now;
        return CastResult.STARTED;
    }

    /** Called every tick while channelling; completes the channel when its time is up. */
    public CastResult advanceChannel(long now) {
        if (channel == null) return CastResult.NOT_CHANNELING;
        if (now < channel.completesAt()) return CastResult.STARTED;
        reserved -= channel.cost();
        current -= channel.cost();
        channel = null;
        lastCastTick = now;
        return CastResult.COMPLETED;
    }

    /** Interrupts the channel: the lost share of the reservation is spent, the rest returns. */
    public CastResult interrupt(long now) {
        if (channel == null) return CastResult.NOT_CHANNELING;
        double lost = channel.cost() * interruptLoss;
        reserved -= channel.cost();
        current -= lost;
        channel = null;
        lastCastTick = now;
        return CastResult.INTERRUPTED;
    }

    /** Progress of the active channel, 0..1 (0 when none). */
    public double channelProgress(long now) {
        if (channel == null) return 0;
        return Math.min(1.0, Math.max(0, (now - channel.startedTick()) / (double) channel.durationTicks()));
    }

    /** Sets a recovery bonus per tick from a source (0 removes it). */
    public void setBonus(FocusSource source, double perTick) {
        if (perTick < 0) throw new IllegalArgumentException();
        if (perTick == 0) bonuses.remove(source); else bonuses.put(source, perTick);
    }

    /** One-off grants (successful cast, supernatural kill). Capped at capacity. */
    public void grant(FocusSource source, double amount) {
        if (amount < 0) throw new IllegalArgumentException();
        current = Math.min(capacity, current + amount);
    }

    public void tick(long now) {
        if (channel != null) return;
        if (now - lastCastTick < recoveryDelayTicks) return;
        double r = baseRecoveryPerTick;
        for (double b : bonuses.values()) r += b;
        current = Math.min(capacity, current + r);
    }

    public void setCapacity(double c) {
        if (!(c > 0)) throw new IllegalArgumentException();
        capacity = c;
        current = Math.min(current, capacity);
        if (reserved > current) reserved = current;
    }

    public void setBaseRecoveryPerTick(double r) {
        if (r < 0) throw new IllegalArgumentException();
        baseRecoveryPerTick = r;
    }

    public void restore(double value) {
        current = Double.isFinite(value) ? Math.max(0, Math.min(capacity, value)) : capacity;
        reserved = 0;
        channel = null;
    }

    public double current() { return current; }

    public double reserved() { return reserved; }

    public double capacity() { return capacity; }

    public boolean channeling() { return channel != null; }

    public Channel channel() { return channel; }
}
