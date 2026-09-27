package com.doomsovereign.core.api;

/** A machine or device that draws power from a Doom power network each tick. */
public interface EnergyConsumer {
    /** Energy wanted this tick. */
    long demand();

    /** Higher priorities are served first when supply is short (security before lighting). */
    default int priority() {
        return 0;
    }

    /** Delivers the energy granted this tick (0..demand). */
    void accept(long energy);
}
