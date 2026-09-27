package com.doomsovereign.core.presentation;

import com.doomsovereign.core.flight.FlightEvent;
import com.doomsovereign.core.flight.FlightState;
import com.doomsovereign.core.suit.DoomModeState;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Random;
import java.util.Set;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PresentationTest {
    static Set<String> animations = new HashSet<>();
    static Set<String> sounds = new HashSet<>();
    static Set<String> effects = new HashSet<>();
    static Set<String> bones = new HashSet<>();

    static JsonObject read(Path p) throws IOException {
        return JsonParser.parseString(Files.readString(p, StandardCharsets.UTF_8)).getAsJsonObject();
    }

    @BeforeAll
    static void loadAssets() throws IOException {
        String dir = System.getProperty("doom.assets");
        Assumptions.assumeTrue(dir != null && Files.isDirectory(Path.of(dir)), "generated assets not present");
        Path a = Path.of(dir);
        animations.addAll(read(a.resolve("geckolib/animations/armor/royal_armor.animation.json")).getAsJsonObject("animations").keySet());
        for (String k : read(a.resolve("sounds.json")).keySet()) sounds.add(Cue.NAMESPACE + ":" + k);
        read(a.resolve("vfx/effects.json")).getAsJsonArray("effects")
                .forEach(e -> effects.add(Cue.NAMESPACE + ":" + e.getAsJsonObject().get("id").getAsString()));
        read(a.resolve("geckolib/models/armor/royal_armor.geo.json")).getAsJsonArray("minecraft:geometry").get(0).getAsJsonObject()
                .getAsJsonArray("bones").forEach(b -> bones.add(b.getAsJsonObject().get("name").getAsString()));
    }

    @Test
    void everyCueResolvesToARealAsset() {
        for (Cue c : Cue.values()) {
            if (c.animation() != null) assertTrue(animations.contains(c.animation()), c + " clip " + c.animation());
            if (c.sound() != null) assertTrue(sounds.contains(c.sound()), c + " sound " + c.sound());
            if (c.effect() != null) assertTrue(effects.contains(c.effect()), c + " effect " + c.effect());
            if (c.locator() != null) assertTrue(bones.contains(c.locator()), c + " locator " + c.locator());
            assertTrue(c.animation() != null || c.sound() != null || c.effect() != null, c + " presents nothing");
        }
    }

    @Test
    void basicSelections() {
        ArmorAnimationState s = ArmorAnimationState.standing();
        assertNull(ArmorAnimationSelector.select(s.with(DoomModeState.INACTIVE, false)), "vanilla animation outside Doom Mode");
        assertEquals("animation.royal_armor.armor_initialization", ArmorAnimationSelector.select(s.with(DoomModeState.INITIALISING, true)));
        assertEquals("animation.royal_armor.mask_seal", ArmorAnimationSelector.select(s.with(DoomModeState.INITIALISING, false)));
        assertEquals("animation.royal_armor.idle_armored", ArmorAnimationSelector.select(s));
        assertEquals("animation.royal_armor.idle_authoritative", ArmorAnimationSelector.select(s.idleFor(400)));
        assertEquals("animation.royal_armor.idle_arms_behind_back", ArmorAnimationSelector.select(s.idleFor(5000)));
        assertEquals("animation.royal_armor.walk", ArmorAnimationSelector.select(s.moving(0.1, false)));
        assertEquals("animation.royal_armor.sprint", ArmorAnimationSelector.select(s.moving(0.1, true)));
        assertEquals("animation.royal_armor.falling", ArmorAnimationSelector.select(s.airborne(-1.0)));
        assertEquals("animation.royal_armor.crouch", ArmorAnimationSelector.select(s.combat(false, false, false, true)));
        assertEquals("animation.royal_armor.sustained_beam", ArmorAnimationSelector.select(s.combat(true, true, false, false)));
    }

    @Test
    void flightSelections() {
        ArmorAnimationState s = ArmorAnimationState.standing();
        assertEquals("animation.royal_armor.hover", ArmorAnimationSelector.select(s.withFlight(FlightState.HOVER, 0, 0, 0)));
        assertEquals("animation.royal_armor.vertical_ascent", ArmorAnimationSelector.select(s.withFlight(FlightState.HOVER, 0, 0, 0.3)));
        assertEquals("animation.royal_armor.controlled_descent", ArmorAnimationSelector.select(s.withFlight(FlightState.HOVER, 0, 0, -0.3)));
        assertEquals("animation.royal_armor.forward_flight", ArmorAnimationSelector.select(s.withFlight(FlightState.FLIGHT, 1, 0.2, 0)));
        assertEquals("animation.royal_armor.strafe_left", ArmorAnimationSelector.select(s.withFlight(FlightState.FLIGHT, 0, -1, 0)));
        assertEquals("animation.royal_armor.strafe_right", ArmorAnimationSelector.select(s.withFlight(FlightState.FLIGHT, 0.1, 1, 0)));
        assertEquals("animation.royal_armor.boosted_flight", ArmorAnimationSelector.select(s.withFlight(FlightState.BOOST, 1, 0, 0)));
        assertEquals("animation.royal_armor.controlled_descent", ArmorAnimationSelector.select(s.withFlight(FlightState.LOW_ENERGY_DESCENT, 0, 0, -0.3)));
    }

    @Test
    void flightEventsMapToCues() {
        assertEquals(Cue.HARD_LANDING, ArmorAnimationSelector.cueFor(FlightEvent.HARD_LANDING));
        assertNull(ArmorAnimationSelector.cueFor(FlightEvent.REFUSED_LOCKED));
        for (FlightEvent e : FlightEvent.values()) assertDoesNotThrow(() -> ArmorAnimationSelector.cueFor(e));
    }

    /** Property test: any state selects either vanilla (null) or a clip that exists in the generated library. */
    @Test
    void randomStatesAlwaysSelectAnExistingClip() {
        Random r = new Random(5);
        for (int i = 0; i < 20_000; i++) {
            ArmorAnimationState s = new ArmorAnimationState(DoomModeState.values()[r.nextInt(4)], r.nextBoolean(),
                    FlightState.values()[r.nextInt(FlightState.values().length)], r.nextBoolean(), r.nextDouble() * 0.5,
                    r.nextDouble() * 2 - 1, r.nextDouble() * 2 - 1, r.nextDouble() * 2 - 1, r.nextBoolean(), r.nextBoolean(),
                    r.nextBoolean(), r.nextBoolean(), r.nextBoolean(), r.nextInt(3000));
            String clip = ArmorAnimationSelector.select(s);
            if (s.mode() == DoomModeState.INACTIVE) assertNull(clip);
            else assertTrue(animations.contains(clip), "selected missing clip " + clip + " for " + s);
        }
    }
}
