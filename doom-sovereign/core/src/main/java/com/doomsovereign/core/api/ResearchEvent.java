package com.doomsovereign.core.api;

/**
 * Something the player did that research cares about.
 *
 * @param type   what happened
 * @param key    what it happened to (item id, subject id, advancement id, structure id)
 * @param amount how many times (usually 1)
 */
public record ResearchEvent(Type type, String key, int amount) {
    public enum Type { SAMPLE_COLLECTED, SUBJECT_ANALYSED, ITEM_CRAFTED, ACHIEVEMENT, STRUCTURE_VISITED, BOSS_DEFEATED, DIMENSION_ENTERED }

    public ResearchEvent {
        if (key == null || key.isBlank()) throw new IllegalArgumentException("key");
        if (amount <= 0) throw new IllegalArgumentException("amount must be positive");
    }

    public static ResearchEvent of(Type type, String key) {
        return new ResearchEvent(type, key, 1);
    }
}
