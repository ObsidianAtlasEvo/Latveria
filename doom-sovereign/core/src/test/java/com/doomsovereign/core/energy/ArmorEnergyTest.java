package com.doomsovereign.core.energy;

import org.junit.jupiter.api.Test;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

class ArmorEnergyTest {
    private static ArmorEnergy full() {
        ArmorEnergy e = new ArmorEnergy(10_000, 5, 0.10, 0.25, 60);
        e.insert(10_000, false);
        return e;
    }

    @Test
    void randomisedOperationsConserveEnergyAndStayInBounds() {
        Random r = new Random(42);
        for (int run = 0; run < 50; run++) {
            ArmorEnergy e = new ArmorEnergy(1 + r.nextInt(50_000), r.nextInt(10), r.nextDouble() * 0.3, 0.35, r.nextInt(80));
            long now = 0;
            RechargeSource charger = () -> 17;
            for (int i = 0; i < 5_000; i++) {
                DrainCategory c = DrainCategory.values()[r.nextInt(DrainCategory.values().length)];
                switch (r.nextInt(6)) {
                    case 0 -> e.tryConsume(c, r.nextInt(3_000), now);
                    case 1 -> e.drain(c, r.nextInt(500), now);
                    case 2 -> e.insert(r.nextInt(2_000), r.nextBoolean());
                    case 3 -> e.extract(r.nextInt(2_000), r.nextBoolean());
                    case 4 -> e.tick(now, r.nextBoolean() ? charger : null);
                    default -> e.setCostMultiplier(c, 0.25 + r.nextDouble() * 3);
                }
                now += r.nextInt(3);
                assertTrue(e.stored() >= 0, "never negative");
                assertTrue(e.stored() <= e.capacity(), "never above capacity");
                assertEquals(e.stored(), e.totalReceived() + e.totalRegenerated() - e.totalConsumed(), "conservation");
            }
        }
    }

    @Test
    void weaponsCannotTouchTheReserveButTheShieldCan() {
        ArmorEnergy e = full();
        assertEquals(1_000, e.reserve());
        assertTrue(e.tryConsume(DrainCategory.WEAPON, 9_000, 0));
        assertEquals(1_000, e.stored());
        assertFalse(e.tryConsume(DrainCategory.WEAPON, 1, 1), "reserve is off limits to weapons");
        assertFalse(e.tryConsume(DrainCategory.FLIGHT, 1, 1));
        assertEquals(EnergyStatus.RESERVE, e.status());
        assertTrue(e.tryConsume(DrainCategory.SHIELD, 600, 2));
        assertTrue(e.tryConsume(DrainCategory.EMERGENCY, 400, 2));
        assertEquals(EnergyStatus.DEPLETED, e.status());
    }

    @Test
    void tryConsumeIsAllOrNothing() {
        ArmorEnergy e = full();
        e.tryConsume(DrainCategory.WEAPON, 8_950, 0);
        long before = e.stored();
        assertFalse(e.tryConsume(DrainCategory.WEAPON, 100, 0));
        assertEquals(before, e.stored(), "a refused shot costs nothing");
    }

    @Test
    void partialDrainReportsDeliveredFraction() {
        ArmorEnergy e = full();
        e.tryConsume(DrainCategory.WEAPON, 8_900, 0);
        assertEquals(1_100, e.stored());
        double got = e.drain(DrainCategory.FLIGHT, 400, 0);
        assertEquals(0.25, got, 1e-9);
        assertEquals(1_000, e.stored());
    }

    @Test
    void regenerationWaitsForTheIdleDelay() {
        ArmorEnergy e = full();
        e.tryConsume(DrainCategory.WEAPON, 5_000, 100);
        for (long t = 101; t < 160; t++) e.tick(t, null);
        assertEquals(5_000, e.stored(), "no regen within 60 ticks of a drain");
        e.tick(160, null);
        assertEquals(5_005, e.stored());
        long ticks = 0;
        for (long t = 161; e.stored() < e.capacity(); t++, ticks++) e.tick(t, null);
        assertEquals(10_000, e.stored());
        assertEquals(999, ticks);
    }

