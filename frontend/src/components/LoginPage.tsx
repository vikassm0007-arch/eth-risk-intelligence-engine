"use client";

import React, { useState } from "react";
import { Shield, Lock, Wallet, Mail, AlertCircle, ArrowRight, UserCheck } from "lucide-react";

interface LoginPageProps {
  onLoginSuccess: (user: any, token: string) => void;
  onClose: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onClose }) => {
  const [tab, setTab] = useState<"standard" | "siwe">("standard");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStandardLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8001/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      onLoginSuccess(data.user, data.access_token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoPreset = async (demoEmail: string, demoRole: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8001/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: demoEmail, password: demoEmail.includes("admin") ? "admin123" : (demoEmail.includes("senior") ? "senior123" : "junior123") })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      onLoginSuccess(data.user, data.access_token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSIWELogin = async () => {
    setLoading(true);
    setError(null);
    try {
      let addr = walletAddress.trim();
      if (!addr) {
        // Fallback demo Metamask address if browser extension not connected
        addr = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d";
      }

      // 1. Fetch Nonce
      const nonceRes = await fetch(`http://localhost:8001/api/v1/auth/siwe/nonce?address=${addr}`);
      const nonceData = await nonceRes.json();

      // 2. Mock SIWE Verification call
      const verifyRes = await fetch("http://localhost:8001/api/v1/auth/siwe/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wallet_address: addr,
          signature: "0xmock_ecdsa_signature_hash_proof",
          message: nonceData.message
        })
      });
      const data = await verifyRes.json();
      if (!verifyRes.ok) throw new Error(data.detail || "SIWE authentication failed");
      onLoginSuccess(data.user, data.access_token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Enterprise Portal Authentication</h2>
            <p className="text-xs text-slate-400">Role-Based Access Control & SIWE Web3 Login</p>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 mb-6 text-xs font-semibold">
          <button
            onClick={() => setTab("standard")}
            className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
              tab === "standard" ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Mail className="w-3.5 h-3.5" /> Email & Password
          </button>
          <button
            onClick={() => setTab("siwe")}
            className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
              tab === "siwe" ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Wallet className="w-3.5 h-3.5 text-amber-400" /> Web3 SIWE Wallet
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2 mb-4">
            <AlertCircle className="w-4 h-4 shrink-0" /> {error}
          </div>
        )}

        {tab === "standard" ? (
          <form onSubmit={handleStandardLogin} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">Enterprise Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@risk.eth"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-2"
            >
              {loading ? "Authenticating..." : "Login to Portal"} <ArrowRight className="w-4 h-4" />
            </button>

            {/* Quick Demo Role Presets */}
            <div className="mt-4 pt-4 border-t border-slate-800">
              <p className="text-[11px] text-slate-400 mb-2 font-medium">Quick Demo Role Login:</p>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleDemoPreset("admin@risk.eth", "Admin")}
                  className="p-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-[10px] text-purple-300 font-bold"
                >
                  Admin
                </button>
                <button
                  type="button"
                  onClick={() => handleDemoPreset("senior@risk.eth", "Senior Analyst")}
                  className="p-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg text-[10px] text-blue-300 font-bold"
                >
                  Senior Lead
                </button>
                <button
                  type="button"
                  onClick={() => handleDemoPreset("junior@risk.eth", "Junior Analyst")}
                  className="p-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 rounded-lg text-[10px] text-emerald-300 font-bold"
                >
                  Junior Analyst
                </button>
              </div>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">Ethereum Wallet Address (Metamask)</label>
              <input
                type="text"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder="0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <button
              onClick={handleSIWELogin}
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white text-xs font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-2"
            >
              <Wallet className="w-4 h-4" /> {loading ? "Verifying ECDSA Signature..." : "SIWE Sign-In with Metamask"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
