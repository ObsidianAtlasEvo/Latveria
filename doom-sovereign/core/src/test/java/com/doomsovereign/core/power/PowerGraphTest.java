package com.doomsovereign.core.power;

import com.doomsovereign.core.api.EnergyStorage;
import com.doomsovereign.core.api.PowerNodeAdapter;
import com.doomsovereign.core.support.Storage;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PowerGraphTest {
    /** A configurable node. */
    static final class N implements PowerNodeAdapter {
        final long id;
        final NodeKind kind;
        long gen, demand, throughput = Long.MAX_VALUE, received;
        int priority;
        Storage buffer;

        N(long id, NodeKind kind) {
            this.id = id;
            this.kind = kind;
        }

        static N gen(long id, long g) { N n = new N(id, NodeKind.GENERATOR); n.gen = g; return n; }

        static N use(long id, long d, int prio) { N n = new N(id, NodeKind.CONSUMER); n.demand = d; n.priority = prio; return n; }

        static N buf(long id, long cap, long stored) { N n = new N(id, NodeKind.BUFFER); n.buffer = new Storage(cap, stored); return n; }

        static N wire(long id, long cap) { N n = new N(id, NodeKind.CONDUIT); n.throughput = cap; return n; }

        @Override public long nodeId() { return id; }
        @Override public NodeKind kind() { return kind; }
        @Override public long generation() { return gen; }
        @Override public long demand() { return demand; }
        @Override public int priority() { return priority; }
        @Override public void supply(long e) { received += e; }
        @Override public EnergyStorage buffer() { return buffer; }
        @Override public long throughput() { return throughput; }
    }

    static PowerGraph chain(N... ns) {
        PowerGraph g = new PowerGraph();
        for (N n : ns) g.add(n);
        for (int i = 1; i < ns.length; i++) g.connect(ns[i - 1].id, ns[i].id);
        return g;
    }

    static void assertConserved(NetworkStats s) {
        assertEquals(s.generated() + s.discharged(), s.delivered() + s.charged() + s.wasted(), s.toString());
        assertTrue(s.wasted() >= 0 && s.unmetDemand() >= 0 && s.charged() >= 0 && s.discharged() >= 0, s.toString());
    }

    @Test
    void connectingMergesAndCountsNetworks() {
        PowerGraph g = new PowerGraph();
        for (long i = 1; i <= 6; i++) g.add(N.wire(i, 100));
        assertEquals(6, g.networkCount());
        g.connect(1, 2);
        g.connect(2, 3);
        g.connect(4, 5);
        assertEquals(3, g.networkCount());
        assertEquals(g.networkOf(1), g.networkOf(3));
        assertNotEquals(g.networkOf(1), g.networkOf(4));
        assertFalse(g.connect(1, 2), "already linked");
        assertFalse(g.connect(1, 1));
        g.connect(3, 4);
        assertEquals(2, g.networkCount());
        assertEquals(5, g.members(g.networkOf(5)).size());
        assertThrows(IllegalArgumentException.class, () -> g.add(N.wire(1, 5)));
        assertThrows(IllegalArgumentException.class, () -> g.connect(1, 99));
    }

    @Test
    void cuttingABridgeSplitsLazily() {
        PowerGraph g = chain(N.wire(1, 9), N.wire(2, 9), N.wire(3, 9), N.wire(4, 9));
        long before = g.rebuilds();
        g.disconnect(2, 3);
        assertEquals(2, g.networkCount());
        assertEquals(before + 1, g.rebuilds(), "one flood fill");
        assertEquals(Set.of(1L, 2L), new HashSet<>(g.members(g.networkOf(1))));
        assertEquals(Set.of(3L, 4L), new HashSet<>(g.members(g.networkOf(4))));
        assertFalse(g.disconnect(2, 3));
    }

    @Test
    void cuttingALoopDoesNotSplit() {
        PowerGraph g = chain(N.wire(1, 9), N.wire(2, 9), N.wire(3, 9), N.wire(4, 9));
        g.connect(4, 1);
        g.disconnect(2, 3);
        assertEquals(1, g.networkCount());
    }

    @Test
    void removingALeafNeverRebuilds() {
        PowerGraph g = chain(N.wire(1, 9), N.wire(2, 9), N.wire(3, 9));
        long before = g.rebuilds();
        g.remove(3);
        assertEquals(1, g.networkCount());
        assertEquals(before, g.rebuilds());
        g.remove(3);
        assertEquals(2, g.nodeCount());
    }

    @Test
    void removingAMiddleNodeSplits() {
        PowerGraph g = chain(N.wire(1, 9), N.wire(2, 9), N.wire(3, 9));
        g.remove(2);
        assertEquals(2, g.networkCount());
        g.remove(1);
        g.remove(3);
        assertEquals(0, g.networkCount());
    }

    @Test
    void priorityThenProportional() {
        N gen = N.gen(1, 100);
        N life = N.use(2, 60, 10);
        N forgeA = N.use(3, 30, 0);
        N forgeB = N.use(4, 90, 0);
        PowerGraph g = chain(gen, life, forgeA, forgeB);
        NetworkStats s = g.tick().get(0);
        assertEquals(60, life.received, "high priority is served first and in full");
        assertEquals(10, forgeA.received, "40 left, split 30:90");
        assertEquals(30, forgeB.received);
        assertEquals(100, s.delivered());
        assertEquals(80, s.unmetDemand());
        assertConserved(s);
    }

    @Test
    void proportionalSharesAreExactIntegers() {
        List<PowerNodeAdapter> tier = List.of(N.use(1, 1, 0), N.use(2, 1, 0), N.use(3, 1, 0));
        long[] s = PowerGraph.proportional(tier, 2);
        assertEquals(2, s[0] + s[1] + s[2]);
        for (long v : s) assertTrue(v == 0 || v == 1);
        assertArrayEquals(new long[]{0, 0, 0}, PowerGraph.proportional(tier, 0));
        assertArrayEquals(new long[]{1, 1, 1}, PowerGraph.proportional(tier, 50), "never more than asked");
    }

    @Test
    void buffersAbsorbSurplusAndCoverDeficits() {
        N gen = N.gen(1, 100);
        N use = N.use(2, 30, 0);
        N cap = N.buf(3, 1000, 0);
        PowerGraph g = chain(gen, use, cap);
        NetworkStats s = g.tick().get(0);
        assertEquals(70, s.charged());
        assertEquals(70, cap.buffer.stored());
        assertConserved(s);
        gen.gen = 0;
        use.demand = 50;
        s = g.tick().get(0);
        assertEquals(50, s.discharged());
        assertEquals(20, cap.buffer.stored());
        assertEquals(80, use.received);
        assertConserved(s);
    }

    @Test
    void theWeakestConduitCapsTransfer() {
        N gen = N.gen(1, 1000);
        N thin = N.wire(2, 64);
        N use = N.use(3, 500, 0);
        N cap = N.buf(4, 10_000, 0);
        PowerGraph g = chain(gen, N.wire(5, 10_000), thin, use, cap);
        NetworkStats s = g.tick().get(0);
        assertEquals(64, s.transferCap());
        assertEquals(64, use.received);
        assertEquals(0, s.charged(), "the whole budget went to the consumer");
        assertEquals(936, s.wasted());
        assertConserved(s);
    }

    @Test
    void networksWithoutGenerationDrawNothingAndWasteNothing() {
        N use = N.use(1, 10, 0);
        PowerGraph g = chain(use, N.wire(2, 99));
        NetworkStats s = g.tick().get(0);
        assertEquals(0, s.delivered());
        assertEquals(10, s.unmetDemand());
        assertConserved(s);
    }

    @Test
    void generationSaturatesInsteadOfOverflowing() {
        PowerGraph g = chain(N.gen(1, Long.MAX_VALUE), N.gen(2, Long.MAX_VALUE), N.use(3, 5, 0));
        NetworkStats s = g.tick().get(0);
        assertEquals(Long.MAX_VALUE, s.generated());
        assertEquals(5, s.delivered());
        assertConserved(s);
    }

    /** Property test: random topologies and loads always conserve energy, never over-deliver, and match a reference component count. */
    @Test
    void randomNetworksConserveEnergyAndTopologyStaysCorrect() {
        for (int seed = 0; seed < 200; seed++) {
            Random r = new Random(seed);
            PowerGraph g = new PowerGraph();
            List<N> nodes = new ArrayList<>();
            int count = 5 + r.nextInt(60);
            for (int i = 0; i < count; i++) {
                N n = switch (r.nextInt(4)) {
                    case 0 -> N.gen(i, r.nextInt(500));
                    case 1 -> N.use(i, r.nextInt(400), r.nextInt(3));
                    case 2 -> N.buf(i, 1 + r.nextInt(2000), r.nextInt(500));
                    default -> N.wire(i, 1 + r.nextInt(800));
                };
                if (n.buffer != null && n.buffer.stored() > n.buffer.capacity()) n.buffer = new Storage(n.buffer.capacity(), n.buffer.capacity());
                nodes.add(n);
                g.add(n);
            }
            Set<Long> removed = new HashSet<>();
            Set<List<Long>> edges = new HashSet<>();
            for (int step = 0; step < 150; step++) {
                long a = r.nextInt(count), b = r.nextInt(count);
                if (removed.contains(a) || removed.contains(b) || a == b) continue;
                List<Long> e = a < b ? List.of(a, b) : List.of(b, a);
                int op = r.nextInt(10);
                if (op < 6) { g.connect(a, b); edges.add(e); }
                else if (op < 9) { g.disconnect(a, b); edges.remove(e); }
                else {
                    g.remove(a);
                    removed.add(a);
                    edges.removeIf(x -> x.contains(a));
                }
                if (step % 10 == 0) {
                    assertEquals(referenceComponents(count, removed, edges), g.networkCount(), "seed " + seed + " step " + step);
                    long demandBefore = 0;
                    for (N n : nodes) n.received = 0;
                    for (NetworkStats s : g.tick()) assertConserved(s);
                    for (N n : nodes) {
                        if (n.kind == NodeKind.CONSUMER && !removed.contains(n.id)) assertTrue(n.received <= n.demand, "over-delivered");
                        if (n.buffer != null) assertTrue(n.buffer.stored() >= 0 && n.buffer.stored() <= n.buffer.capacity());
                        demandBefore += n.demand;
                    }
                    assertTrue(demandBefore >= 0);
                }
            }
        }
    }

    static int referenceComponents(int count, Set<Long> removed, Set<List<Long>> edges) {
        int[] parent = new int[count];
        for (int i = 0; i < count; i++) parent[i] = i;
        for (List<Long> e : edges) union(parent, (int) (long) e.get(0), (int) (long) e.get(1));
        Set<Integer> roots = new HashSet<>();
        for (int i = 0; i < count; i++) if (!removed.contains((long) i)) roots.add(find(parent, i));
        return roots.size();
    }

    static int find(int[] p, int i) {
        while (p[i] != i) i = p[i] = p[p[i]];
        return i;
    }

    static void union(int[] p, int a, int b) {
        p[find(p, a)] = find(p, b);
    }
}
