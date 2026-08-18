"use client";

import React, { useEffect, useState, useRef } from "react";
import { Header } from "@/components/Header";
import { RiskMetrics } from "@/components/RiskMetrics";
import { LiveFeed, TransactionItem } from "@/components/LiveFeed";
import { InvestigatorModal } from "@/components/InvestigatorModal";
import { LoginPage } from "@/components/LoginPage";
import { ProgressDashboard } from "@/components/ProgressDashboard";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"live" | "analytics">("live");
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);

  // Authentication State
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [userToken, setUserToken] = useState<string | null>(null);

  // Telemetry metrics
  const [stats, setStats] = useState({
    tps: 3.2,
    totalProcessed: 0,
    criticalCount: 0,
    avgLatencyMs: 6.9
  });

  const wsRef = useRef<WebSocket | null>(null);
  const isPausedRef = useRef(isPaused);
  isPausedRef.current = isPaused;

  useEffect(() => {
    // Check if token exists in localStorage
    const savedToken = localStorage.getItem("evm_risk_token");
    const savedUser = localStorage.getItem("evm_risk_user");
    if (savedToken && savedUser) {
      setUserToken(savedToken);
      setCurrentUser(JSON.parse(savedUser));
    }

    // Connect to WebSocket backend on port 8001
    const wsUrl = "ws://localhost:8001/ws/live-stream";
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      console.log("Connected to Real-Time WebSocket Risk Stream on port 8001");
      setWsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "NEW_TRANSACTION" && payload.data) {
          if (isPausedRef.current) return;

          const newTx: TransactionItem = payload.data;
          setTransactions((prev) => [newTx, ...prev.slice(0, 99)]);

          setStats((prev) => ({
            ...prev,
            totalProcessed: prev.totalProcessed + 1,
            criticalCount: prev.criticalCount + (newTx.alert_level === "CRITICAL" || newTx.alert_level === "HIGH" ? 1 : 0),
            tps: parseFloat((3.0 + Math.random() * 1.5).toFixed(1)),
            avgLatencyMs: parseFloat(((prev.avgLatencyMs * 9 + newTx.execution_time_ms) / 10).toFixed(1))
          }));
        }
      } catch (err) {
        console.error("WS Parse Error:", err);
      }
    };

    socket.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      socket.close();
    };
  }, []);

  const handleLoginSuccess = (user: any, token: string) => {
    setCurrentUser(user);
    setUserToken(token);
    localStorage.setItem("evm_risk_token", token);
    localStorage.setItem("evm_risk_user", JSON.stringify(user));
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setUserToken(null);
    localStorage.removeItem("evm_risk_token");
    localStorage.removeItem("evm_risk_user");
  };

  const handleTriggerAttack = async (attackType: string) => {
    try {
      await fetch(`http://localhost:8001/api/v1/trigger-attack?attack_type=${attackType}`, {
        method: "POST"
      });
    } catch (err) {
      console.error("Trigger Attack Error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      {/* Header */}
      <Header
        wsConnected={wsConnected}
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        currentUser={currentUser}
        onOpenLogin={() => setShowLoginModal(true)}
        onLogout={handleLogout}
        onTriggerAttack={handleTriggerAttack}
      />

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === "live" ? (
          <>
            {/* Risk Telemetry Metrics Bar */}
            <RiskMetrics
              tps={stats.tps}
              totalProcessed={stats.totalProcessed}
              criticalCount={stats.criticalCount}
              avgLatencyMs={stats.avgLatencyMs}
            />

            {/* Live Streaming Feed Table */}
            <LiveFeed
              transactions={transactions}
              isPaused={isPaused}
              onTogglePause={() => setIsPaused(!isPaused)}
              onSelectWallet={(addr) => setSelectedWallet(addr)}
            />
          </>
        ) : (
          /* Case Management & Operational Progress Dashboard */
          <ProgressDashboard
            userToken={userToken}
            userRole={currentUser?.role}
          />
        )}
      </main>

      {/* Wallet Investigator Modal */}
      {selectedWallet && (
        <InvestigatorModal
          walletAddress={selectedWallet}
          onClose={() => setSelectedWallet(null)}
        />
      )}

      {/* Enterprise Authentication Modal */}
      {showLoginModal && (
        <LoginPage
          onLoginSuccess={handleLoginSuccess}
          onClose={() => setShowLoginModal(false)}
        />
      )}
    </div>
  );
}
