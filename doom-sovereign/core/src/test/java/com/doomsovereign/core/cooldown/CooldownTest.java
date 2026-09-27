package com.doomsovereign.core.cooldown;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class CooldownTest {
    @Test
    void expiresOnTheExactTick() {
        Cooldown c = Cooldown.of(20);
        assertTrue(c.tryUse(100));
        assertFalse(c.ready(119));
        assertEquals(1, c.remaining(119));
        assertTrue(c.ready(120));
        assertEquals(0, c.remaining(120));
    }

    @Test
    void chargesRegenerateOneAtATime() {
        Cooldown c = new Cooldown(40, 2);
        assertTrue(c.tryUse(0));
        assertTrue(c.tryUse(5));
        assertFalse(c.tryUse(6));
        assertEquals(0, c.charges(39));
        assertEquals(1, c.charges(40));
        assertEquals(1, c.charges(79));
        assertEquals(2, c.charges(80));
        assertEquals(2, c.charges(10_000), "never above max");
    }

    @Test
    void usingDuringRechargeDoesNotRestartIt() {
        Cooldown c = new Cooldown(40, 3);
        c.tryUse(0);
        c.tryUse(10);
        assertEquals(1, c.charges(10));
        assertEquals(2, c.charges(40), "first charge back at 40 regardless of the second use");
    }

    @Test
    void progressSweepsFromZeroToOne() {
        Cooldown c = Cooldown.of(10);
        c.tryUse(0);
        assertEquals(0.0, c.progress(0), 1e-9);
        assertEquals(0.5, c.progress(5), 1e-9);
        assertEquals(1.0, c.progress(10), 1e-9);
    }

    @Test
    void reductionShortensFutureRecharges() {
        Cooldown c = Cooldown.of(100);
        c.setReduction(0.25);
        c.tryUse(0);
        assertFalse(c.ready(74));
        assertTrue(c.ready(75));
        assertThrows(IllegalArgumentException.class, () -> c.setReduction(0.9));
    }

    @Test
    void zeroCooldownIsAlwaysReady() {
        Cooldown c = Cooldown.of(0);
        for (int i = 0; i < 5; i++) assertTrue(c.tryUse(3));
    }

    @Test
    void restoreRoundTrip() {
        Cooldown c = new Cooldown(30, 2);
        c.tryUse(0);
        c.tryUse(1);
        Cooldown d = new Cooldown(30, 2);
        d.restore(c.storedCharges(), c.nextChargeAt());
        for (long t = 0; t < 100; t++) assertEquals(c.charges(t), d.charges(t));
    }

    @Test
    void setRejectsUnknownAbilities() {
        CooldownSet s = new CooldownSet();
        s.define("bolt", 8, 1);
        assertTrue(s.tryUse("bolt", 0));
        assertFalse(s.ready("bolt", 7));
        assertThrows(IllegalArgumentException.class, () -> s.get("nope"));
    }
}
