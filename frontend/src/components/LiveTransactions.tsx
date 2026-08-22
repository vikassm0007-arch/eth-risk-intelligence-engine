"use client";

import React, { useState } from "react";
import { ShieldAlert, Pause, Play, Filter, Eye, ChevronRight, IndianRupee } from "lucide-react";

export interface TransactionItemINR {
  tx_hash: string;
  block_number: number;
  timestamp: number;
  from_address: string;
  to_address: string;
  value_eth: number;
  value_usd: number;
  value_inr: number;
  value_inr_formatted?: string;
  gas_price_gwei: number;
  gas_inr?: number;
  input_data: string;
  is_erc20: boolean;
  ml_probability: number;
  rule_risk_score: number;
  composite_risk_score: number;
  alert_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  reasons: string[];
  top_shap_drivers: Array<{ feature: string; shap_value: number; feature_value: number }>;
  execution_time_ms: number;
}

interface LiveTransactionsProps {
  transactions: TransactionItemINR[];
  isPaused: boolean;
  onTogglePause: () => void;
  onSelectWallet: (address: string) => void;
}

export const LiveTransactions: React.FC<LiveTransactionsProps> = ({
  transactions,
  isPaused,
  onTogglePause,
  onSelectWallet
}) => {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [minInrFilter, setMinInrFilter] = useState<number>(0);

  const filteredTx = transactions.filter(tx => {
    if (filterLevel !== "ALL" && tx.alert_level !== filterLevel) return false;
    if (minInrFilter > 0 && (tx.value_inr || 0) < minInrFilter) return false;
    return true;
  });

  const getBadgeStyle = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse";
      case "HIGH":
        return "bg-amber-500/20 text-amber-400 border-amber-500/40";
      case "MEDIUM":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    }
  };

  return (
    <div className="bg-surface border border-border rounded-xl shadow-xl overflow-hidden">
      {/* Table Header Bar */}
      <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-4 bg-slate-900/60">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg border border-amber-500/20">
            <IndianRupee className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Live EVM Stream (INR ₹ Localized)</h2>
            <p className="text-[11px] text-slate-400 font-mono">Dynamic ETH/INR Oracle • Sub-Second Latency</p>
          </div>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 text-xs font-mono ml-2">
            {filteredTx.length} items
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* INR Value Filter */}
          <select
            value={minInrFilter}
            onChange={(e) => setMinInrFilter(Number(e.target.value))}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none font-mono"
          >
            <option value={0}>All Values (₹)</option>
            <option value={100000}>Min ₹1 Lakh</option>
            <option value={1000000}>Min ₹10 Lakhs</option>
            <option value={10000000}>Min ₹1 Crore</option>
          </select>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1" />
            {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((level) => (
              <button
                key={level}
                onClick={() => setFilterLevel(level)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                  filterLevel === level
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {level}
              </button>
            ))}
          </div>

          {/* Pause / Resume Button */}
          <button
            onClick={onTogglePause}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isPaused
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30"
                : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
            }`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5 fill-amber-300" /> : <Pause className="w-3.5 h-3.5" />}
            {isPaused ? "RESUME STREAM" : "PAUSE"}
          </button>
        </div>
      </div>

      {/* Streaming Table */}
      <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider font-semibold border-b border-border z-10">
            <tr>
              <th className="py-3 px-4">Risk Level</th>
              <th className="py-3 px-4">Composite Score</th>
              <th className="py-3 px-4">Tx Hash</th>
              <th className="py-3 px-4">From Wallet</th>
              <th className="py-3 px-4">To Wallet</th>
              <th className="py-3 px-4">Value (₹ INR / ETH)</th>
              <th className="py-3 px-4">Gas Fee (₹)</th>
              <th className="py-3 px-4">SHAP Risk Explanation Drivers</th>
              <th className="py-3 px-4">Inference</th>
              <th className="py-3 px-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs text-slate-300">
            {filteredTx.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-12 text-center text-slate-500 font-sans">
                  Awaiting live Ethereum transaction payloads with INR valuations...
                </td>
              </tr>
            ) : (
              filteredTx.map((tx) => (
                <tr
                  key={tx.tx_hash}
                  className={`hover:bg-slate-800/50 transition-colors ${
                    tx.alert_level === "CRITICAL" ? "bg-rose-950/20" : ""
                  }`}
                >
                  {/* Alert Badge */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span
                      className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${getBadgeStyle(
                        tx.alert_level
                      )}`}
                    >
                      {tx.alert_level}
                    </span>
                  </td>

                  {/* Composite Risk Score */}
                  <td className="py-3 px-4 whitespace-nowrap font-bold text-white">
                    {tx.composite_risk_score.toFixed(1)} <span className="text-[10px] text-slate-500 font-normal">/ 100</span>
                  </td>

                  {/* Tx Hash */}
                  <td className="py-3 px-4 whitespace-nowrap text-blue-400">
                    {tx.tx_hash.slice(0, 10)}...
                  </td>

                  {/* From Wallet */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <button
                      onClick={() => onSelectWallet(tx.from_address)}
                      className="text-slate-200 hover:text-blue-400 underline decoration-slate-700 underline-offset-2 flex items-center gap-1 group"
                    >
                      {tx.from_address.slice(0, 8)}...{tx.from_address.slice(-4)}
                      <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  </td>

                  {/* To Wallet */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <button
                      onClick={() => onSelectWallet(tx.to_address)}
                      className="text-slate-300 hover:text-blue-400 underline decoration-slate-700 underline-offset-2"
                    >
                      {tx.to_address.slice(0, 8)}...{tx.to_address.slice(-4)}
                    </button>
                  </td>

                  {/* Value (Dual ETH & INR) */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <div className="font-bold text-emerald-400 text-sm">
                      {tx.value_inr_formatted || `₹${(tx.value_inr || 0).toLocaleString()}`}
                    </div>
                    <div className="text-[10px] text-slate-400">{tx.value_eth} ETH</div>
                  </td>

                  {/* Gas Fee in INR */}
                  <td className="py-3 px-4 whitespace-nowrap text-amber-300 font-semibold">
                    ₹{tx.gas_inr ? tx.gas_inr.toFixed(2) : (tx.gas_price_gwei * 0.4).toFixed(2)}
                  </td>

                  {/* SHAP / Reasons */}
                  <td className="py-3 px-4 max-w-xs font-sans text-xs">
                    {tx.reasons && tx.reasons.length > 0 ? (
                      <div className="space-y-1">
                        {tx.reasons.slice(0, 2).map((reason, idx) => (
                          <div key={idx} className="text-slate-300 text-[11px] flex items-start gap-1">
                            <span className="text-amber-400 font-bold">•</span> {reason}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-500 italic">Standard EVM transfer</span>
                    )}
                  </td>

                  {/* Pipeline Latency */}
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400 text-[11px]">
                    {tx.execution_time_ms} ms
                  </td>

                  {/* Action Button */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <button
                      onClick={() => onSelectWallet(tx.from_address)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-blue-600/30 text-slate-300 hover:text-blue-300 border border-slate-700 rounded-lg text-xs font-sans flex items-center gap-1 transition-all"
                    >
                      <Eye className="w-3.5 h-3.5" /> Audit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
