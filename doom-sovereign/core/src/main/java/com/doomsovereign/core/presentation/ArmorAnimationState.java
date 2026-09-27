package com.doomsovereign.core.presentation;

import com.doomsovereign.core.flight.FlightState;
import com.doomsovereign.core.suit.DoomModeState;

/**
 * What the base animation layer needs to know about the wearer this frame.
 *
 * @param mode             Doom Mode state
 * @param firstEquip       the suit has never finished initialising (plays the long sequence)
 * @param flight           flight state from the server
 * @param onGround         vanilla on-ground flag
 * @param horizontalSpeed  blocks per tick
 * @param verticalSpeed    blocks per tick, positive up
 * @param forwardInput     -1..1 (flight strafing chooses the strafe clips)
 * @param strafeInput      -1..1, positive = right
 * @param sprinting        vanilla sprint flag
 * @param sneaking         vanilla sneak flag
 * @param aiming           a gauntlet is raised (charge held or aim mode)
 * @param beaming          sustained beam active
 * @param channeling       a ritual is being channelled
 * @param idleTicks        ticks since the last movement or action (idle variants rotate on this)
 */
public record ArmorAnimationState(DoomModeState mode, boolean firstEquip, FlightState flight, boolean onGround,
                                  double horizontalSpeed, double verticalSpeed, double forwardInput, double strafeInput,
                                  boolean sprinting, boolean sneaking, boolean aiming, boolean beaming, boolean channeling,
                                  long idleTicks) {
    public static ArmorAnimationState standing() {
        return new ArmorAnimationState(DoomModeState.ACTIVE, false, FlightState.GROUNDED, true, 0, 0, 0, 0, false, false,
                false, false, false, 0);
    }

    public ArmorAnimationState withFlight(FlightState f, double fwd, double strafe, double vy) {
        return new ArmorAnimationState(mode, firstEquip, f, false, horizontalSpeed, vy, fwd, strafe, sprinting, sneaking,
                aiming, beaming, channeling, idleTicks);
    }

    public ArmorAnimationState moving(double speed, boolean sprint) {
        return new ArmorAnimationState(mode, firstEquip, flight, onGround, speed, verticalSpeed, forwardInput, strafeInput,
                sprint, sneaking, aiming, beaming, channeling, 0);
    }

    public ArmorAnimationState idleFor(long ticks) {
        return new ArmorAnimationState(mode, firstEquip, flight, onGround, 0, verticalSpeed, forwardInput, strafeInput, false,
                sneaking, aiming, beaming, channeling, ticks);
    }

    public ArmorAnimationState with(DoomModeState m, boolean first) {
        return new ArmorAnimationState(m, first, flight, onGround, horizontalSpeed, verticalSpeed, forwardInput, strafeInput,
                sprinting, sneaking, aiming, beaming, channeling, idleTicks);
    }

    public ArmorAnimationState airborne(double vy) {
        return new ArmorAnimationState(mode, firstEquip, flight, false, horizontalSpeed, vy, forwardInput, strafeInput,
                sprinting, sneaking, aiming, beaming, channeling, idleTicks);
    }

    public ArmorAnimationState combat(boolean aim, boolean beam, boolean ritual, boolean sneak) {
        return new ArmorAnimationState(mode, firstEquip, flight, onGround, horizontalSpeed, verticalSpeed, forwardInput,
                strafeInput, sprinting, sneak, aim, beam, ritual, idleTicks);
    }
}
