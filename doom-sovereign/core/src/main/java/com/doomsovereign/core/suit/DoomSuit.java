package com.doomsovereign.core.suit;

import com.doomsovereign.core.api.ArmorRuntimeAdapter;
import com.doomsovereign.core.api.FlightEnvironment;
import com.doomsovereign.core.cooldown.CooldownSet;
import com.doomsovereign.core.energy.ArmorEnergy;
import com.doomsovereign.core.energy.DrainCategory;
import com.doomsovereign.core.energy.DrainTable;
import com.doomsovereign.core.energy.RechargeSource;
import com.doomsovereign.core.flight.FlightController;
import com.doomsovereign.core.flight.FlightInput;
import com.doomsovereign.core.flight.FlightOutput;
import com.doomsovereign.core.flight.FlightProfile;
import com.doomsovereign.core.focus.ArcaneFocus;
import com.doomsovereign.core.heat.HeatModel;
import com.doomsovereign.core.module.Capability;
import com.doomsovereign.core.module.Loadout;
import com.doomsovereign.core.module.Stat;
import com.doomsovereign.core.module.SuitStats;
import com.doomsovereign.core.shield.ShieldConfig;
import com.doomsovereign.core.shield.ShieldModel;
import java.util.Set;

/**
 * Everything one wearer's Royal Armor is doing, ticked once per server tick.
 *
 * <p>This is the object the Fabric adapter keeps per player: it feeds in input and environment,
 * and reads back flight velocities, HUD values and one-shot cues. Stats from the module loadout
 * are pushed into each subsystem by {@link #applyLoadout(Set)}, so subsystems never read modules
 * themselves.
 */
public final class DoomSuit {
    public static final int FIRST_EQUIP_TICKS = 50;
    public static final int QUICK_EQUIP_TICKS = 14;
    public static final int SHUTDOWN_TICKS = 10;
    public static final double BOLT_DAMAGE = 7;
    public static final double CHARGED_DAMAGE = 22;
    public static final double BEAM_DAMAGE_PER_TICK = 1.1;
    public static final double BOLT_HEAT = 9;
    public static final double CHARGED_HEAT = 34;
    public static final double BEAM_HEAT_PER_TICK = 1.6;
    public static final int CHARGE_TICKS = 30;
    static final double APPRENTICE_FOCUS_RECOVERY = 100.0 / (240 * 20);

    private final ArmorEnergy energy = ArmorEnergy.royalMk1();
    private final HeatModel heat = HeatModel.royalGauntlets();
    private ShieldModel shield = ShieldModel.royalMk1();
    private final ArcaneFocus focus = ArcaneFocus.apprentice();
    private final FlightController flight;
    private final CooldownSet cooldowns = new CooldownSet();
    private final Loadout loadout;
    private SuitStats stats;

    private DoomModeState mode = DoomModeState.INACTIVE;
    private int modeTimer;
    private boolean everInitialised;
    private long chargeStarted = -1;
    private boolean beaming;

    public DoomSuit(Loadout loadout, Set<String> research) {
        this.loadout = loadout;
        this.flight = new FlightController(FlightProfile.locked());
        cooldowns.define("bolt", 8, 1);
        cooldowns.define("charged_blast", 60, 1);
        cooldowns.define("pulse", 160, 1);
        cooldowns.define("scan", 40, 1);
        cooldowns.define("slam", 80, 1);
        applyLoadout(research);
    }

