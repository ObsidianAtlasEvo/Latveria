package com.doomsovereign.core.power;

import com.doomsovereign.core.power.PowerGraphTest.N;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Large-network stress test. Measures wall-clock times on whatever machine runs the build and
 * writes them to docs/PERFORMANCE_CORE.md (path passed by Gradle). The assertions only use very
 * loose ceilings so a slow CI machine does not fail the build; the recorded numbers are the point.
 */
@Tag("stress")
class PowerGraphStressTest {
    private final List<String> rows = new ArrayList<>();

    private long timed(String what, Runnable r) {
        long t0 = System.nanoTime();
        r.run();
        long ns = System.nanoTime() - t0;
        rows.add(String.format(Locale.ROOT, "| %s | %.2f ms |", what, ns / 1e6));
        return ns;
    }

    @Test
    void hundredThousandNodes() throws IOException {
        final int side = 317; // 317 x 317 = 100,489 nodes
        PowerGraph g = new PowerGraph();
        List<N> consumers = new ArrayList<>();
        timed("register 100,489 nodes", () -> {
            for (int y = 0; y < side; y++)
                for (int x = 0; x < side; x++) {
                    long id = (long) y * side + x;
                    N n;
                    if (x % 50 == 0 && y % 50 == 0) n = N.gen(id, 5_000);
                    else if ((x + y) % 97 == 0) { n = N.use(id, 40, (x + y) % 3); consumers.add(n); }
                    else if ((x * 7 + y) % 211 == 0) n = N.buf(id, 50_000, 0);
                    else n = N.wire(id, 1_000_000);
                    g.add(n);
                }
        });
        assertEquals(side * side, g.nodeCount());
        timed("connect as a 317x317 grid (200,288 links, merge smaller-into-larger)", () -> {
            for (int y = 0; y < side; y++)
                for (int x = 0; x < side; x++) {
                    long id = (long) y * side + x;
                    if (x + 1 < side) g.connect(id, id + 1);
                    if (y + 1 < side) g.connect(id, id + side);
                }
        });
        assertEquals(1, g.networkCount());
        long[] tickNs = new long[20];
        for (int i = 0; i < tickNs.length; i++) {
            long t0 = System.nanoTime();
            for (NetworkStats s : g.tick()) PowerGraphTest.assertConserved(s);
            tickNs[i] = System.nanoTime() - t0;
        }
        java.util.Arrays.sort(tickNs);
        rows.add(String.format(Locale.ROOT, "| flow tick, one 100k-node network (median of 20) | %.2f ms |", tickNs[10] / 1e6));
        rows.add(String.format(Locale.ROOT, "| flow tick, worst of 20 | %.2f ms |", tickNs[19] / 1e6));
        long served = consumers.stream().filter(c -> c.received > 0).count();
        assertEquals(consumers.size(), served, "every consumer on a well-fed grid gets power");

        // cut the grid in half along a column: 317 disconnects, one lazy rebuild
        final int col = side / 2;
        long rebuildsBefore = g.rebuilds();
        timed("cut 317 links (marks dirty only)", () -> {
            for (int y = 0; y < side; y++) g.disconnect((long) y * side + col, (long) y * side + col + 1);
        });
        long splitNs = timed("lazy split: flood fill of 100k members", g::settle);
        assertEquals(2, g.networkCount());
        assertEquals(rebuildsBefore + 1, g.rebuilds());
        timed("rejoin halves with one link", () -> g.connect(col, col + 1));
        assertEquals(1, g.networkCount());

        // leaf churn: add and remove 10,000 leaves - must never trigger a rebuild
        long before = g.rebuilds();
        timed("add + remove 10,000 leaf nodes", () -> {
            for (int i = 0; i < 10_000; i++) {
                long id = 1_000_000L + i;
                g.add(N.wire(id, 10));
                g.connect(id, i);
                g.remove(id);
            }
        });
        g.settle();
        assertEquals(before, g.rebuilds(), "leaf removal never rebuilds");

        // many small networks: 20,000 isolated pairs
        PowerGraph many = new PowerGraph();
        timed("build 20,000 separate 5-node networks", () -> {
            for (int k = 0; k < 20_000; k++) {
                long base = k * 5L;
                many.add(N.gen(base, 100));
                many.add(N.use(base + 1, 60, 0));
                many.add(N.buf(base + 2, 1000, 0));
                many.add(N.wire(base + 3, 500));
                many.add(N.use(base + 4, 60, 1));
                for (int j = 1; j < 5; j++) many.connect(base + j - 1, base + j);
            }
        });
        assertEquals(20_000, many.networkCount());
        long manyTick = timed("flow tick, 20,000 networks / 100,000 nodes", () -> {
            for (NetworkStats s : many.tick()) PowerGraphTest.assertConserved(s);
        });

        assertTrue(tickNs[10] < 2_000_000_000L, "a 100k-node tick should be far below 2 s");
        assertTrue(splitNs < 5_000_000_000L);
        assertTrue(manyTick < 5_000_000_000L);
        writeReport();
    }

    private void writeReport() throws IOException {
        String path = System.getProperty("doom.perf.report");
        if (path == null) return;
        Runtime rt = Runtime.getRuntime();
        StringBuilder sb = new StringBuilder();
        sb.append("# Core performance (power network)\n\n");
        sb.append("Generated by `PowerGraphStressTest` during `gradle :core:test`. These are wall-clock numbers from\n");
        sb.append("the machine that ran the build, measured on a plain JVM (no Minecraft running). They show the\n");
        sb.append("algorithmic cost of the graph code only; in-game cost also includes block-entity callbacks.\n\n");
        sb.append(String.format(Locale.ROOT, "- Date: %s%n- JVM: %s %s (%s)%n- OS: %s %s%n- CPUs available: %d%n- Max heap: %d MiB%n%n",
                LocalDate.now(), System.getProperty("java.vm.name"), System.getProperty("java.version"),
                System.getProperty("java.vm.vendor"), System.getProperty("os.name"), System.getProperty("os.arch"),
                rt.availableProcessors(), rt.maxMemory() / (1024 * 1024)));
        sb.append("| Operation | Time |\n|---|---|\n");
        for (String r : rows) sb.append(r).append('\n');
        sb.append("\nFirst-run numbers include JIT warm-up. A real server ticks each network once per game tick (50 ms budget);\n");
        sb.append("Doom networks in normal play are a few hundred nodes, three orders of magnitude below this test.\n");
        sb.append("Note: the 20,000-separate-networks case does NOT fit in one 50 ms tick. If a server ever reached that,\n");
        sb.append("networks would have to be ticked round-robin or only when a member changed; neither is implemented yet.\n");
        Path p = Path.of(path);
        Files.createDirectories(p.getParent());
        Files.writeString(p, sb.toString(), StandardCharsets.UTF_8);
    }
}
