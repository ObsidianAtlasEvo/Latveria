package com.doomsovereign.core.analysis;

import java.util.List;

/** What there is to know about one kind of creature. Loaded from data. */
public record SubjectProfile(String subjectId, String name, List<Trait> traits, List<Countermeasure> countermeasures) {
    public SubjectProfile {
        traits = List.copyOf(traits);
        countermeasures = List.copyOf(countermeasures);
        java.util.Set<String> ids = new java.util.HashSet<>();
        for (Trait t : traits) if (!ids.add(t.id())) throw new IllegalArgumentException(subjectId + ": duplicate trait " + t.id());
        for (Countermeasure c : countermeasures)
            for (String t : c.traits())
                if (!ids.contains(t)) throw new IllegalArgumentException(subjectId + ": countermeasure " + c.id() + " needs unknown trait " + t);
    }

    /** Fallback for creatures without a profile (e.g. from other mods): vitals and behaviour only. */
    public static SubjectProfile generic(String subjectId) {
        return new SubjectProfile(subjectId, subjectId, List.of(
                new Trait("health", TraitCategory.VITALS, "Health and armour readout", 10, null),
                new Trait("hostility", TraitCategory.BEHAVIOUR, "Aggression pattern recorded", 40, ObservationMethod.OBSERVED_ATTACK),
                new Trait("attack_profile", TraitCategory.ATTACK, "Attack reach and cadence", 70, ObservationMethod.DAMAGE_TAKEN)),
                List.of());
    }
}