    @Test
    void passiveDrainDoesNotResetTheRegenTimer() {
        ArmorEnergy e = full();
        e.tryConsume(DrainCategory.WEAPON, 1_000, 0);
        e.tryConsume(DrainCategory.PASSIVE, 1, 50);
        e.tick(60, null);
        assertEquals(9_004, e.stored());
    }

    @Test
    void chargerIsDebitedForWhatItDelivers() {
        ArmorEnergy e = new ArmorEnergy(1_000, 0, 0, 0.2, 0);
        long[] delivered = {0};
        RechargeSource cradle = new RechargeSource() {
            @Override public long ratePerTick() { return 300; }
            @Override public void onDelivered(long amount) { delivered[0] += amount; }
        };
        for (int i = 0; i < 5; i++) e.tick(i, cradle);
        assertEquals(1_000, e.stored());
        assertEquals(1_000, delivered[0], "charger only pays for energy actually accepted");
    }

    @Test
    void shrinkingCapacityDestroysExcessRatherThanInventingIt() {
        ArmorEnergy e = full();
        e.setCapacity(4_000);
        assertEquals(4_000, e.stored());
        assertEquals(e.stored(), e.totalReceived() + e.totalRegenerated() - e.totalConsumed());
        e.setCapacity(20_000);
        assertEquals(4_000, e.stored(), "growing capacity adds no energy");
    }

    @Test
    void multipliersRoundCostsUp() {
        ArmorEnergy e = full();
        e.setCostMultiplier(DrainCategory.WEAPON, 0.9);
        assertEquals(1, e.effectiveCost(DrainCategory.WEAPON, 1), "never free by rounding");
        assertEquals(226, e.effectiveCost(DrainCategory.WEAPON, 251));
        assertThrows(IllegalArgumentException.class, () -> e.setCostMultiplier(DrainCategory.WEAPON, 0));
    }

    @Test
    void statusBands() {
        ArmorEnergy e = full();
        assertEquals(EnergyStatus.NOMINAL, e.status());
        e.tryConsume(DrainCategory.SHIELD, 7_500, 0);
        assertEquals(EnergyStatus.LOW, e.status());
        e.tryConsume(DrainCategory.SHIELD, 1_500, 0);
        assertEquals(EnergyStatus.RESERVE, e.status());
    }

    @Test
    void royalMk1BudgetSupportsUsefulFlight() {
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.insert(e.capacity(), false);
        long cruise = e.sustainTicks(DrainCategory.FLIGHT, DrainTable.CRUISE_PER_TICK);
        assertTrue(cruise >= 20 * 120, "at least two minutes of cruise: " + cruise);
        long hover = e.sustainTicks(DrainCategory.FLIGHT, DrainTable.HOVER_PER_TICK);
        assertTrue(hover >= 20 * 60 * 7, "at least seven minutes of hover: " + hover);
        assertTrue(e.spendable(DrainCategory.WEAPON) / DrainTable.BOLT >= 70, "70+ bolts");
    }

    @Test
    void restoreClampsUntrustedValues() {
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.restore(-50, 0);
        assertEquals(0, e.stored());
        e.restore(Long.MAX_VALUE, 0);
        assertEquals(e.capacity(), e.stored());
    }

    @Test
    void flightCostGrowsWithSpeedAndAcceleration() {
        long hover = DrainTable.flightCost(0, 0.55, 0, false);
        long cruise = DrainTable.flightCost(0.55, 0.55, 0, false);
        long accel = DrainTable.flightCost(0.3, 0.55, 0.035, false);
        long boost = DrainTable.flightCost(1.1, 0.55, 0, true);
        assertEquals(DrainTable.HOVER_PER_TICK, hover);
        assertEquals(DrainTable.CRUISE_PER_TICK, cruise);
        assertTrue(accel > DrainTable.flightCost(0.3, 0.55, 0, false));
        assertTrue(boost >= DrainTable.BOOST_PER_TICK);
    }
}
