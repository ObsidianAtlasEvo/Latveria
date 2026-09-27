package com.doomsovereign.core.research;

import java.util.List;
import java.util.Set;

import static com.doomsovereign.core.research.Branch.*;
import static com.doomsovereign.core.research.Requirement.*;

/**
 * The default research tree. Every node changes what Doom can do. Requirements come from ordinary
 * Minecraft accomplishments: materials gathered, places visited, things studied and defeated.
 */
public final class DoomResearch {
    private DoomResearch() {
    }

    private static ResearchNode n(String id, Branch b, String title, String desc, Set<String> pre, List<Requirement> req, int ticks) {
        return new ResearchNode(id, b, title, desc, pre, req, ticks);
    }

    public static ResearchTree standard() {
        return new ResearchTree(List.of(
                // Science foundations
                n("latverian_metallurgy", SCIENCE, "Latverian Metallurgy", "Forge Latverian alloy: iron, copper and quartz folded under redstone current.",
                        Set.of(), List.of(sample("minecraft:iron_ingot", 32), sample("minecraft:copper_ingot", 32), sample("minecraft:quartz", 8)), 0),
                n("doom_engineering", SCIENCE, "Doom Engineering", "Build the Doom Forge and the Research Console.",
                        Set.of("latverian_metallurgy"), List.of(sample("minecraft:redstone", 64), crafted("doom_sovereign:latverian_alloy")), 600),
                // Armor
                n("royal_armor", ARMOR, "The Royal Armor", "Assemble the Royal Armor of Doom and enter Doom Mode.",
                        Set.of("doom_engineering"), List.of(sample("minecraft:diamond", 8), entered("minecraft:the_nether")), 1_200),
                n("pressure_hull", ARMOR, "Pressure Hull", "Environmental seal and aquatic impellers.",
                        Set.of("royal_armor"), List.of(analysed("minecraft:guardian"), sample("minecraft:prismarine_crystals", 16)), 1_200),
                n("vibranium_lattice", ARMOR, "Resonant Lattice", "Dense capacitors and the Mk II frame.",
                        Set.of("royal_armor"), List.of(sample("minecraft:netherite_ingot", 2), sample("minecraft:echo_shard", 4)), 2_400),
                // Energy / mobility
                n("repulsor_levitation", ENERGY, "Repulsor Levitation", "Thrusters: powered take-off, hover and flight.",
                        Set.of("royal_armor"), List.of(sample("minecraft:blaze_rod", 8), sample("minecraft:phantom_membrane", 4)), 1_200),
                n("emergency_repulsors", ENERGY, "Emergency Repulsors", "Fall arrest fires automatically before a fatal impact.",
                        Set.of("repulsor_levitation"), List.of(achieved("doom_sovereign:survive_long_fall")), 0),
                n("afterburner_lattice", ENERGY, "Afterburner Lattice", "Mk II thrusters and boost.",
                        Set.of("repulsor_levitation", "vibranium_lattice"), List.of(sample("minecraft:ghast_tear", 4)), 2_400),
                n("coherent_emitters", ENERGY, "Coherent Emitters", "Gauntlet focusing: charged blasts and the sustained beam.",
                        Set.of("royal_armor"), List.of(analysed("minecraft:blaze"), sample("minecraft:amethyst_shard", 16)), 1_800),
                n("omnidirectional_fields", ENERGY, "Omnidirectional Fields", "Spherical force fields.",
                        Set.of("coherent_emitters"), List.of(analysed("minecraft:shulker"), sample("minecraft:shulker_shell", 4)), 2_400),
                // Robotics
                n("doombot_cognition", ROBOTICS, "Doombot Cognition", "The Doombot Assembly Station and the Standard Doombot.",
                        Set.of("doom_engineering"), List.of(sample("minecraft:iron_block", 8), sample("minecraft:redstone_block", 4),
                                analysed("minecraft:iron_golem")), 1_800),
                n("praetorian_protocols", ROBOTICS, "Praetorian Protocols", "Royal-security Doombots with threat response.",
                        Set.of("doombot_cognition", "royal_armor"), List.of(defeated("doom_sovereign:rogue_sentinel")), 2_400),
                // Sorcery (parallel to technology, not behind it)
                n("apprentice_of_the_arts", SORCERY, "Apprentice of the Arts", "Arcane Focus awakens. Mystic bolt and the first ward.",
                        Set.of(), List.of(sample("minecraft:lapis_lazuli", 32), achieved("minecraft:story/enchant_item")), 0),
                n("wardcraft", SORCERY, "Wardcraft", "Protective wards against hostile magic and curses.",
                        Set.of("apprentice_of_the_arts"), List.of(analysed("minecraft:witch"), analysed("minecraft:evoker")), 1_200),
                n("chains_of_binding", SORCERY, "Chains of Binding", "Runic chains that hold an eligible enemy in place.",
                        Set.of("wardcraft"), List.of(sample("minecraft:chain", 16), analysed("minecraft:vex")), 1_200),
                n("translocation", SORCERY, "Translocation", "Short-range combat teleport.",
                        Set.of("apprentice_of_the_arts"), List.of(analysed("minecraft:enderman"), sample("minecraft:ender_pearl", 16)), 1_200),
                n("ritual_circles", SORCERY, "Ritual Circles", "Advanced spells cast within a charged circle.",
                        Set.of("wardcraft"), List.of(visited("minecraft:ancient_city")), 2_400),
                n("banishment", SORCERY, "Banishment", "Unmake supernatural creatures bound to this plane.",
                        Set.of("ritual_circles"), List.of(defeated("minecraft:wither")), 3_600),
                n("veil_of_the_mask", SORCERY, "Veil of the Mask", "An enchanted cloak that hides a still figure.",
                        Set.of("translocation"), List.of(visited("minecraft:woodland_mansion")), 1_800),
                // Dimensional / hybrid
                n("dimensional_theory", DIMENSIONAL, "Dimensional Theory", "Teleport stabilizers and anchored translocation.",
                        Set.of("translocation", "coherent_emitters"), List.of(entered("minecraft:the_end")), 2_400),
                n("techno_arcane_synthesis", HYBRID, "Techno-Arcane Synthesis", "Armour energy stabilises wards; analysed magic yields counter-runes.",
                        Set.of("wardcraft", "omnidirectional_fields"), List.of(), 3_600),
                n("temporal_mechanics", HYBRID, "Temporal Mechanics", "The Time Platform.",
                        Set.of("dimensional_theory", "techno_arcane_synthesis"),
                        List.of(defeated("minecraft:ender_dragon"), sample("minecraft:nether_star", 1)), 6_000)
        ));
    }
}
