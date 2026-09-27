package com.doomsovereign.core.api;

/** A creature (or machine) Doom can study. The adapter maps an entity type to a stable id. */
public interface AnalysisSubject {
    /** Stable identifier, e.g. {@code minecraft:blaze}. */
    String subjectId();

    /** Current observable state; used by scans to report live values. */
    default double healthFraction() {
        return 1.0;
    }
}
