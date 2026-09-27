package com.doomsovereign.core.presentation;

import com.doomsovereign.core.flight.FlightState;

/**
 * Chooses the looping base clip for the Royal Armor each frame. One-shot overlays (blasts,
 * landings, casts) come from {@link Cue}; this only decides what plays underneath them.
 * Returns null when the vanilla animation should run (armour not in Doom Mode).
 */
public final class ArmorAnimationSelector {
    /** Idle variants rotate in after these many ticks without movement. */
    public static final long AUTHORITATIVE_AFTER = 400;
    public static final long ARMS_BEHIND_BACK_AFTER = 1200;
    public static final double WALK_SPEED = 0.02;
    public static final double SPRINT_SPEED = 0.2;
    public static final double VERTICAL_THRESHOLD = 0.1;

    private ArmorAnimationSelector() {
    }

    public static String select(ArmorAnimationState s) {
        String clip = switch (s.mode()) {
            case INACTIVE -> null;
            case INITIALISING -> s.firstEquip() ? "armor_initialization" : "mask_seal";
            case SHUTTING_DOWN -> "shutdown_low_power";
            case ACTIVE -> active(s);
        };
        return clip == null ? null : Cue.ARMOR_ANIMATION_PREFIX + clip;
    }

    private static String active(ArmorAnimationState s) {
        FlightState f = s.flight();
        switch (f) {
            case TAKEOFF:
                return "takeoff";
            case FALL_ARREST:
                return "hover";
            case HOVER:
                if (s.verticalSpeed() > VERTICAL_THRESHOLD) return "vertical_ascent";
                if (s.verticalSpeed() < -VERTICAL_THRESHOLD) return "controlled_descent";
                return s.aiming() ? "gauntlet_aim" : "hover";
            case FLIGHT:
                if (Math.abs(s.strafeInput()) > Math.abs(s.forwardInput()) + 0.1)
                    return s.strafeInput() > 0 ? "strafe_right" : "strafe_left";
                return "forward_flight";
            case BOOST:
                return "boosted_flight";
            case BRAKE:
                return "braking";
            case DESCENT:
            case LOW_ENERGY_DESCENT:
                return "controlled_descent";
            case LANDING:
            case GROUNDED:
            default:
                break;
        }
        if (s.beaming()) return "sustained_beam";
        if (s.channeling()) return "ritual_channel";
        if (s.aiming()) return "gauntlet_aim";
        if (s.sneaking()) return "crouch";
        if (!s.onGround() && s.verticalSpeed() < -0.5) return "falling";
        if (s.sprinting() || s.horizontalSpeed() > SPRINT_SPEED) return "sprint";
        if (s.horizontalSpeed() > WALK_SPEED) return "walk";
        if (s.idleTicks() >= ARMS_BEHIND_BACK_AFTER) return "idle_arms_behind_back";
        if (s.idleTicks() >= AUTHORITATIVE_AFTER) return "idle_authoritative";
        return "idle_armored";
    }

    /** One-shot cue for a flight event, or null when the event has no presentation of its own. */
    public static Cue cueFor(com.doomsovereign.core.flight.FlightEvent e) {
        return switch (e) {
            case TAKEOFF -> Cue.TAKEOFF;
            case IGNITION_MIDAIR -> Cue.IGNITION_MIDAIR;
            case BOOST_ENGAGED -> Cue.BOOST_ENGAGED;
            case BRAKING -> Cue.BRAKING;
            case SOFT_LANDING -> Cue.SOFT_LANDING;
            case HARD_LANDING -> Cue.HARD_LANDING;
            case FALL_ARRESTED -> Cue.FALL_ARRESTED;
            case LOW_ENERGY, POWER_LOST -> Cue.LOW_ENERGY;
            case BOOST_RELEASED, DISENGAGED, REFUSED_NO_ENERGY, REFUSED_LOCKED -> null;
        };
    }
}
