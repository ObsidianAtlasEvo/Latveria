package com.doomsovereign.core.focus;

/**
 * Ways Arcane Focus recovers (directive section 14). Unlike armour energy it cannot be charged
 * from a machine: it returns with time and stillness, near places of power, and from mastery.
 */
public enum FocusSource {
    /** Ordinary slow recovery, only while not casting. */
    TIME,
    /** Standing still, not flying, not in combat for a while. */
    MEDITATION,
    /** Inside a charged ritual circle. */
    RITUAL_SITE,
    /** An equipped relic. */
    RELIC,
    /** Completing a spell successfully returns a sliver. */
    SUCCESSFUL_CAST,
    /** Banishing or slaying a supernatural enemy. */
    SUPERNATURAL_KILL
}
