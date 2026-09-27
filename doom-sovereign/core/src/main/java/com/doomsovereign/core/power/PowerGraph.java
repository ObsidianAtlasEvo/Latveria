package com.doomsovereign.core.power;

import com.doomsovereign.core.api.EnergyStorage;
import com.doomsovereign.core.api.PowerNodeAdapter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/**
 * The Doom power network (directive section 28).
 *
 * <p>Nodes are registered by their block entities; connections are declared explicitly (the mod
 * connects a node to its placed neighbours when it loads). Networks are cached connected
 * components: joining two nodes merges the smaller network into the larger in O(smaller);
 * disconnecting only marks that network dirty, and it is split lazily by a flood fill restricted to
 * its own members on the next tick. Nothing ever scans the world.
 *
 * <p>Each tick a network: collects generation; serves consumer demand by priority (proportionally
 * within a priority, with exact integer remainders); tops up buffers from any surplus; covers any
 * deficit from buffers; and throws away generation nobody could take. The weakest conduit on the
 * network caps how much energy may move per tick.
 */
public final class PowerGraph {
    private static final class Node {
        final long id;
        final PowerNodeAdapter adapter;
        final Set<Long> links = new HashSet<>(4);
        int network;

        Node(long id, PowerNodeAdapter a) {
            this.id = id;
            this.adapter = a;
        }
    }

    private static final class Network {
        final int id;
        final Set<Long> members = new LinkedHashSet<>();
        boolean dirty;

        Network(int id) {
            this.id = id;
        }
    }

    private final Map<Long, Node> nodes = new HashMap<>();
    private final Map<Integer, Network> networks = new HashMap<>();
    private int nextNetwork = 1;
    private long rebuilds;

    // ---- topology ---------------------------------------------------------------------------------
    public void add(PowerNodeAdapter a) {
        long id = a.nodeId();
        if (nodes.containsKey(id)) throw new IllegalArgumentException("node already registered: " + id);
        Node n = new Node(id, a);
        Network net = new Network(nextNetwork++);
        net.members.add(id);
        n.network = net.id;
        nodes.put(id, n);
        networks.put(net.id, net);
    }

    public void remove(long id) {
        Node n = nodes.remove(id);
        if (n == null) return;
        Network net = networks.get(n.network);
        net.members.remove(id);
        for (long other : n.links) {
            Node o = nodes.get(other);
            if (o != null) o.links.remove(id);
        }
        if (net.members.isEmpty()) networks.remove(net.id);
        else if (n.links.size() > 1) net.dirty = true; // removing a leaf can never split a network
    }

    public boolean connect(long a, long b) {
        if (a == b) return false;
        Node na = nodes.get(a), nb = nodes.get(b);
        if (na == null || nb == null) throw new IllegalArgumentException("unknown node");
        if (!na.links.add(b)) return false;
        nb.links.add(a);
        if (na.network != nb.network) merge(networks.get(na.network), networks.get(nb.network));
        return true;
    }

    public boolean disconnect(long a, long b) {
        Node na = nodes.get(a), nb = nodes.get(b);
        if (na == null || nb == null || !na.links.remove(b)) return false;
        nb.links.remove(a);
        networks.get(na.network).dirty = true;
        return true;
    }

    private void merge(Network x, Network y) {
        Network big = x.members.size() >= y.members.size() ? x : y;
        Network small = big == x ? y : x;
        for (long id : small.members) nodes.get(id).network = big.id;
        big.members.addAll(small.members);
        big.dirty |= small.dirty;
        networks.remove(small.id);
    }

    private void rebuild(Network net) {
        rebuilds++;
        Set<Long> unvisited = new LinkedHashSet<>(net.members);
        boolean first = true;
        while (!unvisited.isEmpty()) {
            long start = unvisited.iterator().next();
            Network target = first ? net : new Network(nextNetwork++);
            Set<Long> comp = new LinkedHashSet<>();
            ArrayDeque<Long> q = new ArrayDeque<>();
            q.add(start);
            unvisited.remove(start);
            while (!q.isEmpty()) {
                long id = q.poll();
                comp.add(id);
                for (long l : nodes.get(id).links) if (unvisited.remove(l)) q.add(l);
            }
            if (first) {
                net.members.clear();
                net.members.addAll(comp);
                net.dirty = false;
                first = false;
            } else {
                target.members.addAll(comp);
                networks.put(target.id, target);
            }
            for (long id : comp) nodes.get(id).network = target.id;
        }
    }

    /** Recomputes any split networks now (normally done lazily in {@link #tick()}). */
    public void settle() {
        for (Network n : new ArrayList<>(networks.values())) if (n.dirty) rebuild(n);
    }

    // ---- flow ---------------------------------------------------------------------------------------
    public List<NetworkStats> tick() {
        settle();
        List<NetworkStats> out = new ArrayList<>(networks.size());
        for (Network net : networks.values()) out.add(tickNetwork(net));
        return out;
    }

