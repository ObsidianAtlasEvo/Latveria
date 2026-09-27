package com.doomsovereign.core.flight;

import java.util.Set;

/**
 * What the adapter should apply this tick. Velocities are in the wearer's local frame (forward,
 * right, up) so the core never needs yaw; the adapter rotates them into world space.
 *
 * @param state          state after this tick
 * @param forwardSpeed   blocks/tick along facing
 * @param strafeSpeed    blocks/tick to the right
 * @param verticalSpeed  blocks/tick upward; NaN means "leave vanilla gravity alone"
 * @param leanDegrees    forward body lean for the animation layer
 * @param rollDegrees    sideways roll for strafing
 * @param thrust         0..1 exhaust intensity for particles and audio
 * @param energyDrained  DE spent this tick
 * @param landingImpact  0..1 when landing this tick (drives shockwave and camera impulse)
 * @param events         one-shot cues
 */
public record FlightOutput(FlightState state, double forwardSpeed, double strafeSpeed, double verticalSpeed,
                           double leanDegrees, double rollDegrees, double thrust, long energyDrained,
                           double landingImpact, Set<FlightEvent> events) {
    public boolean overridesGravity() {
        return !Double.isNaN(verticalSpeed);
    }
}
