"use client";

import React, { useState } from "react";
import { X, Send, ShieldAlert, User, Clock, FileText, CheckCircle2, AlertOctagon, Download } from "lucide-react";

interface CaseDetailDrawerProps {
  caseData: any;
  userToken: string | null;
  onClose: () => void;
  onRefresh: () => void;
}

export const CaseDetailDrawer: React.FC<CaseDetailDrawerProps> = ({
  caseData,
  userToken,
  onClose,
  onRefresh
}) => {
  const [newNote, setNewNote] = useState("");
  const [loadingNote, setLoadingNote] = useState(false);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setLoadingNote(true);
    try {
      const res = await fetch(`http://localhost:8001/api/v1/cases/${caseData.id}/notes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": userToken ? `Bearer ${userToken}` : ""
        },
        body: JSON.stringify({ note_text: newNote })
      });
      if (res.ok) {
        setNewNote("");
        onRefresh();
      }
    } catch (err) {
      console.error("Failed to add note:", err);
    } finally {
      setLoadingNote(false);
    }
  };

  const handleExportPDF = () => {
    alert(`Exporting Audit Evidence Report for Case ${caseData.id} (PDF Generator)`);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-end">
      <div className="bg-surface border-l border-border max-w-xl w-full h-full flex flex-col p-6 shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-blue-400">{caseData.id}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                caseData.priority === "CRITICAL" ? "bg-rose-500/20 text-rose-400" : "bg-amber-500/20 text-amber-400"
              }`}>
                {caseData.priority}
              </span>
            </div>
            <h3 className="text-lg font-bold text-white mt-1">Investigator Case Audit</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportPDF}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1 font-semibold"
            >
              <Download className="w-4 h-4" /> Export PDF
            </button>
            <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-lg bg-slate-800">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Case Telemetry Summary */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 mb-6">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Target Wallet:</span>
            <span className="text-white font-mono font-semibold">{caseData.wallet_address}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Tx Hash:</span>
            <span className="text-blue-400 font-mono">{caseData.tx_hash ? caseData.tx_hash.slice(0, 14) + "..." : "N/A"}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Composite Risk Score:</span>
            <span className="text-rose-400 font-bold text-sm">{caseData.risk_score} / 100</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Flagged USD Volume:</span>
            <span className="text-emerald-400 font-bold">${caseData.flagged_value_usd ? caseData.flagged_value_usd.toLocaleString() : "0"}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Assigned Lead:</span>
            <span className="text-slate-200 font-semibold">{caseData.assigned_to_name || "Unassigned"}</span>
          </div>
        </div>

        {/* Investigator Notes Timeline */}
        <div className="flex-1 flex flex-col min-h-0 mb-6">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-blue-400" /> Investigator Audit Log & Notes Timeline
          </h4>

          <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
            {(!caseData.notes || caseData.notes.length === 0) ? (
              <p className="text-xs text-slate-500 italic p-4 text-center">No investigator notes recorded yet.</p>
            ) : (
              caseData.notes.map((n: any, idx: number) => (
                <div key={idx} className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                    <span className="font-semibold text-blue-300">{n.author_name}</span>
                    <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-xs text-slate-200">{n.note_text}</p>
                </div>
              ))
            )}
          </div>

          {/* Add Note Form */}
          <form onSubmit={handleAddNote} className="flex gap-2">
            <input
              type="text"
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Add investigator note or manual tag..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={loadingNote}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold flex items-center gap-1"
            >
              <Send className="w-3.5 h-3.5" /> Post
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
