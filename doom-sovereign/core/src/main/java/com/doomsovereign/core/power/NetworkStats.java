package com.doomsovereign.core.power;

/**
 * Energy flow of one network in one tick. Invariant (tested):
 * {@code generated + discharged == delivered + charged + wasted}.
 */
public record NetworkStats(int networkId, int nodes, long generated, long discharged, long delivered, long charged,
                           long wasted, long unmetDemand, long transferCap) {
}