    /** Recomputes stats from modules and research and pushes them into every subsystem. */
    public void applyLoadout(Set<String> research) {
        stats = loadout.stats();
        long cap = Math.round(20_000 * stats.get(Stat.ENERGY_CAPACITY_MULT));
        energy.setCapacity(cap);
        energy.setRegenPerTick(2 + Math.round(stats.get(Stat.ENERGY_REGEN_ADD)));
        energy.setCostMultiplier(DrainCategory.FLIGHT, stats.get(Stat.FLIGHT_COST_MULT));
        energy.setCostMultiplier(DrainCategory.WEAPON, stats.get(Stat.WEAPON_COST_MULT));
        energy.setCostMultiplier(DrainCategory.SHIELD, stats.get(Stat.SHIELD_COST_MULT));
        heat.setPassivePerTick(0.25 + stats.get(Stat.PASSIVE_COOLING_ADD));
        heat.setActiveCoolingPerTick(stats.get(Stat.ACTIVE_COOLING_ADD));
        // the field emitter is rebuilt only when its hardware changes (loadouts change at the Armor Cradle, not mid-fight)
        ShieldConfig sc = ShieldConfig.royalMk1().withCapacity(ShieldConfig.royalMk1().capacity() * stats.get(Stat.SHIELD_CAPACITY_MULT))
                .withSpherical(stats.has(Capability.SPHERICAL_SHIELD));
        if (!sc.equals(shield.config())) shield = new ShieldModel(sc);
        shield.setArcaneInsulation(Math.min(1.0, stats.get(Stat.ARCANE_INSULATION_ADD)));
        focus.setBaseRecoveryPerTick(APPRENTICE_FOCUS_RECOVERY * stats.get(Stat.FOCUS_RECOVERY_MULT));
        boolean thrusters = loadout.installed().contains("thruster_mk1") || loadout.installed().contains("thruster_mk2");
        FlightProfile base = FlightProfile.royalMk1();
        flight.setProfile(new FlightProfile(thrusters && research.contains("repulsor_levitation"),
                stats.has(Capability.BOOST), stats.has(Capability.FALL_ARREST) || research.contains("emergency_repulsors"),
                base.cruiseSpeed() * stats.get(Stat.CRUISE_SPEED_MULT), base.boostSpeed() * stats.get(Stat.BOOST_SPEED_MULT),
                base.acceleration() * stats.get(Stat.ACCELERATION_MULT), base.braking(), base.climbRate(), base.arrestFallDistance()));
    }

    // ---- Doom Mode ----------------------------------------------------------------------------------
    /** Per-tick upkeep. Returns the flight output for the adapter to apply. */
    public FlightOutput tick(ArmorRuntimeAdapter wearer, FlightInput input, FlightEnvironment env, RechargeSource charger) {
        long now = wearer.gameTime();
        updateMode(wearer.equippedPieces() == 4);
        energy.tick(now, charger);
        heat.tick(0);
        focus.tick(now);
        if (now % 20 == 0) energy.tryConsume(DrainCategory.PASSIVE, DrainTable.PASSIVE_PER_SECOND, now);
        if (mode == DoomModeState.ACTIVE) {
            shield.tick(energy, now);
            if (beaming && !beamTick(now)) beaming = false;
            return flight.tick(input, env, energy, now);
        }
        if (flight.state().powered()) flight.shutdown();
        shield.lower(now);
        beaming = false;
        chargeStarted = -1;
        return flight.tick(FlightInput.NONE, env, energy, now);
    }

    private void updateMode(boolean fullSet) {
        switch (mode) {
            case INACTIVE -> {
                if (fullSet) {
                    mode = DoomModeState.INITIALISING;
                    modeTimer = everInitialised ? QUICK_EQUIP_TICKS : FIRST_EQUIP_TICKS;
                }
            }
            case INITIALISING -> {
                if (!fullSet) { mode = DoomModeState.INACTIVE; return; }
                if (--modeTimer <= 0) {
                    mode = DoomModeState.ACTIVE;
                    everInitialised = true;
                }
            }
            case ACTIVE -> {
                if (!fullSet) {
                    mode = DoomModeState.SHUTTING_DOWN;
                    modeTimer = SHUTDOWN_TICKS;
                }
            }
            case SHUTTING_DOWN -> {
                if (fullSet) { mode = DoomModeState.INITIALISING; modeTimer = QUICK_EQUIP_TICKS; return; }
                if (--modeTimer <= 0) mode = DoomModeState.INACTIVE;
            }
        }
    }

    /** 0..1 progress of the equip sequence, for animation and HUD fade. */
    public double initialisationProgress() {
        if (mode == DoomModeState.ACTIVE) return 1;
        if (mode != DoomModeState.INITIALISING) return 0;
        int total = everInitialised ? QUICK_EQUIP_TICKS : FIRST_EQUIP_TICKS;
        return 1.0 - modeTimer / (double) total;
    }

    // ---- gauntlets ----------------------------------------------------------------------------------
    public ShotResult fireBolt(long now) {
        if (mode != DoomModeState.ACTIVE) return ShotResult.refused(ShotResult.Refusal.NOT_IN_DOOM_MODE);
        if (!heat.canFire()) return ShotResult.refused(ShotResult.Refusal.OVERHEATED);
        if (!cooldowns.ready("bolt", now)) return ShotResult.refused(ShotResult.Refusal.COOLDOWN);
        if (!energy.tryConsume(DrainCategory.WEAPON, DrainTable.BOLT, now)) return ShotResult.refused(ShotResult.Refusal.NO_ENERGY);
        cooldowns.tryUse("bolt", now);
        double dmg = BOLT_DAMAGE * stats.get(Stat.WEAPON_DAMAGE_MULT) * heat.outputFactor();
        heat.addHeat(BOLT_HEAT);
        return ShotResult.fired(dmg);
    }

