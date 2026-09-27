package com.doomsovereign.core.analysis;

import java.util.Set;

/**
 * An engineering or arcane response that becomes available once a subject is understood.
 *
 * @param id           unlock id (research/module/ward key)
 * @param title        display name
 * @param description  what it does
 * @param minKnowledge knowledge needed
 * @param traits       traits that must be revealed
 */
public record Countermeasure(String id, String title, String description, double minKnowledge, Set<String> traits) {
    public Countermeasure {
        traits = Set.copyOf(traits);
    }
}
