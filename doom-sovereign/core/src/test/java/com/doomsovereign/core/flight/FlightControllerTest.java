package com.doomsovereign.core.flight;

import com.doomsovereign.core.energy.ArmorEnergy;
import com.doomsovereign.core.support.Fakes.Env;
import java.util.Random;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class FlightControllerTest {
    private static ArmorEnergy full() {
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.insert(e.capacity(), false);
        return e;
    }

    /** Takes off from the ground and runs until hovering. Returns the next tick number. */
    private static long airborne(FlightController fc, ArmorEnergy e) {
        Env ground = Env.ground();
        FlightOutput o = fc.tick(FlightInput.togglePress(), ground, e, 0);
        assertEquals(FlightState.TAKEOFF, o.state());
        assertTrue(o.events().contains(FlightEvent.TAKEOFF));
        Env air = Env.air();
        long t = 1;
        while (fc.state() == FlightState.TAKEOFF) fc.tick(FlightInput.NONE, air, e, t++);
        assertEquals(FlightState.HOVER, fc.state());
        return t;
    }

    @Test
    void flightMustBeEarned() {
        FlightController fc = new FlightController(FlightProfile.locked());
        FlightOutput o = fc.tick(FlightInput.togglePress(), Env.ground(), full(), 0);
        assertEquals(FlightState.GROUNDED, o.state());
        assertTrue(o.events().contains(FlightEvent.REFUSED_LOCKED));
        assertFalse(o.overridesGravity());
    }

    @Test
    void takeoffNeedsEnergy() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        FlightOutput o = fc.tick(FlightInput.togglePress(), Env.ground(), ArmorEnergy.royalMk1(), 0);
        assertEquals(FlightState.GROUNDED, o.state());
        assertTrue(o.events().contains(FlightEvent.REFUSED_NO_ENERGY));
    }

    @Test
    void takeoffIsAShortFixedLiftThenHover() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        FlightOutput first = fc.tick(FlightInput.togglePress(), Env.ground(), e, 0);
        assertTrue(first.verticalSpeed() > 0.4);
        assertTrue(first.energyDrained() >= 60, "takeoff burst");
        int ticks = 0;
        double prevLift = Double.MAX_VALUE;
        while (fc.state() == FlightState.TAKEOFF) {
            FlightOutput o = fc.tick(FlightInput.NONE, Env.air(), e, 1 + ticks);
            if (o.state() == FlightState.TAKEOFF) {
                assertTrue(o.verticalSpeed() > 0 && o.verticalSpeed() <= prevLift + 1e-12, "lift tapers");
                prevLift = o.verticalSpeed();
            }
            ticks++;
        }
        assertEquals(FlightController.TAKEOFF_TICKS, ticks);
        assertEquals(FlightState.HOVER, fc.state());
    }

    @Test
    void speedRampsToCruiseAndNeverPastIt() {
        FlightProfile p = FlightProfile.royalMk1();
        FlightController fc = new FlightController(p);
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        Env air = Env.air();
        FlightOutput o = fc.tick(FlightInput.move(1, 0), air, e, t++);
        assertEquals(FlightState.FLIGHT, o.state());
        double prev = 0;
        int ticksToCruise = -1;
        for (int i = 0; i < 60; i++) {
            o = fc.tick(FlightInput.move(1, 0), air, e, t++);
            assertTrue(o.forwardSpeed() - prev <= p.acceleration() + 1e-12, "no instant top speed");
            assertTrue(o.forwardSpeed() <= p.cruiseSpeed() + 1e-12);
            if (ticksToCruise < 0 && Math.abs(o.forwardSpeed() - p.cruiseSpeed()) < 1e-12) ticksToCruise = i + 1;
            prev = o.forwardSpeed();
        }
        assertEquals((int) Math.ceil(p.cruiseSpeed() / p.acceleration()), ticksToCruise);
        assertTrue(o.leanDegrees() > 0 && o.leanDegrees() <= FlightController.MAX_LEAN);
    }

    @Test
    void releasingMovementBrakesBackToHover() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        Env air = Env.air();
        for (int i = 0; i < 30; i++) fc.tick(FlightInput.move(1, 0), air, e, t++);
        FlightOutput o = fc.tick(FlightInput.NONE, air, e, t++);
        assertEquals(FlightState.BRAKE, o.state());
        assertTrue(o.events().contains(FlightEvent.BRAKING));
        int guard = 0;
        while (fc.state() == FlightState.BRAKE && guard++ < 100) fc.tick(FlightInput.NONE, air, e, t++);
        assertEquals(FlightState.HOVER, fc.state());
        assertEquals(0, fc.speed());
    }

    @Test
    void boostIsGatedByTheProfile() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        Env air = Env.air();
        for (int i = 0; i < 80; i++) {
            FlightOutput o = fc.tick(FlightInput.move(1, 0).withBoost(), air, e, t++);
            assertNotEquals(FlightState.BOOST, o.state());
            assertTrue(o.forwardSpeed() <= 0.55 + 1e-12);
        }
        fc.setProfile(FlightProfile.royalMk1().withBoost(true));
        FlightOutput o = fc.tick(FlightInput.move(1, 0).withBoost(), air, e, t++);
        assertEquals(FlightState.BOOST, o.state());
        assertTrue(o.events().contains(FlightEvent.BOOST_ENGAGED));
        for (int i = 0; i < 80; i++) o = fc.tick(FlightInput.move(1, 0).withBoost(), air, e, t++);
        assertEquals(1.1, o.forwardSpeed(), 1e-9);
        assertTrue(o.energyDrained() >= 25, "boost is expensive");
        assertEquals(1.0, o.thrust());
        fc.setProfile(FlightProfile.royalMk1());
        assertEquals(FlightState.FLIGHT, fc.state(), "losing the boost module drops out of boost");
    }

    @Test
    void strafingRollsTowardTheStrafe() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        FlightOutput o = null;
        for (int i = 0; i < 30; i++) o = fc.tick(FlightInput.move(0, -1), Env.air(), e, t++);
        assertTrue(o.strafeSpeed() < 0 && o.rollDegrees() < 0);
        for (int i = 0; i < 60; i++) o = fc.tick(FlightInput.move(0, 1), Env.air(), e, t++);
        assertTrue(o.strafeSpeed() > 0 && o.rollDegrees() > 0);
        assertTrue(Math.abs(o.rollDegrees()) <= FlightController.MAX_ROLL + 1e-9);
    }

    @Test
    void disengagingDescendsAndLandsSoftly() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        FlightOutput o = fc.tick(FlightInput.togglePress(), Env.air(), e, t++);
        assertEquals(FlightState.DESCENT, o.state());
        assertTrue(o.events().contains(FlightEvent.DISENGAGED));
        o = fc.tick(FlightInput.NONE, Env.air(), e, t++);
        assertEquals(-FlightController.DESCENT_RATE, o.verticalSpeed(), 1e-12);
        o = fc.tick(FlightInput.NONE, Env.ground(), e, t++);
        assertEquals(FlightState.LANDING, o.state());
        assertTrue(o.events().contains(FlightEvent.SOFT_LANDING));
        assertTrue(o.landingImpact() > 0 && o.landingImpact() < 0.5);
        for (int i = 0; i < FlightController.LANDING_TICKS; i++) o = fc.tick(FlightInput.NONE, Env.ground(), e, t++);
        assertEquals(FlightState.GROUNDED, o.state());
        assertFalse(o.overridesGravity());
    }

    @Test
    void fastDescentIntoTheGroundIsAHardLanding() {
        FlightProfile fast = FlightProfile.royalMk1().withBoost(true).withSpeeds(1.2, 2.0, 0.1);
        FlightController fc = new FlightController(fast);
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        for (int i = 0; i < 40; i++) fc.tick(FlightInput.move(1, 0).withBoost().withDescend(), Env.air(), e, t++);
        FlightOutput o = fc.tick(FlightInput.move(1, 0).withBoost().withDescend(), Env.ground(), e, t++);
        assertEquals(FlightState.LANDING, o.state());
        assertTrue(o.events().contains(FlightEvent.HARD_LANDING));
        assertTrue(o.landingImpact() > 0.5);
    }

    @Test
    void dangerousFallsAreArrested() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        Env falling = Env.air();
        falling.fall = 10;
        falling.vy = -1.2;
        long before = e.stored();
        FlightOutput o = fc.tick(FlightInput.NONE, falling, e, 0);
        assertEquals(FlightState.FALL_ARREST, o.state());
        assertTrue(o.events().contains(FlightEvent.FALL_ARRESTED));
        assertTrue(before - e.stored() >= 400);
        double prev = o.verticalSpeed();
        for (int i = 1; i <= FlightController.ARREST_TICKS; i++) {
            o = fc.tick(FlightInput.NONE, falling, e, i);
            assertTrue(o.verticalSpeed() >= prev - 1e-12, "fall slows every tick");
            prev = o.verticalSpeed();
        }
        assertEquals(0, prev, 1e-12);
        assertEquals(FlightState.HOVER, fc.state());
    }

    @Test
    void fallArrestRespectsItsConditions() {
        Env shortFall = Env.air();
        shortFall.fall = 3;
        shortFall.vy = -1.2;
        assertEquals(FlightState.GROUNDED, new FlightController(FlightProfile.royalMk1()).tick(FlightInput.NONE, shortFall, full(), 0).state());
        Env water = Env.air();
        water.fall = 20;
        water.vy = -1.2;
        water.fluid = true;
        assertEquals(FlightState.GROUNDED, new FlightController(FlightProfile.royalMk1()).tick(FlightInput.NONE, water, full(), 0).state());
        Env deep = Env.air();
        deep.fall = 20;
        deep.vy = -1.2;
        assertEquals(FlightState.GROUNDED, new FlightController(FlightProfile.locked()).tick(FlightInput.NONE, deep, full(), 0).state(),
                "no dampener, no arrest");
    }

    @Test
    void ignitingInMidAirGoesStraightToHover() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        FlightOutput o = fc.tick(FlightInput.togglePress(), Env.air(), full(), 0);
        assertEquals(FlightState.HOVER, o.state());
        assertTrue(o.events().contains(FlightEvent.IGNITION_MIDAIR));
    }

    @Test
    void runningDryForcesAGentleDescentNotAFall() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.insert(e.reserve() + 400, false);
        long t = airborne(fc, e);
        FlightOutput o = null;
        boolean sawLow = false;
        for (int i = 0; i < 2000 && !sawLow; i++) {
            o = fc.tick(FlightInput.move(1, 0), Env.air(), e, t++);
            sawLow = o.events().contains(FlightEvent.LOW_ENERGY);
        }
        assertTrue(sawLow);
        assertEquals(FlightState.LOW_ENERGY_DESCENT, o.state());
        assertEquals(-FlightController.LOW_ENERGY_DESCENT_RATE, o.verticalSpeed(), 1e-12);
        assertTrue(e.stored() <= e.reserve(), "normal flight never dips into the reserve");
        o = fc.tick(FlightInput.move(1, 0).withAscend(), Env.air(), e, t++);
        assertEquals(FlightState.LOW_ENERGY_DESCENT, o.state(), "cannot climb out of an emergency descent");
        o = fc.tick(FlightInput.NONE, Env.ground(), e, t++);
        assertEquals(FlightState.LANDING, o.state());
    }

    @Test
    void emergencyPowerEventuallyRunsOut() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.insert(e.reserve() + 200, false);
        long t = airborne(fc, e);
        FlightOutput o = null;
        for (int i = 0; i < 10_000 && fc.state() != FlightState.GROUNDED; i++) o = fc.tick(FlightInput.move(1, 0), Env.air(), e, t++);
        assertEquals(FlightState.GROUNDED, fc.state());
        assertTrue(o.events().contains(FlightEvent.POWER_LOST));
        assertEquals(0, e.stored());
    }

    @Test
    void shutdownKillsThrust() {
        FlightController fc = new FlightController(FlightProfile.royalMk1());
        ArmorEnergy e = full();
        long t = airborne(fc, e);
        for (int i = 0; i < 20; i++) fc.tick(FlightInput.move(1, 0), Env.air(), e, t++);
        fc.shutdown();
        assertEquals(FlightState.GROUNDED, fc.state());
        assertEquals(0, fc.speed());
    }

    /** Property test: random inputs and terrain never break the controller's invariants. */
    @Test
    void randomisedInputsKeepInvariants() {
        for (int seed = 0; seed < 300; seed++) {
            Random r = new Random(seed);
            FlightProfile p = switch (seed % 3) {
                case 0 -> FlightProfile.royalMk1();
                case 1 -> FlightProfile.royalMk1().withBoost(true);
                default -> FlightProfile.locked();
            };
            FlightController fc = new FlightController(p);
            ArmorEnergy e = ArmorEnergy.royalMk1();
            e.insert(r.nextInt((int) e.capacity() + 1), false);
            Env env = Env.ground();
            for (long t = 0; t < 1500; t++) {
                if (r.nextInt(40) == 0) env.onGround = !env.onGround;
                env.vy = env.onGround ? 0 : -r.nextDouble() * 2;
                env.fall = env.onGround ? 0 : r.nextDouble() * 20;
                env.fluid = r.nextInt(30) == 0;
                FlightInput in = new FlightInput(r.nextInt(25) == 0, r.nextDouble() * 2.4 - 1.2, r.nextDouble() * 2.4 - 1.2,
                        r.nextBoolean(), r.nextInt(4) == 0, r.nextBoolean());
                if (r.nextInt(500) == 0) e.insert(r.nextInt(5000), false);
                long before = e.stored();
                FlightOutput o = fc.tick(in, env, e, t);
                String where = "seed " + seed + " tick " + t;
                assertTrue(e.stored() >= 0, where);
                assertEquals(Math.max(0, before - e.stored()), o.energyDrained(), where);
                assertTrue(fc.speed() >= 0 && fc.speed() <= p.boostSpeed() + 1e-9, where);
                if (!p.boostUnlocked()) {
                    assertNotEquals(FlightState.BOOST, o.state(), where);
                    assertTrue(fc.speed() <= p.cruiseSpeed() + 1e-9, where);
                }
                if (!p.flightUnlocked()) assertFalse(o.state().powered(), where);
                if (o.state() == FlightState.GROUNDED) {
                    assertEquals(0, fc.speed(), where);
                    assertFalse(o.overridesGravity(), where);
                }
                assertTrue(o.thrust() >= 0 && o.thrust() <= 1, where);
                assertTrue(o.landingImpact() >= 0 && o.landingImpact() <= 1, where);
                assertTrue(Double.isNaN(o.verticalSpeed()) || Math.abs(o.verticalSpeed()) <= 2.0 + 1e-9, where);
                assertTrue(Math.abs(o.leanDegrees()) <= FlightController.MAX_LEAN + 1e-9, where);
            }
        }
    }
}
