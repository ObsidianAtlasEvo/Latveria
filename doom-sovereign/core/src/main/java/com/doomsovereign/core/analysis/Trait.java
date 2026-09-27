package com.doomsovereign.core.analysis;

/**
 * A fact about a subject that becomes visible once enough is known.
 *
 * @param id        stable id within the subject
 * @param category  vitals, attack, behaviour, resistance, weakness or immunity
 * @param text      short HUD/codex text
 * @param threshold knowledge (0..100) needed
 * @param via       if set, this method must have been used at least once (you only learn a blaze
 *                  is immune to fire by watching fire fail against it, not by scanning)
 */
public record Trait(String id, TraitCategory category, String text, double threshold, ObservationMethod via) {
}
