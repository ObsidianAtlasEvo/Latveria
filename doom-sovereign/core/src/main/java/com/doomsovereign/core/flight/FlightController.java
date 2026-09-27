package com.doomsovereign.core.flight;

import com.doomsovereign.core.api.FlightEnvironment;
import com.doomsovereign.core.energy.ArmorEnergy;
import com.doomsovereign.core.energy.DrainCategory;
import com.doomsovereign.core.energy.DrainTable;
import java.util.EnumSet;
import java.util.Set;

/**
 * Deterministic flight state machine (directive section 16).
 *
 * <p>Runs server-side once per tick. Speed ramps toward the target (no instant top speed), lean
 * follows speed, releasing movement brakes to a hover, and energy is drawn in proportion to speed
 * and acceleration. When the cell reaches its reserve the suit refuses further thrust and flies a
 * gentle emergency descent instead of dropping the wearer out of the sky.
 */
public final class FlightController {
    public static final int TAKEOFF_TICKS = 8;
    public static final int LANDING_TICKS = 6;
    public static final int ARREST_TICKS = 6;
    public static final double TAKEOFF_LIFT = 0.42;
    public static final double DESCENT_RATE = 0.25;
    public static final double LOW_ENERGY_DESCENT_RATE = 0.3;
    public static final double HARD_LANDING_SPEED = 0.7;
    public static final double MAX_LEAN = 28;
    public static final double MAX_ROLL = 14;

    private FlightState state = FlightState.GROUNDED;
    private int timer;
    private double speed;
    private double dirForward = 1;
    private double dirStrafe;
    private double lastVertical;
    private double arrestStartVelocity;
    private double impactThisTick;
    private FlightProfile profile;

    public FlightController(FlightProfile profile) {
        this.profile = profile;
    }

    public FlightOutput tick(FlightInput in, FlightEnvironment env, ArmorEnergy energy, long now) {
        Set<FlightEvent> events = EnumSet.noneOf(FlightEvent.class);
        long before = energy.stored();
        double vertical = Double.NaN;
        double prevSpeed = speed;
        impactThisTick = 0;

        switch (state) {
            case GROUNDED -> {
                speed = 0;
                if (!env.onGround() && profile.fallArrestUnlocked() && env.fallDistance() >= profile.arrestFallDistance()
                        && env.verticalVelocity() < -0.6 && !env.inFluid()) {
                    if (energy.tryConsume(DrainCategory.EMERGENCY, DrainTable.FALL_ARREST, now)) {
                        enter(FlightState.FALL_ARREST);
                        arrestStartVelocity = env.verticalVelocity();
                        events.add(FlightEvent.FALL_ARRESTED);
                        vertical = arrestStartVelocity;
                        break;
                    }
                }
                if (in.toggle()) {
                    if (!profile.flightUnlocked()) {
                        events.add(FlightEvent.REFUSED_LOCKED);
                    } else if (!energy.tryConsume(DrainCategory.FLIGHT, DrainTable.TAKEOFF, now)) {
                        events.add(FlightEvent.REFUSED_NO_ENERGY);
                    } else if (env.onGround()) {
                        enter(FlightState.TAKEOFF);
                        events.add(FlightEvent.TAKEOFF);
                        vertical = TAKEOFF_LIFT;
                    } else {
                        enter(FlightState.HOVER);
                        events.add(FlightEvent.IGNITION_MIDAIR);
                        vertical = 0;
                    }
                }
            }
            case TAKEOFF -> {
                vertical = TAKEOFF_LIFT * (1.0 - timer / (double) TAKEOFF_TICKS) + 0.05;
                timer++;
                if (timer >= TAKEOFF_TICKS) enter(FlightState.HOVER);
            }
            case FALL_ARREST -> {
                timer++;
                double t = Math.min(1.0, timer / (double) ARREST_TICKS);
                vertical = arrestStartVelocity * (1.0 - t);
                if (timer >= ARREST_TICKS) {
                    if (profile.flightUnlocked() && energy.spendable(DrainCategory.FLIGHT) > 0) enter(FlightState.HOVER);
                    else enter(FlightState.DESCENT);
                }
            }
            case LANDING -> {
                timer++;
                speed = Math.max(0, speed - profile.braking() * 2);
                if (timer >= LANDING_TICKS) enter(FlightState.GROUNDED);
            }
            case DESCENT, LOW_ENERGY_DESCENT -> {
                boolean low = state == FlightState.LOW_ENERGY_DESCENT;
                speed = Math.max(0, speed - profile.braking());
                vertical = -(low ? LOW_ENERGY_DESCENT_RATE : DESCENT_RATE);
                if (env.onGround()) {
                    land(events, Math.abs(lastVertical));
                    vertical = Double.NaN;
                } else if (!low && in.toggle() && energy.spendable(DrainCategory.FLIGHT) > 0) {
                    enter(FlightState.HOVER);
                    vertical = 0;
                } else if (low && energy.drain(DrainCategory.EMERGENCY, 1, now) < 1.0) {
                    enter(FlightState.GROUNDED);
                    events.add(FlightEvent.POWER_LOST);
                    vertical = Double.NaN;
                }
            }
            case HOVER, FLIGHT, BOOST, BRAKE -> vertical = poweredTick(in, env, events);
        }

        // thrust costs (powered, steerable states)
        if (state == FlightState.HOVER || state == FlightState.FLIGHT || state == FlightState.BOOST || state == FlightState.BRAKE
                || state == FlightState.TAKEOFF) {
            long cost = DrainTable.flightCost(speed, profile.cruiseSpeed(), speed - prevSpeed, state == FlightState.BOOST);
            double got = energy.drain(DrainCategory.FLIGHT, cost, now);
            if (got < 1.0) {
                enter(FlightState.LOW_ENERGY_DESCENT);
                events.add(FlightEvent.LOW_ENERGY);
                vertical = -LOW_ENERGY_DESCENT_RATE;
            }
        }
        if (!Double.isNaN(vertical)) lastVertical = vertical;
        else lastVertical = env.verticalVelocity();
        double impact = impactThisTick;
        if (impact > 0) lastVertical = 0;

        double lean = state.powered() ? MAX_LEAN * Math.min(1.0, speed / profile.boostSpeed()) * Math.signum(dirForward + 1e-9) : 0;
        double roll = state.powered() ? MAX_ROLL * dirStrafe * Math.min(1.0, speed / profile.cruiseSpeed()) : 0;
        double thrust = switch (state) {
            case GROUNDED, LANDING -> 0.0;
            case TAKEOFF, FALL_ARREST -> 1.0;
            case BOOST -> 1.0;
            case LOW_ENERGY_DESCENT -> 0.15;
            case DESCENT -> 0.2;
            default -> 0.25 + 0.6 * Math.min(1.0, speed / profile.boostSpeed());
        };
        return new FlightOutput(state, speed * dirForward, speed * dirStrafe, vertical, lean, roll, thrust,
                Math.max(0, before - energy.stored()), impact, events);
    }

