"use client";

import React from "react";
import { Activity, ShieldAlert, Cpu, IndianRupee } from "lucide-react";

interface RiskMetricsProps {
  tps: number;
  totalProcessed: number;
  criticalCount: number;
  avgLatencyMs: number;
  totalInrMonitoredFormatted?: string;
  ethInrRateFormatted?: string;
}

export const RiskMetrics: React.FC<RiskMetricsProps> = ({
  tps,
  totalProcessed,
  criticalCount,
  avgLatencyMs,
  totalInrMonitoredFormatted = "₹4.85 Cr",
  ethInrRateFormatted = "₹2,75,000"
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {/* Card 1: INR Volume Monitored */}
      <div className="bg-surface border border-border p-4 rounded-xl flex items-center justify-between shadow-lg">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Volume Monitored (₹)</p>
          <h3 className="text-2xl font-bold text-emerald-400 mt-1">{totalInrMonitoredFormatted}</h3>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5">Rate: 1 ETH = {ethInrRateFormatted}</p>
        </div>
        <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
          <IndianRupee className="w-5 h-5" />
        </div>
      </div>

      {/* Card 2: Throughput & Total Scored */}
      <div className="bg-surface border border-border p-4 rounded-xl flex items-center justify-between shadow-lg">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Throughput & Scored</p>
          <h3 className="text-2xl font-bold text-white mt-1">{tps.toFixed(1)} <span className="text-xs font-normal text-slate-400">tx/s</span></h3>
          <p className="text-[10px] text-slate-400 mt-0.5">{totalProcessed.toLocaleString()} Total Scored</p>
        </div>
        <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20">
          <Activity className="w-5 h-5" />
        </div>
      </div>

      {/* Card 3: Avg Pipeline Latency */}
      <div className="bg-surface border border-border p-4 rounded-xl flex items-center justify-between shadow-lg">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">TreeSHAP SLA Latency</p>
          <h3 className="text-2xl font-bold text-emerald-400 mt-1">{avgLatencyMs.toFixed(1)} <span className="text-xs font-normal text-slate-400">ms (&lt;15ms)</span></h3>
          <p className="text-[10px] text-slate-400 mt-0.5">Real-time XAI Engine</p>
        </div>
        <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg border border-purple-500/20">
          <Cpu className="w-5 h-5" />
        </div>
      </div>

      {/* Card 4: Critical Alerts */}
      <div className="bg-surface border border-border p-4 rounded-xl flex items-center justify-between shadow-lg">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Critical/High Alerts</p>
          <h3 className="text-2xl font-bold text-rose-400 mt-1">{criticalCount}</h3>
          <p className="text-[10px] text-rose-400/80 mt-0.5">Automated Case Trigger</p>
        </div>
        <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg border border-rose-500/20">
          <ShieldAlert className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
