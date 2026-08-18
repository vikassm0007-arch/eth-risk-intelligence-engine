"use client";

import React, { useEffect, useState } from "react";
import { X, ShieldAlert, AlertOctagon, CheckCircle2, ArrowRightLeft, Clock, ExternalLink } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { CytoscapeGraph } from "./CytoscapeGraph";

interface InvestigatorModalProps {
  walletAddress: string;
  onClose: () => void;
}

export const InvestigatorModal: React.FC<InvestigatorModalProps> = ({ walletAddress, onClose }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvestigation = async () => {
      try {
        setLoading(true);
        const res = await fetch(`http://localhost:8001/api/v1/investigate/${walletAddress}`);
        const result = await res.json();
        setData(result);
      } catch (err) {
        console.error("Failed to load investigation:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchInvestigation();
  }, [walletAddress]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-surface border border-border p-8 rounded-2xl max-w-lg w-full text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-bold text-white">Analyzing Wallet Graph & TreeSHAP Drivers...</h3>
          <p className="text-xs text-slate-400 mt-1 font-mono">{walletAddress}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const shapData = (data.shap_explanations || []).map((item: any) => ({
    name: item.feature,
    score: parseFloat((item.shap_value * 100).toFixed(1))
  }));

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-surface border border-border rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white bg-slate-800 p-2 rounded-lg transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Section */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white font-mono">{data.wallet_address}</h2>
              {data.is_sanctioned ? (
                <span className="px-3 py-1 bg-rose-500/20 border border-rose-500/40 text-rose-400 text-xs font-bold rounded-full flex items-center gap-1">
                  <AlertOctagon className="w-3.5 h-3.5" /> OFAC SANCTIONED
                </span>
              ) : (
                <span className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 text-xs font-bold rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> CLEAN ENTITY
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Recorded Activity: <span className="text-slate-200 font-semibold">{data.total_tx_count} transactions</span>
            </p>
          </div>

          {/* Risk Score Pill */}
          <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center gap-4">
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-semibold">Composite Risk</p>
              <p className={`text-2xl font-black ${
                data.composite_risk_score >= 90 ? 'text-rose-500' :
                data.composite_risk_score >= 70 ? 'text-amber-500' : 'text-emerald-400'
              }`}>
                {data.composite_risk_score.toFixed(1)} / 100
              </p>
            </div>
          </div>
        </div>

        {/* Grid Layout: SHAP Waterfall Plot & 2-Hop Network Graph */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* SHAP Waterfall Bar Chart */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
            <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-blue-400" /> SHAP Feature Driver Breakdown (%)
            </h4>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={shapData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <XAxis type="number" stroke="#64748b" fontSize={10} />
                  <YAxis type="category" dataKey="name" stroke="#cbd5e1" fontSize={10} width={130} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", borderRadius: "8px" }}
                    itemStyle={{ color: "#38bdf8", fontSize: "12px" }}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {shapData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.score > 40 ? "#ef4444" : "#3b82f6"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 2-Hop Network Graph */}
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
            <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-emerald-400" /> 2-Hop Transaction Network Graph
            </h4>
            {data.network_graph && <CytoscapeGraph graphData={data.network_graph} />}
          </div>
        </div>

        {/* Historical Timeline Table */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-purple-400" /> Wallet Transaction History Timeline
          </h4>
          <div className="overflow-x-auto max-h-48">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="py-2 px-3">Tx Hash</th>
                  <th className="py-2 px-3">Counterparty</th>
                  <th className="py-2 px-3">Value (ETH)</th>
                  <th className="py-2 px-3">Value (USD)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {(data.timeline || []).map((tx: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-2 px-3 text-blue-400">{tx.tx_hash.slice(0, 10)}...</td>
                    <td className="py-2 px-3 text-slate-300">{tx.counterparty.slice(0, 10)}...</td>
                    <td className="py-2 px-3 text-emerald-400 font-semibold">{tx.val_eth} ETH</td>
                    <td className="py-2 px-3 text-slate-400">${tx.val_usd.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
