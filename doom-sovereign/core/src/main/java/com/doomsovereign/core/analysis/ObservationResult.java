package com.doomsovereign.core.analysis;

import java.util.List;

/**
 * @param gained                 knowledge added (0 if the observation was too soon to count)
 * @param counted                whether the observation counted at all
 * @param newlyRevealed          trait ids revealed by this observation
 * @param newlyUnlocked          countermeasure ids unlocked by this observation
 * @param becameComplete         the subject is now fully analysed (fires a research event)
 */
public record ObservationResult(double gained, boolean counted, List<String> newlyRevealed, List<String> newlyUnlocked,
                                boolean becameComplete) {
}
