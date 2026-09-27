package com.doomsovereign.core.shield;

import com.doomsovereign.core.api.ShieldDamageContext;
import com.doomsovereign.core.api.ShieldDamageContext.DamageKind;
import com.doomsovereign.core.energy.ArmorEnergy;
import com.doomsovereign.core.energy.DrainCategory;
import com.doomsovereign.core.energy.DrainTable;
import java.util.EnumMap;
import java.util.Map;

/**
 * Doom's force field (directive section 18).
 *
 * <p>The field has its own charge (in damage points). Raising it costs a burst of armour energy;
 * while active it slowly refills from armour energy; every absorbed point is paid for. Hits from
 * outside the covered arc pass straight through. Different damage kinds interact differently:
 * energy and projectiles are what the field was built for, explosions are partly absorbed, and
 * sorcery slides through technology unless the suit carries arcane insulation or a techno-arcane
 * ward. A single hit stronger than the overload threshold collapses the field outright, with a
 * longer lockout than ordinary depletion.
 */
public final class ShieldModel {
    private final ShieldConfig cfg;
    private ShieldMode mode = ShieldMode.DIRECTIONAL;
    private ShieldState state = ShieldState.OFF;
    private double charge;
    private long stateSince;
    private long lastHit = Long.MIN_VALUE / 2;
    private long collapsedUntil;
    private double arcaneInsulation;
    private final Map<DamageKind, Double> efficiency = new EnumMap<>(DamageKind.class);

    public ShieldModel(ShieldConfig cfg) {
        this.cfg = cfg;
        efficiency.put(DamageKind.KINETIC, 0.85);
        efficiency.put(DamageKind.PROJECTILE, 1.0);
        efficiency.put(DamageKind.EXPLOSIVE, 0.7);
        efficiency.put(DamageKind.ENERGY, 1.0);
        efficiency.put(DamageKind.ARCANE, 0.25);
        efficiency.put(DamageKind.ENVIRONMENTAL, 0.0);
        efficiency.put(DamageKind.UNBLOCKABLE, 0.0);
    }

    public static ShieldModel royalMk1() {
        return new ShieldModel(ShieldConfig.royalMk1());
    }

    /** Raises the field in the given mode. Fails while collapsed or without the raise energy. */
    public boolean raise(ShieldMode m, ArmorEnergy energy, long now) {
        if (state == ShieldState.COLLAPSED && now < collapsedUntil) return false;
        if (m == ShieldMode.SPHERICAL && !cfg.sphericalUnlocked()) return false;
        if (state == ShieldState.ACTIVE || state == ShieldState.RAISING || state == ShieldState.FAILING) {
            mode = m;
            return true;
        }
        if (!energy.tryConsume(DrainCategory.SHIELD, DrainTable.SHIELD_RAISE, now)) return false;
        mode = m;
        state = ShieldState.RAISING;
        stateSince = now;
        // the recharge delay counts from the raise, so a freshly raised field starts at its raise charge
        lastHit = now;
        charge = Math.max(charge, cfg.capacity() * cfg.raiseChargeFraction());
        return true;
    }

    public void lower(long now) {
        if (state != ShieldState.COLLAPSED) {
            state = ShieldState.OFF;
            stateSince = now;
        }
    }

    public boolean covers(double bearingDeg) {
        if (mode == ShieldMode.SPHERICAL) return true;
        double b = normalize(bearingDeg);
        return Math.abs(b) <= cfg.arcDegrees() / 2.0;
    }