    private double poweredTick(FlightInput in, FlightEnvironment env, Set<FlightEvent> events) {
        if (in.toggle()) {
            enter(FlightState.DESCENT);
            events.add(FlightEvent.DISENGAGED);
            return -DESCENT_RATE;
        }
        double vertical = in.ascend() ? profile.climbRate() : in.descend() ? -profile.climbRate() : 0;
        if (env.onGround() && in.descend()) {
            land(events, Math.abs(lastVertical));
            return Double.NaN;
        }
        double mag = in.magnitude();
        if (mag > 0.05) {
            double n = Math.hypot(in.forward(), in.strafe());
            dirForward = in.forward() / n;
            dirStrafe = in.strafe() / n;
        }
        boolean wantBoost = in.boost() && profile.boostUnlocked() && mag > 0.05;
        switch (state) {
            case HOVER -> {
                speed = Math.max(0, speed - profile.braking());
                if (wantBoost) { enter(FlightState.BOOST); events.add(FlightEvent.BOOST_ENGAGED); }
                else if (mag > 0.05) enter(FlightState.FLIGHT);
            }
            case FLIGHT -> {
                if (mag <= 0.05) { enter(FlightState.BRAKE); events.add(FlightEvent.BRAKING); }
                else if (wantBoost) { enter(FlightState.BOOST); events.add(FlightEvent.BOOST_ENGAGED); }
                else speed = approach(speed, profile.cruiseSpeed() * mag, profile.acceleration(), profile.braking());
            }
            case BOOST -> {
                if (mag <= 0.05) { enter(FlightState.BRAKE); events.add(FlightEvent.BRAKING); }
                else if (!wantBoost) { enter(FlightState.FLIGHT); events.add(FlightEvent.BOOST_RELEASED); }
                else speed = approach(speed, profile.boostSpeed() * mag, profile.acceleration() * 1.8, profile.braking());
            }
            case BRAKE -> {
                speed = Math.max(0, speed - profile.braking());
                if (mag > 0.05) enter(wantBoost ? FlightState.BOOST : FlightState.FLIGHT);
                else if (speed <= 0.02) { speed = 0; enter(FlightState.HOVER); }
            }
            default -> {
            }
        }
        if (env.onGround() && vertical <= 0 && state != FlightState.HOVER && speed < 0.05) {
            land(events, Math.abs(lastVertical));
            return Double.NaN;
        }
        return vertical;
    }

    private static double approach(double v, double target, double up, double down) {
        return v < target ? Math.min(target, v + up) : Math.max(target, v - down);
    }

    /** Enters LANDING and records this tick's 0..1 impact (drives shockwave, camera impulse, hard-landing pose). */
    private void land(Set<FlightEvent> events, double verticalSpeed) {
        double impactSpeed = Math.hypot(verticalSpeed, speed * 0.5);
        enter(FlightState.LANDING);
        events.add(impactSpeed >= HARD_LANDING_SPEED ? FlightEvent.HARD_LANDING : FlightEvent.SOFT_LANDING);
        impactThisTick = Math.max(Math.min(1.0, impactSpeed / 1.5), 0.01);
    }

    private void enter(FlightState s) {
        state = s;
        timer = 0;
        if (s == FlightState.GROUNDED) speed = 0; // thrusters off: vanilla movement owns the wearer again
    }

    public void setProfile(FlightProfile p) {
        profile = p;
        if (!p.boostUnlocked() && state == FlightState.BOOST) enter(FlightState.FLIGHT);
    }

    /** Forces thrusters off (death, dimension change, armour removed). */
    public void shutdown() {
        enter(FlightState.GROUNDED);
        speed = 0;
    }

    public FlightState state() { return state; }

    public double speed() { return speed; }

    public FlightProfile profile() { return profile; }
}