    /** Starts charging a heavy blast (hold the fire key). */
    public boolean beginCharge(long now) {
        if (mode != DoomModeState.ACTIVE || !heat.canFire() || !cooldowns.ready("charged_blast", now)) return false;
        chargeStarted = now;
        return true;
    }

    public double chargeProgress(long now) {
        if (chargeStarted < 0) return 0;
        int need = (int) Math.round(CHARGE_TICKS * stats.get(Stat.CHARGE_TIME_MULT));
        return Math.min(1.0, (now - chargeStarted) / (double) Math.max(1, need));
    }

    /** Releases the charge. Under-charged blasts fire weaker; releasing before 25 % fizzles. */
    public ShotResult releaseCharge(long now) {
        if (chargeStarted < 0) return ShotResult.refused(ShotResult.Refusal.NOT_CHARGING);
        double p = chargeProgress(now);
        chargeStarted = -1;
        if (mode != DoomModeState.ACTIVE) return ShotResult.refused(ShotResult.Refusal.NOT_IN_DOOM_MODE);
        if (p < 0.25) return ShotResult.refused(ShotResult.Refusal.NOT_CHARGING);
        if (!heat.canFire()) return ShotResult.refused(ShotResult.Refusal.OVERHEATED);
        if (!energy.tryConsume(DrainCategory.WEAPON, Math.round(DrainTable.CHARGED_BLAST * p), now))
            return ShotResult.refused(ShotResult.Refusal.NO_ENERGY);
        cooldowns.tryUse("charged_blast", now);
        double dmg = CHARGED_DAMAGE * p * stats.get(Stat.WEAPON_DAMAGE_MULT) * heat.outputFactor();
        heat.addHeat(CHARGED_HEAT * p);
        return ShotResult.fired(dmg);
    }

    public ShotResult startBeam(long now) {
        if (mode != DoomModeState.ACTIVE) return ShotResult.refused(ShotResult.Refusal.NOT_IN_DOOM_MODE);
        if (!stats.has(Capability.SUSTAINED_BEAM)) return ShotResult.refused(ShotResult.Refusal.NOT_UNLOCKED);
        if (!heat.canFire()) return ShotResult.refused(ShotResult.Refusal.OVERHEATED);
        beaming = true;
        return ShotResult.fired(BEAM_DAMAGE_PER_TICK);
    }

    public void stopBeam() {
        beaming = false;
    }

    private boolean beamTick(long now) {
        if (!heat.canFire()) return false;
        if (!energy.tryConsume(DrainCategory.WEAPON, DrainTable.BEAM_PER_TICK, now)) return false;
        heat.addHeat(BEAM_HEAT_PER_TICK);
        return true;
    }

    /** Beam damage this tick (0 when not beaming); throttled by heat. */
    public double beamDamage() {
        return beaming ? BEAM_DAMAGE_PER_TICK * stats.get(Stat.WEAPON_DAMAGE_MULT) * heat.outputFactor() : 0;
    }

    /** Movement multiplier while beaming: Doom plants his feet. */
    public double beamMovementFactor() {
        return beaming ? 0.35 : 1.0;
    }

    public boolean scan(long now) {
        if (mode != DoomModeState.ACTIVE || !cooldowns.ready("scan", now)) return false;
        if (!energy.tryConsume(DrainCategory.SCANNER, DrainTable.SCAN, now)) return false;
        return cooldowns.tryUse("scan", now);
    }

    public boolean pulse(long now) {
        if (mode != DoomModeState.ACTIVE || !cooldowns.ready("pulse", now)) return false;
        if (!energy.tryConsume(DrainCategory.WEAPON, DrainTable.PULSE, now)) return false;
        return cooldowns.tryUse("pulse", now);
    }

    // ---- accessors ------------------------------------------------------------------------------------
    public ArmorEnergy energy() { return energy; }

    public HeatModel heat() { return heat; }

    public ShieldModel shield() { return shield; }

    public ArcaneFocus focus() { return focus; }

    public FlightController flight() { return flight; }

    public CooldownSet cooldowns() { return cooldowns; }

    public Loadout loadout() { return loadout; }

    public SuitStats stats() { return stats; }

    public DoomModeState mode() { return mode; }

    public boolean everInitialised() { return everInitialised; }

    public boolean beaming() { return beaming; }

    /** Persistence. */
    public void restoreFlags(boolean initialisedBefore) {
        everInitialised = initialisedBefore;
    }
}
