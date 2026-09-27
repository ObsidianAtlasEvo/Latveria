package com.doomsovereign.core.research;

import com.doomsovereign.core.api.ResearchEvent;

/**
 * A concrete accomplishment a node needs, e.g. "collect 8 blaze rods" or "fully analyse a blaze".
 *
 * @param type  event type that counts
 * @param key   what it must concern
 * @param count how many
 */
public record Requirement(ResearchEvent.Type type, String key, int count) {
    public Requirement {
        if (count <= 0) throw new IllegalArgumentException("count");
    }

    public static Requirement sample(String item, int n) {
        return new Requirement(ResearchEvent.Type.SAMPLE_COLLECTED, item, n);
    }

    public static Requirement analysed(String subject) {
        return new Requirement(ResearchEvent.Type.SUBJECT_ANALYSED, subject, 1);
    }

    public static Requirement crafted(String item) {
        return new Requirement(ResearchEvent.Type.ITEM_CRAFTED, item, 1);
    }

    public static Requirement achieved(String id) {
        return new Requirement(ResearchEvent.Type.ACHIEVEMENT, id, 1);
    }

    public static Requirement visited(String structure) {
        return new Requirement(ResearchEvent.Type.STRUCTURE_VISITED, structure, 1);
    }

    public static Requirement defeated(String boss) {
        return new Requirement(ResearchEvent.Type.BOSS_DEFEATED, boss, 1);
    }

    public static Requirement entered(String dimension) {
        return new Requirement(ResearchEvent.Type.DIMENSION_ENTERED, dimension, 1);
    }

    String counterKey() {
        return type + "|" + key;
    }
}
