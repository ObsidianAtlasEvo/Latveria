package com.doomsovereign.core.api;

/** Anything that holds Doom Energy: armour cells, machine buffers, power cores. */
public interface EnergyStorage {
    long capacity();

    long stored();

    /** Adds up to {@code amount}; returns what was (or would be) accepted. Never negative. */
    long insert(long amount, boolean simulate);

    /** Removes up to {@code amount}; returns what was (or would be) removed. Never negative. */
    long extract(long amount, boolean simulate);

    default long space() {
        return capacity() - stored();
    }

    default double fraction() {
        return capacity() == 0 ? 0 : (double) stored() / capacity();
    }
}
