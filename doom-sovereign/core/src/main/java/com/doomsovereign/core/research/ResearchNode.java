package com.doomsovereign.core.research;

import java.util.List;
import java.util.Set;

/**
 * One research project. Nodes unlock transformative capabilities (a new thruster, a new spell),
 * never +2 % bonuses.
 *
 * @param id            stable id; also the unlock id modules and abilities check
 * @param branch        Science, Armor, Robotics, Energy, Dimensional, Sorcery or Hybrid
 * @param title         display name
 * @param description   what it gives, in one sentence
 * @param prerequisites node ids that must be completed first
 * @param requirements  accomplishments that must be recorded
 * @param consoleTicks  time at the Research Console to complete once requirements are met (0 = automatic)
 */
public record ResearchNode(String id, Branch branch, String title, String description, Set<String> prerequisites,
                           List<Requirement> requirements, int consoleTicks) {
    public ResearchNode {
        prerequisites = Set.copyOf(prerequisites);
        requirements = List.copyOf(requirements);
        if (consoleTicks < 0) throw new IllegalArgumentException("consoleTicks");
    }
}
