package com.doomsovereign.core.support;

import com.doomsovereign.core.api.EnergyStorage;

/** A plain capacitor for power-network tests. */
public final class Storage implements EnergyStorage {
    private final long capacity;
    private long stored;

    public Storage(long capacity, long stored) {
        this.capacity = capacity;
        this.stored = stored;
    }

    @Override public long capacity() { return capacity; }
    @Override public long stored() { return stored; }

    @Override
    public long insert(long amount, boolean simulate) {
        long n = Math.max(0, Math.min(amount, capacity - stored));
        if (!simulate) stored += n;
        return n;
    }

    @Override
    public long extract(long amount, boolean simulate) {
        long n = Math.max(0, Math.min(amount, stored));
        if (!simulate) stored -= n;
        return n;
    }
}
