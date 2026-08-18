"use client";

import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

interface GraphData {
  nodes: Array<{ data: { id: string; label: string; isTarget?: boolean; isSanctioned?: boolean } }>;
  edges: Array<{ data: { source: string; target: string; label: string } }>;
}

interface CytoscapeGraphProps {
  graphData: GraphData;
}

export const CytoscapeGraph: React.FC<CytoscapeGraphProps> = ({ graphData }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Safely cleanup previous instance if any
    if (cyRef.current) {
      try {
        cyRef.current.stop();
        cyRef.current.destroy();
        cyRef.current = null;
      } catch (err) {
        // Ignore destruction race conditions
      }
    }

    // Transform data format for Cytoscape.js
    const elements = [
      ...graphData.nodes.map(n => ({
        data: {
          id: n.data.id,
          label: n.data.label,
          color: n.data.isSanctioned ? "#ef4444" : (n.data.isTarget ? "#3b82f6" : "#10b981")
        }
      })),
      ...graphData.edges.map(e => ({
        data: {
          source: e.data.source,
          target: e.data.target,
          label: e.data.label
        }
      }))
    ];

    try {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements: elements,
        style: [
          {
            selector: "node",
            style: {
              "background-color": "data(color)",
              "label": "data(label)",
              "color": "#ffffff",
              "font-size": "10px",
              "text-valign": "bottom",
              "text-margin-y": 5,
              "width": 28,
              "height": 28,
              "border-width": 2,
              "border-color": "#ffffff"
            }
          },
          {
            selector: "edge",
            style: {
              "width": 2,
              "line-color": "#475569",
              "target-arrow-color": "#475569",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier"
            }
          }
        ],
        layout: {
          name: "concentric",
          animate: false,
          padding: 20
        }
      });
    } catch (err) {
      console.error("Cytoscape initialization error:", err);
    }

    return () => {
      if (cyRef.current) {
        try {
          cyRef.current.stop();
          cyRef.current.destroy();
          cyRef.current = null;
        } catch (err) {
          // Prevent React 18 cleanup exception
        }
      }
    };
  }, [graphData]);

  return (
    <div className="w-full h-64 bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden">
      <div ref={containerRef} className="w-full h-full" />
      <div className="absolute bottom-2 left-2 flex items-center gap-3 bg-slate-900/80 px-3 py-1 rounded-md text-[10px] text-slate-400 border border-slate-800">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" /> Target Wallet</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Counterparty</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" /> OFAC Sanctioned</span>
      </div>
    </div>
  );
};
