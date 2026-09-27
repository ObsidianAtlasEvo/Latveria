package com.doomsovereign.core.suit;

import com.doomsovereign.core.energy.RechargeSource;
import com.doomsovereign.core.flight.FlightInput;
import com.doomsovereign.core.flight.FlightState;
import com.doomsovereign.core.module.Loadout;
import com.doomsovereign.core.module.ModuleCatalog;
import com.doomsovereign.core.shield.ShieldMode;
import com.doomsovereign.core.support.Fakes.Env;
import com.doomsovereign.core.support.Fakes.Wearer;
import java.util.Set;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DoomSuitTest {
    static final ModuleCatalog CAT = ModuleCatalog.standard();
    static final Set<String> FLIGHT_RESEARCH = Set.of("repulsor_levitation", "coherent_emitters", "omnidirectional_fields");

    static DoomSuit suit(String frame, Set<String> research, String... modules) {
        Loadout l = new Loadout(CAT, CAT.frame(frame));
        for (String m : modules) assertTrue(l.install(m, research).isEmpty(), m);
        DoomSuit s = new DoomSuit(l, research);
        s.energy().insert(s.energy().capacity(), false);
        return s;
    }

    /** Ticks the suit with all four pieces on until Doom Mode is active; returns the next tick. */
    static long activate(DoomSuit s, Wearer w) {
        long t = w.time;
        for (int i = 0; i < 200 && s.mode() != DoomModeState.ACTIVE; i++) {
            w.time = t++;
            s.tick(w, FlightInput.NONE, Env.ground(), null);
        }
        assertEquals(DoomModeState.ACTIVE, s.mode());
        return t;
    }

    @Test
    void doomModeNeedsTheFullSetAndAnInitialisation() {
        DoomSuit s = suit("royal_mk1", Set.of());
        Wearer w = new Wearer();
        w.pieces = 3;
        for (int i = 0; i < 100; i++) { w.time = i; s.tick(w, FlightInput.NONE, Env.ground(), null); }
        assertEquals(DoomModeState.INACTIVE, s.mode());
        assertEquals(ShotResult.Refusal.NOT_IN_DOOM_MODE, s.fireBolt(100).refusal());
        w.pieces = 4;
        int ticks = 0;
        double prev = -1;
        while (s.mode() != DoomModeState.ACTIVE) {
            w.time = 100 + ticks++;
            s.tick(w, FlightInput.NONE, Env.ground(), null);
            assertTrue(s.initialisationProgress() >= prev);
            prev = s.initialisationProgress();
        }
        assertEquals(DoomSuit.FIRST_EQUIP_TICKS + 1, ticks, "one tick to begin, then the full first-equip sequence");
        assertTrue(s.everInitialised());
    }

    @Test
    void laterEquipsAreQuickAndRemovalShutsDown() {
        DoomSuit s = suit("royal_mk1", Set.of());
        Wearer w = new Wearer();
        long t = activate(s, w);
        w.pieces = 3;
        w.time = t++;
        s.tick(w, FlightInput.NONE, Env.ground(), null);
        assertEquals(DoomModeState.SHUTTING_DOWN, s.mode());
        for (int i = 0; i < DoomSuit.SHUTDOWN_TICKS; i++) { w.time = t++; s.tick(w, FlightInput.NONE, Env.ground(), null); }
        assertEquals(DoomModeState.INACTIVE, s.mode());
        w.pieces = 4;
        int ticks = 0;
        while (s.mode() != DoomModeState.ACTIVE) { w.time = t++; ticks++; s.tick(w, FlightInput.NONE, Env.ground(), null); }
        assertEquals(DoomSuit.QUICK_EQUIP_TICKS + 1, ticks);
    }

    @Test
    void flightIsEarnedThroughModuleAndResearch() {
        Wearer w = new Wearer();
        DoomSuit noModule = suit("royal_mk1", FLIGHT_RESEARCH);
        long t = activate(noModule, w);
        w.time = t;
        assertEquals(FlightState.GROUNDED, noModule.tick(w, FlightInput.togglePress(), Env.ground(), null).state());

        Wearer w2 = new Wearer();
        DoomSuit flying = suit("royal_mk1", FLIGHT_RESEARCH, "thruster_mk1");
        t = activate(flying, w2);
        w2.time = t;
        assertEquals(FlightState.TAKEOFF, flying.tick(w2, FlightInput.togglePress(), Env.ground(), null).state());
    }

    @Test
    void removingArmourMidFlightCutsThrust() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", FLIGHT_RESEARCH, "thruster_mk1");
        long t = activate(s, w);
        w.time = t++;
        s.tick(w, FlightInput.togglePress(), Env.ground(), null);
        for (int i = 0; i < 20; i++) { w.time = t++; s.tick(w, FlightInput.move(1, 0), Env.air(), null); }
        assertTrue(s.flight().state().powered());
        w.pieces = 2;
        w.time = t++;
        s.tick(w, FlightInput.move(1, 0), Env.air(), null);
        assertFalse(s.flight().state().powered());
    }

    @Test
    void boltsCostEnergyHeatAndRespectCooldown() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", Set.of());
        long t = activate(s, w);
        long e0 = s.energy().stored();
        ShotResult r = s.fireBolt(t);
        assertTrue(r.fired());
        assertEquals(DoomSuit.BOLT_DAMAGE, r.damage(), 1e-12);
        assertEquals(250, e0 - s.energy().stored());
        assertEquals(DoomSuit.BOLT_HEAT, s.heat().heat(), 1e-12);
        assertEquals(ShotResult.Refusal.COOLDOWN, s.fireBolt(t + 1).refusal());
        assertTrue(s.fireBolt(t + 8).fired());
    }

    @Test
    void sustainedFireOverheatsAndThrottles() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", Set.of());
        long t = activate(s, w);
        double firstDamage = s.fireBolt(t).damage();
        double lastDamage = firstDamage;
        ShotResult.Refusal refusal = null;
        for (long k = 1; k < 400 && refusal != ShotResult.Refusal.OVERHEATED; k++) {
            ShotResult r = s.fireBolt(t + k * 8);
            if (r.fired()) lastDamage = r.damage();
            else refusal = r.refusal();
        }
        assertEquals(ShotResult.Refusal.OVERHEATED, refusal);
        assertTrue(lastDamage < firstDamage, "damage throttles before lockout");
    }

    @Test
    void chargedBlastScalesWithChargeAndFizzlesEarly() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", Set.of());
        long t = activate(s, w);
        assertTrue(s.beginCharge(t));
        assertEquals(ShotResult.Refusal.NOT_CHARGING, s.releaseCharge(t + 5).refusal(), "released before 25 %");
        assertTrue(s.beginCharge(t + 10));
        assertEquals(0.5, s.chargeProgress(t + 25), 1e-12);
        long e0 = s.energy().stored();
        ShotResult full = s.releaseCharge(t + 40);
        assertTrue(full.fired());
        assertEquals(DoomSuit.CHARGED_DAMAGE, full.damage(), 1e-12);
        assertEquals(1200, e0 - s.energy().stored());
        assertFalse(s.beginCharge(t + 41), "cooldown");
    }

    @Test
    void focusingLensesSpeedUpChargingAndUnlockTheBeam() {
        Wearer w = new Wearer();
        DoomSuit plain = suit("royal_mk2", FLIGHT_RESEARCH, "thermal_management");
        long t = activate(plain, w);
        assertEquals(ShotResult.Refusal.NOT_UNLOCKED, plain.startBeam(t).refusal());
        Wearer w2 = new Wearer();
        DoomSuit lens = suit("royal_mk2", FLIGHT_RESEARCH, "thermal_management", "gauntlet_focusing");
        t = activate(lens, w2);
        lens.beginCharge(t);
        assertEquals(1.0, lens.chargeProgress(t + 23), 1e-12, "30 x 0.75 rounds to 23 ticks");
        lens.releaseCharge(t + 23);
        assertTrue(lens.startBeam(t + 1).fired());
        assertEquals(0.35, lens.beamMovementFactor());
        double heat0 = lens.heat().heat();
        w2.time = t + 2;
        lens.tick(w2, FlightInput.NONE, Env.ground(), null);
        assertTrue(lens.beaming());
        assertTrue(lens.beamDamage() > 0);
        assertTrue(lens.heat().heat() > heat0 - 1, "beam heats the gauntlets");
        lens.stopBeam();
        assertEquals(0, lens.beamDamage());
    }

    @Test
    void modulesChangeSubsystems() {
        DoomSuit dense = suit("royal_mk2", Set.of("vibranium_lattice"), "capacitor_dense");
        assertEquals(50_000, dense.energy().capacity());
        DoomSuit sphere = suit("royal_mk2", FLIGHT_RESEARCH, "shield_emitter_spherical");
        assertTrue(sphere.shield().config().sphericalUnlocked());
        DoomSuit plain = suit("royal_mk1", Set.of());
        assertFalse(plain.shield().config().sphericalUnlocked());
        DoomSuit directional = suit("royal_mk1", Set.of(), "shield_emitter_directional");
        assertEquals(40 * 1.3, directional.shield().config().capacity(), 1e-9);
    }

    @Test
    void sphericalShieldWorksOnlyWithItsEmitter() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk2", FLIGHT_RESEARCH, "shield_emitter_spherical");
        long t = activate(s, w);
        assertTrue(s.shield().raise(ShieldMode.SPHERICAL, s.energy(), t));
        Wearer w2 = new Wearer();
        DoomSuit p = suit("royal_mk1", Set.of());
        t = activate(p, w2);
        assertFalse(p.shield().raise(ShieldMode.SPHERICAL, p.energy(), t));
    }

    @Test
    void takingArmourOffLowersTheField() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", Set.of());
        long t = activate(s, w);
        assertTrue(s.shield().raise(ShieldMode.DIRECTIONAL, s.energy(), t));
        w.pieces = 3;
        w.time = t + 1;
        s.tick(w, FlightInput.NONE, Env.ground(), null);
        assertFalse(s.shield().isAbsorbing());
    }

    @Test
    void chargersRefillTheCell() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", Set.of());
        long t = activate(s, w);
        s.energy().extract(10_000, false);
        long[] paid = {0};
        RechargeSource cradle = new RechargeSource() {
            @Override public long ratePerTick() { return 500; }
            @Override public void onDelivered(long amount) { paid[0] += amount; }
        };
        long before = s.energy().stored();
        for (int i = 0; i < 10; i++) { w.time = t + i; s.tick(w, FlightInput.NONE, Env.ground(), cradle); }
        assertTrue(s.energy().stored() - before >= 5_000 - 10);
        assertTrue(paid[0] >= 5_000, "the cradle is debited for what it delivered");
    }

    @Test
    void scansAndPulsesAreGated() {
        Wearer w = new Wearer();
        DoomSuit s = suit("royal_mk1", Set.of());
        assertFalse(s.scan(0));
        long t = activate(s, w);
        assertTrue(s.scan(t));
        assertFalse(s.scan(t + 1));
        assertTrue(s.scan(t + 40));
        assertTrue(s.pulse(t));
        assertFalse(s.pulse(t + 159));
    }
}
