"use client";

import React, { useState } from "react";
import { ShieldAlert, Filter, UserCheck, ChevronRight, AlertTriangle, CheckCircle, Clock } from "lucide-react";

interface CaseWorkflowTableProps {
  cases: any[];
  userRole?: string;
  userToken: string | null;
  onSelectCase: (caseId: string) => void;
  onRefresh: () => void;
}

export const CaseWorkflowTable: React.FC<CaseWorkflowTableProps> = ({
  cases,
  userRole,
  userToken,
  onSelectCase,
  onRefresh
}) => {
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");

  const safeCases = Array.isArray(cases) ? cases : [];

  const filteredCases = safeCases.filter(c => {
    if (statusFilter !== "ALL" && c.status !== statusFilter) return false;
    if (priorityFilter !== "ALL" && c.priority !== priorityFilter) return false;
    return true;
  });

  const handleStatusChange = async (caseId: string, newStatus: string) => {
    try {
      const res = await fetch(`http://localhost:8001/api/v1/cases/${caseId}/status`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": userToken ? `Bearer ${userToken}` : ""
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        onRefresh();
      }
    } catch (err) {
      console.error("Status update error:", err);
    }
  };

  const getStatusBadge = (statusStr: string) => {
    switch (statusStr) {
      case "NEW ALERT":
        return "bg-purple-500/20 text-purple-400 border-purple-500/40 animate-pulse";
      case "UNDER REVIEW":
        return "bg-blue-500/20 text-blue-400 border-blue-500/40";
      case "ESCALATED":
        return "bg-amber-500/20 text-amber-400 border-amber-500/40";
      case "BLOCKED":
        return "bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold";
      case "CLOSED_TP":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/40";
      case "CLOSED_FP":
        return "bg-slate-700/40 text-slate-400 border-slate-600";
      default:
        return "bg-slate-800 text-slate-300";
    }
  };

  return (
    <div className="bg-surface border border-border rounded-xl shadow-xl overflow-hidden">
      {/* Control Bar */}
      <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-4 bg-slate-900/60">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h3 className="text-base font-bold text-white">Investigation Case Workflow Queue</h3>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 text-xs font-mono">
            {filteredCases.length} Active Cases
          </span>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="NEW ALERT">New Alert</option>
            <option value="UNDER REVIEW">Under Review</option>
            <option value="ESCALATED">Escalated</option>
            <option value="BLOCKED">Blocked / Reported</option>
            <option value="CLOSED_TP">Closed (True Positive)</option>
            <option value="CLOSED_FP">Closed (False Positive)</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>
        </div>
      </div>

      {/* Case Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider font-semibold border-b border-border">
            <tr>
              <th className="py-3 px-4">Case ID</th>
              <th className="py-3 px-4">Priority</th>
              <th className="py-3 px-4">Target Wallet</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Flagged USD</th>
              <th className="py-3 px-4">Current Status</th>
              <th className="py-3 px-4">Assigned Analyst</th>
              <th className="py-3 px-4">Workflow Transition</th>
              <th className="py-3 px-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs text-slate-300">
            {filteredCases.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-10 text-center text-slate-500 font-sans">
                  No cases match the selected filter parameters.
                </td>
              </tr>
            ) : (
              filteredCases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                  {/* Case ID */}
                  <td className="py-3 px-4 whitespace-nowrap font-bold text-blue-400">
                    {c.id}
                  </td>

                  {/* Priority */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      c.priority === "CRITICAL" ? "bg-rose-500/20 text-rose-400 border border-rose-500/30" : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    }`}>
                      {c.priority}
                    </span>
                  </td>

                  {/* Wallet Address */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    {c.wallet_address.slice(0, 8)}...{c.wallet_address.slice(-4)}
                  </td>

                  {/* Risk Score */}
                  <td className="py-3 px-4 whitespace-nowrap font-bold text-white">
                    {c.risk_score} / 100
                  </td>

                  {/* Flagged USD */}
                  <td className="py-3 px-4 whitespace-nowrap text-emerald-400 font-semibold">
                    ${c.flagged_value_usd ? c.flagged_value_usd.toLocaleString() : "0"}
                  </td>

                  {/* Status Badge */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${getStatusBadge(c.status)}`}>
                      {c.status}
                    </span>
                  </td>

                  {/* Analyst */}
                  <td className="py-3 px-4 whitespace-nowrap font-sans text-xs text-slate-300">
                    <span className="flex items-center gap-1">
                      <UserCheck className="w-3.5 h-3.5 text-blue-400" /> {c.assigned_to_name || "Unassigned"}
                    </span>
                  </td>

                  {/* Status Transition Select Dropdown */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <select
                      value={c.status}
                      onChange={(e) => handleStatusChange(c.id, e.target.value)}
                      className="bg-slate-950 border border-slate-800 text-slate-300 text-[11px] rounded px-2 py-1 focus:outline-none"
                    >
                      <option value="NEW ALERT">NEW ALERT</option>
                      <option value="UNDER REVIEW">UNDER REVIEW</option>
                      <option value="ESCALATED">ESCALATED</option>
                      <option value="BLOCKED">BLOCKED / REPORTED</option>
                      <option value="CLOSED_TP">CLOSED (True Positive)</option>
                      <option value="CLOSED_FP">CLOSED (False Positive)</option>
                    </select>
                  </td>

                  {/* Action Drawer Button */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <button
                      onClick={() => onSelectCase(c.id)}
                      className="px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-500/30 rounded text-xs flex items-center gap-1 font-sans transition-all"
                    >
                      Audit <ChevronRight className="w-3 h-3" />
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
