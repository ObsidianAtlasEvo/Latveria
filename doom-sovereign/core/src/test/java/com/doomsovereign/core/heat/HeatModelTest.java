package com.doomsovereign.core.heat;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class HeatModelTest {
    @Test
    void thresholdsProgressInOrder() {
        HeatModel h = HeatModel.royalGauntlets();
        assertEquals(HeatState.NOMINAL, h.state());
        h.addHeat(50);
        assertEquals(HeatState.WARNING, h.state());
        assertEquals(1.0, h.outputFactor());
        h.addHeat(25);
        assertEquals(HeatState.THROTTLED, h.state());
        assertTrue(h.outputFactor() < 1.0 && h.outputFactor() > 0.35);
        h.addHeat(25);
        assertEquals(HeatState.LOCKED, h.state());
        assertFalse(h.canFire());
        assertEquals(0, h.outputFactor());
    }

    @Test
    void lockReleasesOnlyBelowRecoveryThreshold() {
        HeatModel h = HeatModel.royalGauntlets();
        h.addHeat(200);
        assertEquals(100, h.heat(), "heat is capped at max, never destroys the suit");
        int ticks = 0;
        while (h.locked()) {
            h.tick(0);
            ticks++;
            if (h.locked()) assertTrue(h.heat() > h.recovery());
        }
        assertEquals(240, ticks, "(100-40)/0.25 ticks at passive cooling");
        assertTrue(h.canFire());
        assertEquals(HeatState.NOMINAL, h.state());
    }

    @Test
    void throttleFactorIsMonotonic() {
        HeatModel h = HeatModel.royalGauntlets();
        double prev = 1.0;
        for (int i = 0; i < 99; i++) {
            h.addHeat(1);
            double f = h.outputFactor();
            assertTrue(f <= prev + 1e-12);
            prev = f;
        }
        assertEquals(1 - 0.65 * 29.0 / 30.0, prev, 1e-9, "99 heat is 29/30 of the way from throttle to critical");
        h.addHeat(1);
        assertEquals(0, h.outputFactor(), "reaching critical locks the gauntlets");
    }

    @Test
    void activeCoolingStartsAfterADelay() {
        HeatModel h = HeatModel.royalGauntlets();
        h.setActiveCoolingPerTick(1.0);
        h.addHeat(60);
        for (int i = 0; i < 20; i++) h.tick(0);
        assertEquals(60 - 20 * 0.25, h.heat(), 1e-9, "only passive cooling during the delay");
        h.tick(0);
        assertEquals(60 - 21 * 0.25 - 1.0, h.heat(), 1e-9);
    }

    @Test
    void environmentCoolingHelpsAndNeverHeats() {
        HeatModel h = HeatModel.royalGauntlets();
        h.addHeat(10);
        h.tick(-5);
        assertEquals(9.75, h.heat(), 1e-9, "negative environment bonus ignored");
        h.tick(2);
        assertEquals(7.5, h.heat(), 1e-9);
    }

    @Test
    void ticksToUnlockPredictsTheHud() {
        HeatModel h = HeatModel.royalGauntlets();
        h.addHeat(100);
        int predicted = h.ticksToUnlock();
        int actual = 0;
        while (h.locked()) { h.tick(0); actual++; }
        assertEquals(predicted, actual);
    }

    @Test
    void restoreSanitises() {
        HeatModel h = HeatModel.royalGauntlets();
        h.restore(Double.NaN, true);
        assertEquals(0, h.heat());
        assertFalse(h.locked(), "a lock below the recovery threshold is not restored");
        h.restore(500, true);
        assertEquals(100, h.heat());
        assertTrue(h.locked());
    }

    @Test
    void invalidConfigurationRejected() {
        assertThrows(IllegalArgumentException.class, () -> new HeatModel(100, 80, 70, 100, 40, 0.3, 0.2, 0, 10));
        assertThrows(IllegalArgumentException.class, () -> new HeatModel(100, 50, 70, 100, 100, 0.3, 0.2, 0, 10));
        assertThrows(IllegalArgumentException.class, () -> HeatModel.royalGauntlets().addHeat(-1));
    }
}