    /** Resolves one incoming hit. Energy for absorbed points is drawn from the armour cell. */
    public AbsorbResult absorb(ShieldDamageContext hit, ArmorEnergy energy, long now) {
        double amount = hit.amount();
        if (!isAbsorbing() || amount <= 0 || !covers(hit.bearingDeg())) return AbsorbResult.untouched(amount, hit.bearingDeg());
        double eff = efficiency.get(hit.kind());
        if (hit.kind() == DamageKind.ARCANE) eff = Math.min(1.0, eff + arcaneInsulation);
        if (eff <= 0) return AbsorbResult.untouched(amount, hit.bearingDeg());
        lastHit = now;
        // overload: one impact larger than the threshold breaks the field
        if (amount * eff >= cfg.capacity() * cfg.overloadFraction()) {
            double absorbed = Math.min(charge, amount * eff);
            payFor(absorbed, energy, now);
            collapse(now, true);
            return new AbsorbResult(absorbed, amount - absorbed, true, 1.0, hit.bearingDeg());
        }
        double want = amount * eff;
        double absorbed = Math.min(charge, want);
        // every absorbed point must be paid for; if the cell cannot pay, absorb less
        double paidFraction = payFor(absorbed, energy, now);
        absorbed *= paidFraction;
        charge -= absorbed;
        double through = amount - absorbed;
        boolean collapsed = false;
        if (charge <= 1e-9) {
            charge = 0;
            collapse(now, false);
            collapsed = true;
        } else if (charge < cfg.capacity() * cfg.flickerFraction()) {
            state = ShieldState.FAILING;
        }
        double ripple = Math.min(1.0, absorbed / (cfg.capacity() * 0.25));
        return new AbsorbResult(absorbed, through, collapsed, ripple, hit.bearingDeg());
    }

    private double payFor(double points, ArmorEnergy energy, long now) {
        if (points <= 0) return 1.0;
        double perPoint = DrainTable.SHIELD_PER_POINT * (mode == ShieldMode.SPHERICAL ? cfg.sphericalCostFactor() : 1.0);
        long cost = (long) Math.ceil(points * perPoint);
        return energy.drain(DrainCategory.SHIELD, cost, now);
    }

    private void collapse(long now, boolean overload) {
        state = ShieldState.COLLAPSED;
        stateSince = now;
        charge = 0;
        collapsedUntil = now + (overload ? cfg.overloadLockoutTicks() : cfg.collapseLockoutTicks());
    }

    /** Per tick: finishes raising, pays upkeep, recharges once the delay since the last hit (or the raise) has passed. */
    public void tick(ArmorEnergy energy, long now) {
        switch (state) {
            case OFF -> {
                return;
            }
            case COLLAPSED -> {
                if (now >= collapsedUntil) {
                    state = ShieldState.OFF;
                    stateSince = now;
                }
                return;
            }
            case RAISING -> {
                if (now - stateSince >= cfg.raiseTicks()) {
                    state = ShieldState.ACTIVE;
                    stateSince = now;
                }
            }
            default -> {
            }
        }
        long upkeep = mode == ShieldMode.SPHERICAL ? cfg.sphericalUpkeepPerTick() : cfg.upkeepPerTick();
        if (energy.drain(DrainCategory.SHIELD, upkeep, now) < 1.0) {
            // cannot hold the field up any more
            collapse(now, false);
            return;
        }
        if (charge < cfg.capacity() && now - lastHit >= cfg.rechargeDelayTicks()) {
            double add = Math.min(cfg.rechargePerTick(), cfg.capacity() - charge);
            long cost = (long) Math.ceil(add * DrainTable.SHIELD_PER_POINT * cfg.rechargeCostFactor());
            double got = energy.drain(DrainCategory.SHIELD, cost, now);
            charge += add * got;
        }
        if (state == ShieldState.FAILING && charge >= cfg.capacity() * cfg.flickerFraction()) state = ShieldState.ACTIVE;
    }

    public boolean isAbsorbing() {
        return state == ShieldState.ACTIVE || state == ShieldState.FAILING;
    }

    public void setArcaneInsulation(double v) {
        if (v < 0 || v > 1) throw new IllegalArgumentException();
        arcaneInsulation = v;
    }

    public void setEfficiency(DamageKind kind, double v) {
        if (v < 0 || v > 1) throw new IllegalArgumentException();
        if (kind == DamageKind.UNBLOCKABLE && v > 0) throw new IllegalArgumentException("unblockable stays unblockable");
        efficiency.put(kind, v);
    }

    static double normalize(double deg) {
        double d = deg % 360.0;
        if (d > 180) d -= 360;
        if (d < -180) d += 360;
        return d;
    }

    public ShieldState state() { return state; }

    public ShieldMode mode() { return mode; }

    public double charge() { return charge; }

    public double fraction() { return charge / cfg.capacity(); }

    public ShieldConfig config() { return cfg; }

    public long collapsedUntil() { return collapsedUntil; }
}
