package com.doomsovereign.core.shield;

import com.doomsovereign.core.api.ShieldDamageContext;
import com.doomsovereign.core.api.ShieldDamageContext.DamageKind;
import com.doomsovereign.core.energy.ArmorEnergy;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ShieldModelTest {
    private static ArmorEnergy cell() {
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.insert(e.capacity(), false);
        return e;
    }

    private static ShieldModel raised(ArmorEnergy e) {
        ShieldModel s = ShieldModel.royalMk1();
        assertTrue(s.raise(ShieldMode.DIRECTIONAL, e, 0));
        for (long t = 0; t <= 5; t++) s.tick(e, t);
        assertEquals(ShieldState.ACTIVE, s.state());
        return s;
    }

    private static ShieldDamageContext hit(double amount, DamageKind k, double bearing) {
        return new ShieldDamageContext(amount, k, bearing);
    }

    @Test
    void raisingTakesTimeAndEnergy() {
        ArmorEnergy e = cell();
        long before = e.stored();
        ShieldModel s = ShieldModel.royalMk1();
        s.raise(ShieldMode.DIRECTIONAL, e, 0);
        assertEquals(ShieldState.RAISING, s.state());
        assertFalse(s.isAbsorbing());
        assertEquals(10, s.absorb(hit(10, DamageKind.PROJECTILE, 0), e, 1).passedThrough(), "not absorbing while raising");
        assertTrue(before - e.stored() >= 200);
    }

    @Test
    void cannotRaiseWithoutEnergy() {
        ArmorEnergy e = ArmorEnergy.royalMk1();
        assertFalse(ShieldModel.royalMk1().raise(ShieldMode.DIRECTIONAL, e, 0));
    }

    @Test
    void directionalFieldOnlyCoversItsArc() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        assertTrue(s.absorb(hit(4, DamageKind.PROJECTILE, 30), e, 10).absorbed() > 0);
        AbsorbResult behind = s.absorb(hit(4, DamageKind.PROJECTILE, 170), e, 11);
        assertEquals(0, behind.absorbed());
        assertEquals(4, behind.passedThrough());
        assertTrue(s.covers(-60) && !s.covers(-61) && s.covers(420), "angles normalise");
    }

    @Test
    void absorbedDamageIsPaidForInEnergy() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        long before = e.stored();
        AbsorbResult r = s.absorb(hit(10, DamageKind.ENERGY, 0), e, 10);
        assertEquals(10, r.absorbed(), 1e-9);
        assertEquals(0, r.passedThrough(), 1e-9);
        assertEquals(900, before - e.stored());
        assertTrue(r.ripple() > 0);
    }

    @Test
    void damageKindsInteractDifferently() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        assertEquals(1.0 * 8, s.absorb(hit(8, DamageKind.PROJECTILE, 0), e, 10).absorbed(), 1e-9);
        assertEquals(0.25 * 8, s.absorb(hit(8, DamageKind.ARCANE, 0), e, 11).absorbed(), 1e-9, "sorcery slides through technology");
        assertEquals(0, s.absorb(hit(8, DamageKind.UNBLOCKABLE, 0), e, 12).absorbed());
        assertEquals(0, s.absorb(hit(8, DamageKind.ENVIRONMENTAL, 0), e, 13).absorbed());
        s.setArcaneInsulation(0.5);
        assertEquals(0.75 * 8, s.absorb(hit(8, DamageKind.ARCANE, 0), e, 14).absorbed(), 1e-9, "insulation helps");
        assertThrows(IllegalArgumentException.class, () -> s.setEfficiency(DamageKind.UNBLOCKABLE, 0.5));
    }

    @Test
    void depletionCollapsesTheFieldAndLocksItOut() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        double absorbedTotal = 0;
        long t = 10;
        while (s.isAbsorbing()) {
            absorbedTotal += s.absorb(hit(6, DamageKind.PROJECTILE, 0), e, t).absorbed();
            t++;
        }
        assertEquals(ShieldState.COLLAPSED, s.state());
        assertEquals(20, absorbedTotal, 1e-6, "absorbed exactly its starting charge (half of 40)");
        assertFalse(s.raise(ShieldMode.DIRECTIONAL, e, t + 50));
        for (long k = t; k <= t + 100; k++) s.tick(e, k);
        assertEquals(ShieldState.OFF, s.state());
        assertTrue(s.raise(ShieldMode.DIRECTIONAL, e, t + 101));
    }

    @Test
    void aSingleHugeHitOverloadsAndLocksOutLonger() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        for (long t = 6; t < 400; t++) s.tick(e, t);
        AbsorbResult r = s.absorb(hit(40, DamageKind.KINETIC, 0), e, 400);
        // 40 kinetic x 0.85 = 34 >= 75% of 40 capacity
        assertTrue(r.collapsed());
        assertTrue(r.passedThrough() > 0);
        assertEquals(1.0, r.ripple());
        assertEquals(600, s.collapsedUntil(), "overload lockout is 200 ticks");
    }

    @Test
    void fieldFlickersWhenNearlyDepleted() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        s.absorb(hit(12, DamageKind.PROJECTILE, 0), e, 10);
        assertEquals(ShieldState.FAILING, s.state());
        assertTrue(s.isAbsorbing());
    }

    @Test
    void rechargesAfterQuietPeriod() {
        ArmorEnergy e = cell();
        ShieldModel s = raised(e);
        s.absorb(hit(10, DamageKind.PROJECTILE, 0), e, 10);
        double c = s.charge();
        for (long t = 11; t < 70; t++) s.tick(e, t);
        assertEquals(c, s.charge(), 1e-9, "no recharge within 60 ticks of a hit");
        for (long t = 70; t < 400; t++) s.tick(e, t);
        assertEquals(40, s.charge(), 1e-9);
    }

    @Test
    void upkeepFailureCollapsesTheField() {
        ArmorEnergy e = ArmorEnergy.royalMk1();
        e.insert(300, false);
        ShieldModel s = ShieldModel.royalMk1();
        assertTrue(s.raise(ShieldMode.DIRECTIONAL, e, 0));
        long t = 0;
        while (s.state() != ShieldState.COLLAPSED && t < 10_000) s.tick(e, t++);
        assertEquals(ShieldState.COLLAPSED, s.state());
        assertEquals(0, e.stored());
    }

    @Test
    void sphericalModeIsGatedAndCoversEverything() {
        ArmorEnergy e = cell();
        assertFalse(ShieldModel.royalMk1().raise(ShieldMode.SPHERICAL, e, 0));
        ShieldModel s = new ShieldModel(ShieldConfig.royalMk1().withSpherical(true));
        assertTrue(s.raise(ShieldMode.SPHERICAL, e, 0));
        for (long t = 0; t <= 5; t++) s.tick(e, t);
        assertTrue(s.absorb(hit(3, DamageKind.PROJECTILE, 180), e, 10).absorbed() > 0);
        long before = e.stored();
        s.absorb(hit(5, DamageKind.PROJECTILE, 90), e, 11);
        assertEquals((long) Math.ceil(5 * 90 * 1.6), before - e.stored(), "spherical absorption costs more");
    }
}
