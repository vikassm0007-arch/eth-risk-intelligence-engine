"use client";

import React, { useState } from "react";
import { ShieldAlert, Activity, Zap, Play, AlertTriangle } from "lucide-react";

interface HeaderProps {
  wsConnected: boolean;
  onTriggerAttack: (attackType: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ wsConnected, onTriggerAttack }) => {
  const [isTriggering, setIsTriggering] = useState(false);

  const handleSimulate = async (type: string) => {
    setIsTriggering(true);
    await onTriggerAttack(type);
    setTimeout(() => setIsTriggering(false), 500);
  };

  return (
    <header className="border-b border-border bg-surface/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
          <ShieldAlert className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            EVM Risk Intelligence Platform
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Sub-Second Streaming AI • XGBoost + TreeSHAP • Real-Time Feature Store
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-medium">
          <span className={`w-2.5 h-2.5 rounded-full ${wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className={wsConnected ? "text-emerald-400" : "text-rose-400"}>
            {wsConnected ? "LIVE STREAM ACTIVE" : "DISCONNECTED"}
          </span>
        </div>

        {/* Simulate Attack Dropdown / Buttons */}
        <div className="flex items-center gap-2 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-semibold px-2 flex items-center gap-1">
            <Zap className="w-3.5 h-3.5 text-amber-400" /> Demo Attacks:
          </span>
          <button
            onClick={() => handleSimulate("TORNADO_SANCTION")}
            disabled={isTriggering}
            className="px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 text-xs font-semibold rounded-lg border border-rose-500/30 transition-all flex items-center gap-1.5"
          >
            <AlertTriangle className="w-3 h-3" /> Tornado Cash
          </button>
          <button
            onClick={() => handleSimulate("SUDDEN_DRAIN")}
            disabled={isTriggering}
            className="px-3 py-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 text-xs font-semibold rounded-lg border border-amber-500/30 transition-all flex items-center gap-1.5"
          >
            <Zap className="w-3 h-3" /> Sudden Drain
          </button>
          <button
            onClick={() => handleSimulate("VELOCITY_BURST")}
            disabled={isTriggering}
            className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-xs font-semibold rounded-lg border border-purple-500/30 transition-all flex items-center gap-1.5"
          >
            <Activity className="w-3 h-3" /> Burst Velocity
          </button>
        </div>
      </div>
    </header>
  );
};
