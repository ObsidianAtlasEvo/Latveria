package com.doomsovereign.core.research;

import java.util.ArrayDeque;
import java.util.Collection;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** The research graph; validated to be acyclic with no dangling references. */
public final class ResearchTree {
    private final Map<String, ResearchNode> nodes = new LinkedHashMap<>();

    public ResearchTree(Collection<ResearchNode> all) {
        for (ResearchNode n : all)
            if (nodes.putIfAbsent(n.id(), n) != null) throw new IllegalArgumentException("duplicate node " + n.id());
        for (ResearchNode n : nodes.values())
            for (String p : n.prerequisites())
                if (!nodes.containsKey(p)) throw new IllegalArgumentException(n.id() + " requires unknown node " + p);
        checkAcyclic();
    }

    private void checkAcyclic() {
        Map<String, Integer> colour = new HashMap<>();
        for (String start : nodes.keySet()) {
            if (colour.getOrDefault(start, 0) != 0) continue;
            Deque<String[]> stack = new ArrayDeque<>();
            stack.push(new String[]{start, "0"});
            while (!stack.isEmpty()) {
                String[] top = stack.peek();
                String id = top[0];
                if (top[1].equals("0")) {
                    colour.put(id, 1);
                    top[1] = "1";
                    for (String p : nodes.get(id).prerequisites()) {
                        int c = colour.getOrDefault(p, 0);
                        if (c == 1) throw new IllegalArgumentException("research cycle through " + p);
                        if (c == 0) stack.push(new String[]{p, "0"});
                    }
                } else {
                    colour.put(id, 2);
                    stack.pop();
                }
            }
        }
    }

    public ResearchNode node(String id) {
        return nodes.get(id);
    }

    public Collection<ResearchNode> nodes() {
        return Collections.unmodifiableCollection(nodes.values());
    }

    /** All transitive prerequisites of a node. */
    public Set<String> ancestors(String id) {
        Set<String> out = new HashSet<>();
        Deque<String> q = new ArrayDeque<>(nodes.get(id).prerequisites());
        while (!q.isEmpty()) {
            String p = q.pop();
            if (out.add(p)) q.addAll(nodes.get(p).prerequisites());
        }
        return out;
    }

    /** Nodes in an order where every prerequisite precedes its dependants. */
    public List<ResearchNode> topological() {
        List<ResearchNode> out = new java.util.ArrayList<>();
        Set<String> done = new HashSet<>();
        while (out.size() < nodes.size()) {
            for (ResearchNode n : nodes.values()) {
                if (!done.contains(n.id()) && done.containsAll(n.prerequisites())) {
                    out.add(n);
                    done.add(n.id());
                }
            }
        }
        return out;
    }
}
