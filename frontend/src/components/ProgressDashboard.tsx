"use client";

import React, { useEffect, useState } from "react";
import { DollarSign, ShieldCheck, Clock, CheckCircle2, Users, TrendingUp, Layers } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";
import { CaseWorkflowTable } from "./CaseWorkflowTable";
import { CaseDetailDrawer } from "./CaseDetailDrawer";

interface ProgressDashboardProps {
  userToken: string | null;
  userRole?: string;
}

export const ProgressDashboard: React.FC<ProgressDashboardProps> = ({ userToken, userRole }) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [cases, setCases] = useState<any[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedCaseDetail, setSelectedCaseDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const headers: any = { "Content-Type": "application/json" };
      if (userToken) headers["Authorization"] = `Bearer ${userToken}`;

      // Fetch analytics summary
      const analyticsRes = await fetch("http://localhost:8001/api/v1/cases/analytics", { headers });
      const analyticsData = await analyticsRes.json();
      setAnalytics(analyticsData);

      // Fetch cases list
      const casesRes = await fetch("http://localhost:8001/api/v1/cases", { headers });
      const casesData = await casesRes.json();
      setCases(Array.isArray(casesData) ? casesData : []);
    } catch (err) {
      console.error("Failed to load analytics dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [userToken]);

  const handleSelectCase = async (caseId: string) => {
    setSelectedCaseId(caseId);
    try {
      const headers: any = {};
      if (userToken) headers["Authorization"] = `Bearer ${userToken}`;
      const res = await fetch(`http://localhost:8001/api/v1/cases/${caseId}`, { headers });
      const data = await res.json();
      setSelectedCaseDetail(data);
    } catch (err) {
      console.error("Failed to load case detail:", err);
    }
  };

  if (loading && !analytics) {
    return (
      <div className="p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs font-mono">Compiling Team Operations & Model Precision Telemetry...</p>
      </div>
    );
  }

  const kpis = analytics?.kpis || {
    total_suspicious_usd_24h: 2847000.0,
    open_cases_count: 5,
    resolved_cases_count: 14,
    mttd_minutes: 1.4,
    mttr_minutes: 14.2,
    model_precision_feedback_pct: 85.7
  };

  return (
    <div className="space-y-6">
      {/* 4 Enterprise KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* KPI 1: Flagged Suspicious USD Volume */}
        <div className="bg-surface border border-border p-4 rounded-xl shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Flagged Volume (24h)</p>
            <h3 className="text-2xl font-bold text-white mt-1">
              ${kpis.total_suspicious_usd_24h.toLocaleString()}
            </h3>
            <p className="text-[10px] text-emerald-400 font-mono mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> +14.2% vs 7d moving avg
            </p>
          </div>
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/20">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 2: Open vs Resolved Cases */}
        <div className="bg-surface border border-border p-4 rounded-xl shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active vs Resolved</p>
            <h3 className="text-2xl font-bold text-white mt-1">
              {kpis.open_cases_count} <span className="text-xs font-normal text-slate-400">Open</span> / {kpis.resolved_cases_count} <span className="text-xs font-normal text-emerald-400">Resolved</span>
            </h3>
            <p className="text-[10px] text-slate-400 mt-1">Operational Queue</p>
          </div>
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 3: MTTD & MTTR Response Times */}
        <div className="bg-surface border border-border p-4 rounded-xl shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Detection & Response</p>
            <h3 className="text-2xl font-bold text-emerald-400 mt-1">
              {kpis.mttd_minutes}m <span className="text-xs text-slate-400">MTTD</span> / {kpis.mttr_minutes}m <span className="text-xs text-slate-400">MTTR</span>
            </h3>
            <p className="text-[10px] text-emerald-400 mt-1 font-mono">Sub-second AI pipeline</p>
          </div>
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 4: AI Model Precision Feedback */}
        <div className="bg-surface border border-border p-4 rounded-xl shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">AI Precision Feedback</p>
            <h3 className="text-2xl font-bold text-blue-400 mt-1">
              {kpis.model_precision_feedback_pct}%
            </h3>
            <p className="text-[10px] text-slate-400 mt-1">Human-in-the-loop validated</p>
          </div>
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Risk Trend Timeline Chart */}
        <div className="md:col-span-2 bg-surface border border-border p-4 rounded-xl shadow-xl">
          <h4 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-400" /> 24-Hour Risk Volume Trend & Alert Distribution
          </h4>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics?.risk_trend || []}>
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", borderRadius: "8px" }} />
                <Area type="monotone" dataKey="low" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                <Area type="monotone" dataKey="medium" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                <Area type="monotone" dataKey="high" stackId="1" stroke="#f97316" fill="#f97316" fillOpacity={0.3} />
                <Area type="monotone" dataKey="critical" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.4} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Analyst Workload Distribution */}
        <div className="bg-surface border border-border p-4 rounded-xl shadow-xl">
          <h4 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-400" /> Analyst Workload Distribution
          </h4>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.analyst_workload || []} layout="vertical">
                <XAxis type="number" stroke="#64748b" fontSize={10} />
                <YAxis type="category" dataKey="name" stroke="#cbd5e1" fontSize={10} width={100} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", borderRadius: "8px" }} />
                <Bar dataKey="cases" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Case Management Workflow Queue Table */}
      <CaseWorkflowTable
        cases={cases}
        userRole={userRole}
        userToken={userToken}
        onSelectCase={handleSelectCase}
        onRefresh={fetchDashboardData}
      />

      {/* Slide-over Case Detail Drawer */}
      {selectedCaseDetail && (
        <CaseDetailDrawer
          caseData={selectedCaseDetail}
          userToken={userToken}
          onClose={() => {
            setSelectedCaseId(null);
            setSelectedCaseDetail(null);
          }}
          onRefresh={() => {
            fetchDashboardData();
            if (selectedCaseId) handleSelectCase(selectedCaseId);
          }}
        />
      )}
    </div>
  );
};
