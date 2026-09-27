package com.doomsovereign.core.heat;

public enum HeatState {
    /** Full output. */
    NOMINAL,
    /** Above the warning threshold: HUD shows heat, output still full. */
    WARNING,
    /** Above the throttle threshold: output scaled down smoothly. */
    THROTTLED,
    /** Critical reached: weapons locked until heat falls back below the recovery threshold. */
    LOCKED
}
