/**
 * Presentation glue between game logic and the generated assets: which animation clip, sound
 * event and particle effect each gameplay moment uses. Pure data and pure functions, so the ids
 * can be checked against the asset files in a unit test; the Minecraft side only looks them up.
 */
package com.doomsovereign.core.presentation;
