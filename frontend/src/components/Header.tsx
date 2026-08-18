"use client";

import React, { useState } from "react";
import { ShieldAlert, Activity, Zap, AlertTriangle, UserCheck, LogIn, LogOut, LayoutDashboard, Radio } from "lucide-react";

interface HeaderProps {
  wsConnected: boolean;
  activeTab: "live" | "analytics";
  onChangeTab: (tab: "live" | "analytics") => void;
  currentUser: any;
  onOpenLogin: () => void;
  onLogout: () => void;
  onTriggerAttack: (attackType: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  wsConnected,
  activeTab,
  onChangeTab,
  currentUser,
  onOpenLogin,
  onLogout,
  onTriggerAttack
}) => {
  const [isTriggering, setIsTriggering] = useState(false);

  const handleSimulate = async (type: string) => {
    setIsTriggering(true);
    await onTriggerAttack(type);
    setTimeout(() => setIsTriggering(false), 500);
  };

  return (
    <header className="border-b border-border bg-surface/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
      {/* Title & Navigation Tabs */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              EVM Risk Intelligence Platform
            </h1>
            <p className="text-xs text-slate-400 font-mono">
              Sub-Second Streaming AI • XGBoost + TreeSHAP • RBAC Case Workflow
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
          <button
            onClick={() => onChangeTab("live")}
            className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === "live" ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Radio className="w-3.5 h-3.5" /> Live Stream
          </button>
          <button
            onClick={() => onChangeTab("analytics")}
            className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === "analytics" ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5 text-amber-400" /> Case Progress & Analytics
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-medium">
          <span className={`w-2.5 h-2.5 rounded-full ${wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className={wsConnected ? "text-emerald-400" : "text-rose-400"}>
            {wsConnected ? "STREAM LIVE" : "DISCONNECTED"}
          </span>
        </div>

        {/* Demo Attack Trigger */}
        <div className="flex items-center gap-2 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-semibold px-2 flex items-center gap-1">
            <Zap className="w-3.5 h-3.5 text-amber-400" /> Attacks:
          </span>
          <button
            onClick={() => handleSimulate("TORNADO_SANCTION")}
            disabled={isTriggering}
            className="px-2.5 py-1 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 text-xs font-semibold rounded-lg border border-rose-500/30 transition-all flex items-center gap-1"
          >
            <AlertTriangle className="w-3 h-3" /> Tornado
          </button>
          <button
            onClick={() => handleSimulate("SUDDEN_DRAIN")}
            disabled={isTriggering}
            className="px-2.5 py-1 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 text-xs font-semibold rounded-lg border border-amber-500/30 transition-all flex items-center gap-1"
          >
            <Zap className="w-3 h-3" /> Drain
          </button>
        </div>

        {/* User Auth & Role Pill */}
        {currentUser ? (
          <div className="flex items-center gap-3 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800">
            <div className="text-right">
              <p className="text-xs font-bold text-white leading-none">
                {currentUser.email || (currentUser.wallet_address ? currentUser.wallet_address.slice(0, 6) + "..." : "User")}
              </p>
              <span className="text-[10px] text-purple-400 font-semibold uppercase">{currentUser.role}</span>
            </div>
            <button
              onClick={onLogout}
              className="p-1.5 bg-slate-800 hover:bg-rose-600/20 text-slate-400 hover:text-rose-400 rounded-lg transition-all"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenLogin}
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition-all shadow-lg flex items-center gap-1.5"
          >
            <LogIn className="w-4 h-4" /> Portal Auth
          </button>
        )}
      </div>
    </header>
  );
};
