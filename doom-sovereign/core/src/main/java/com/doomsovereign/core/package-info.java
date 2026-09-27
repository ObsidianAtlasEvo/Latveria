/**
 * DOOM: SOVEREIGN gameplay core.
 *
 * <p>Pure Java 21 with no Minecraft or Fabric dependency. Everything here is deterministic and
 * unit-tested; the Fabric mod adapts Minecraft objects to the small interfaces in
 * {@link com.doomsovereign.core.api}. Time is measured in game ticks (20 per second) and energy in
 * integer <em>Doom Energy</em> units (DE) so that transfers are exactly conserved.
 */
package com.doomsovereign.core;
