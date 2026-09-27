package com.doomsovereign.core.focus;

import org.junit.jupiter.api.Test;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

class ArcaneFocusTest {
    private static ArcaneFocus focus() {
        return new ArcaneFocus(100, 0.5, 40, 0.5);
    }

    @Test
    void instantCastSpendsOrRefuses() {
        ArcaneFocus f = focus();
        assertEquals(CastResult.COMPLETED, f.castInstant(30, 0));
        assertEquals(70, f.current(), 1e-9);
        assertEquals(CastResult.INSUFFICIENT_FOCUS, f.castInstant(71, 1));
        assertEquals(70, f.current(), 1e-9, "a refused cast costs nothing");
    }

    @Test
    void channelReservesThenSpendsOnCompletion() {
        ArcaneFocus f = focus();
        assertEquals(CastResult.STARTED, f.beginChannel("ritual", 60, 100, 0));
        assertEquals(40, f.available(), 1e-9, "reserved focus is unavailable to other spells");
        assertEquals(CastResult.INSUFFICIENT_FOCUS, f.castInstant(41, 1));
        assertEquals(CastResult.ALREADY_CHANNELING, f.beginChannel("other", 1, 5, 1));
        for (long t = 1; t < 100; t++) assertEquals(CastResult.STARTED, f.advanceChannel(t));
        assertEquals(0.99, f.channelProgress(99), 1e-9);
        assertEquals(CastResult.COMPLETED, f.advanceChannel(100));
        assertEquals(40, f.current(), 1e-9);
        assertEquals(0, f.reserved(), 1e-9);
    }

    @Test
    void interruptionLosesHalfTheReservation() {
        ArcaneFocus f = focus();
        f.beginChannel("banish", 80, 200, 0);
        assertEquals(CastResult.INTERRUPTED, f.interrupt(50));
        assertEquals(60, f.current(), 1e-9, "half of 80 is lost, the rest returns");
        assertEquals(0, f.reserved(), 1e-9);
        assertFalse(f.channeling());
        assertEquals(CastResult.NOT_CHANNELING, f.interrupt(51));
    }

    @Test
    void noRecoveryWhileChannellingOrDuringTheDelay() {
        ArcaneFocus f = focus();
        f.castInstant(50, 0);
        for (long t = 1; t < 40; t++) f.tick(t);
        assertEquals(50, f.current(), 1e-9);
        f.tick(40);
        assertEquals(50.5, f.current(), 1e-9);
        f.beginChannel("x", 10, 1000, 41);
        for (long t = 41; t < 200; t++) f.tick(t);
        assertEquals(50.5, f.current(), 1e-9);
    }

    @Test
    void bonusesStackAndCapAtCapacity() {
        ArcaneFocus f = focus();
        f.castInstant(90, 0);
        f.setBonus(FocusSource.RITUAL_SITE, 2.0);
        f.setBonus(FocusSource.RELIC, 0.5);
        f.tick(100);
        assertEquals(13, f.current(), 1e-9);
        f.setBonus(FocusSource.RELIC, 0);
        f.tick(101);
        assertEquals(15.5, f.current(), 1e-9);
        f.grant(FocusSource.SUPERNATURAL_KILL, 500);
        assertEquals(100, f.current(), 1e-9);
    }

    @Test
    void randomisedInvariant() {
        Random r = new Random(7);
        ArcaneFocus f = focus();
        long now = 0;
        for (int i = 0; i < 20_000; i++) {
            switch (r.nextInt(6)) {
                case 0 -> f.castInstant(r.nextDouble() * 40, now);
                case 1 -> f.beginChannel("c", r.nextDouble() * 60, 1 + r.nextInt(80), now);
                case 2 -> f.advanceChannel(now);
                case 3 -> f.interrupt(now);
                case 4 -> f.grant(FocusSource.SUCCESSFUL_CAST, r.nextDouble() * 5);
                default -> f.tick(now);
            }
            now += r.nextInt(4);
            assertTrue(f.reserved() >= -1e-9);
            assertTrue(f.reserved() <= f.current() + 1e-9, "cannot reserve more than you have");
            assertTrue(f.current() <= f.capacity() + 1e-9);
            assertTrue(f.current() >= -1e-9);
        }
    }
}
