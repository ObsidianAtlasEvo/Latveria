package com.doomsovereign.core.energy;

/** An external charger (Armor Cradle, Power Station, conduit tap) feeding the suit this tick. */
public interface RechargeSource {
    /** Maximum DE per tick this source can deliver. */
    long ratePerTick();

    /** Actually draws the energy that was delivered (so network sources are debited). */
    default void onDelivered(long amount) {
    }
}
