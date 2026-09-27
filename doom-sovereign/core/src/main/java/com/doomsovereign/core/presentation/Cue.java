package com.doomsovereign.core.presentation;

/**
 * A gameplay moment with a fixed presentation. {@code clip} is a one-shot overlay animation (may be
 * null), {@code sound} a sound event, {@code effect} a VFX effect id (see docs/VFX.md), {@code locator}
 * the bone the effect attaches to.
 */
public enum Cue {
    DOOM_MODE_FIRST_EQUIP("armor_initialization", null, null, null),
    MASK_SEAL("mask_seal", "mask.seal", null, null),
    SHUTDOWN("shutdown_low_power", "armor.shutdown", null, null),
    TAKEOFF("takeoff", "flight.thruster_ignition", "repulsor_burst", "right_boot_knee"),
    IGNITION_MIDAIR(null, "flight.thruster_ignition", "repulsor_burst", "right_palm_emitter"),
    BOOST_ENGAGED(null, "flight.boost", "repulsor_trail_boost", "right_boot_knee"),
    BRAKING("braking", null, null, null),
    SOFT_LANDING(null, "armor.step_heavy", null, null),
    HARD_LANDING("hard_landing", "armor.impact_heavy", "landing_shockwave", "armorRightBoot"),
    FALL_ARRESTED(null, "flight.thruster_ignition", "repulsor_burst", "right_boot_knee"),
    LOW_ENERGY(null, "armor.servo", null, null),
    BOLT_LEFT("energy_blast_left", "gauntlet.discharge", "gauntlet_muzzle", "left_palm_emitter"),
    BOLT_RIGHT("energy_blast_right", "gauntlet.discharge", "gauntlet_muzzle", "right_palm_emitter"),
    CHARGE_BEGIN(null, "gauntlet.charge", "gauntlet_charge", "right_palm_emitter"),
    CHARGED_RELEASE("charged_blast", "gauntlet.heavy_blast", "gauntlet_heavy_muzzle", "right_palm_emitter"),
    BEAM_START(null, "gauntlet.beam_loop", "beam", "right_palm_emitter"),
    FIELD_RAISED("force_field_activation", "field.activate", "field_raise", "armorBody"),
    FIELD_HIT("shield_impact_reaction", "field.impact", "field_impact", "armorBody"),
    FIELD_COLLAPSED(null, "field.collapse", "field_collapse", "armorBody"),
    SCAN("scan", "scan.pulse", "scan_sweep", "right_palm_emitter"),
    OVERRIDE("tech_override", "tech.override", null, null),
    SPELL_CAST("spell_cast", "sorcery.arcane_cast", "arcane_sigil", "right_palm_emitter"),
    RITUAL("ritual_channel", "sorcery.ritual_resonance", "ritual_motes", "armorBody"),
    TELEPORT("teleport_cast", "sorcery.teleport", "teleport_flash", "armorBody"),
    BOT_COMMAND("doombot_command", null, null, null),
    MELEE_LIGHT("light_melee", "armor.servo", null, null),
    MELEE_HEAVY("heavy_punch", "armor.impact_heavy", null, null),
    BACKHAND("backhand", "armor.servo", null, null),
    GROUND_SLAM("ground_slam", "armor.impact_heavy", "landing_shockwave", "armorBody"),
    TIME_PLATFORM_CHARGE(null, "time_platform.charge", "time_platform_charge", null),
    TIME_PLATFORM_DISCHARGE(null, "time_platform.discharge", null, null);

    public static final String NAMESPACE = "doom_sovereign";
    public static final String ARMOR_ANIMATION_PREFIX = "animation.royal_armor.";

    private final String clip;
    private final String sound;
    private final String effect;
    private final String locator;

    Cue(String clip, String sound, String effect, String locator) {
        this.clip = clip;
        this.sound = sound;
        this.effect = effect;
        this.locator = locator;
    }

    /** Full animation name, e.g. {@code animation.royal_armor.takeoff}, or null. */
    public String animation() {
        return clip == null ? null : ARMOR_ANIMATION_PREFIX + clip;
    }

    /** Namespaced sound event id, or null. */
    public String sound() {
        return sound == null ? null : NAMESPACE + ":" + sound;
    }

    /** Namespaced VFX effect id, or null. */
    public String effect() {
        return effect == null ? null : NAMESPACE + ":" + effect;
    }

    public String locator() {
        return locator;
    }
}