    private NetworkStats tickNetwork(Network net) {
        long generated = 0;
        long cap = Long.MAX_VALUE;
        TreeMap<Integer, List<PowerNodeAdapter>> byPriority = new TreeMap<>((a, b) -> Integer.compare(b, a));
        List<EnergyStorage> buffers = new ArrayList<>();
        for (long id : net.members) {
            PowerNodeAdapter a = nodes.get(id).adapter;
            switch (a.kind()) {
                case GENERATOR -> generated = sat(generated, Math.max(0, a.generation()));
                case CONSUMER -> { if (a.demand() > 0) byPriority.computeIfAbsent(a.priority(), k -> new ArrayList<>()).add(a); }
                case BUFFER -> { if (a.buffer() != null) buffers.add(a.buffer()); }
                case CONDUIT -> cap = Math.min(cap, Math.max(0, a.throughput()));
            }
        }
        long moveBudget = cap;
        long availableFromGen = generated;
        long discharged = 0, delivered = 0, unmet = 0;
        long bufferAvail = 0;
        for (EnergyStorage b : buffers) bufferAvail = sat(bufferAvail, b.extract(Long.MAX_VALUE, true));

        for (var tier : byPriority.values()) {
            long demand = 0;
            for (PowerNodeAdapter c : tier) demand = sat(demand, c.demand());
            long supply = Math.min(moveBudget, sat(availableFromGen, bufferAvail - discharged));
            long grant = Math.min(demand, supply);
            long[] shares = proportional(tier, grant);
            long fromGen = Math.min(grant, availableFromGen);
            long fromBuf = grant - fromGen;
            if (fromBuf > 0) {
                long got = drawBuffers(buffers, fromBuf);
                // buffers always cover what they advertised; trim defensively if an adapter lied
                if (got < fromBuf) {
                    grant = fromGen + got;
                    shares = proportional(tier, grant);
                }
                discharged += got;
            }
            availableFromGen -= fromGen;
            moveBudget -= grant;
            for (int i = 0; i < tier.size(); i++) tier.get(i).supply(shares[i]);
            delivered += grant;
            unmet += demand - grant;
        }
        // surplus generation charges buffers, limited by the move budget
        long charged = 0;
        long toCharge = Math.min(availableFromGen, moveBudget);
        for (EnergyStorage b : buffers) {
            if (toCharge <= 0) break;
            long c = b.insert(toCharge, false);
            charged += c;
            toCharge -= c;
        }
        long wasted = availableFromGen - charged;
        return new NetworkStats(net.id, net.members.size(), generated, discharged, delivered, charged, wasted, unmet,
                cap == Long.MAX_VALUE ? -1 : cap);
    }

    private static long drawBuffers(List<EnergyStorage> buffers, long amount) {
        long got = 0;
        for (EnergyStorage b : buffers) {
            if (got >= amount) break;
            got += b.extract(amount - got, false);
        }
        return got;
    }

    /** Splits {@code total} across consumers in proportion to demand; remainders go to the largest fractions. */
    static long[] proportional(List<PowerNodeAdapter> tier, long total) {
        int n = tier.size();
        long[] out = new long[n];
        long demand = 0;
        for (PowerNodeAdapter c : tier) demand = sat(demand, c.demand());
        if (total >= demand) {
            for (int i = 0; i < n; i++) out[i] = tier.get(i).demand();
            return out;
        }
        if (total <= 0) return out;
        double[] frac = new double[n];
        long given = 0;
        for (int i = 0; i < n; i++) {
            double exact = (double) tier.get(i).demand() * total / demand;
            out[i] = (long) Math.floor(exact);
            frac[i] = exact - out[i];
            given += out[i];
        }
        long rest = total - given;
        Integer[] order = new Integer[n];
        for (int i = 0; i < n; i++) order[i] = i;
        java.util.Arrays.sort(order, (a, b) -> Double.compare(frac[b], frac[a]));
        for (int k = 0; k < n && rest > 0; k++) {
            int i = order[k];
            if (out[i] < tier.get(i).demand()) {
                out[i]++;
                rest--;
            }
        }
        return out;
    }

    private static long sat(long a, long b) {
        long r = a + b;
        return ((a ^ r) & (b ^ r)) < 0 ? Long.MAX_VALUE : r;
    }

    // ---- queries ------------------------------------------------------------------------------------
    public int networkOf(long nodeId) {
        settle();
        Node n = nodes.get(nodeId);
        if (n == null) throw new IllegalArgumentException("unknown node " + nodeId);
        return n.network;
    }

    public int networkCount() {
        settle();
        return networks.size();
    }

    public int nodeCount() {
        return nodes.size();
    }

    public Collection<Long> members(int network) {
        settle();
        Network n = networks.get(network);
        return n == null ? List.of() : List.copyOf(n.members);
    }

    public long rebuilds() {
        return rebuilds;
    }
}
