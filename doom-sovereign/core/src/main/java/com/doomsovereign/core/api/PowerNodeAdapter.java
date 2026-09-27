package com.doomsovereign.core.api;

import com.doomsovereign.core.power.NodeKind;

/**
 * A block entity participating in a Doom power network. The mod creates one per placed Doom machine,
 * registers it with {@link com.doomsovereign.core.power.PowerGraph} on load and removes it on unload.
 */
public interface PowerNodeAdapter {
    /** Stable id, typically the packed BlockPos plus a dimension salt. */
    long nodeId();

    NodeKind kind();

    /** Generators: energy produced this tick. */
    default long generation() {
        return 0;
    }

    /** Consumers: energy wanted this tick. */
    default long demand() {
        return 0;
    }

    default int priority() {
        return 0;
    }

    /** Consumers: receives the granted energy. */
    default void supply(long energy) {
    }

    /** Buffers and consumers with internal cells. */
    default EnergyStorage buffer() {
        return null;
    }

    /** Conduits: maximum DE per tick this piece can carry. */
    default long throughput() {
        return Long.MAX_VALUE;
    }
}
