"use client";

import React, { useEffect, useState, useRef } from "react";
import { Header } from "@/components/Header";
import { RiskMetrics } from "@/components/RiskMetrics";
import { LiveTransactions, TransactionItemINR } from "@/components/LiveTransactions";
import { InvestigatorModal } from "@/components/InvestigatorModal";
import { LoginPage } from "@/components/LoginPage";
import { ProgressDashboard } from "@/components/ProgressDashboard";

const INITIAL_TRANSACTIONS: TransactionItemINR[] = [
  {
    tx_hash: "0x8f3c49a12b07e8910d54316c28f99e2110293847561a0b3c4d5e6f7a8b9c0d1e",
    block_number: 19582041,
    timestamp: Date.now() / 1000 - 12,
    from_address: "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    to_address: "0x28c6c06298d514db089934071355e5743bf21d60",
    value_eth: 1.45,
    value_usd: 3494.50,
    value_inr: 398750.00,
    value_inr_formatted: "₹3.98 Lakh",
    gas_price_gwei: 22.4,
    gas_inr: 246.40,
    input_data: "0x38ed1739",
    is_erc20: true,
    ml_probability: 0.12,
    rule_risk_score: 10.0,
    composite_risk_score: 11.4,
    alert_level: "LOW",
    reasons: ["Standard Uniswap router interaction"],
    top_shap_drivers: [{ feature: "Account Age", shap_value: -0.15, feature_value: 450 }],
    execution_time_ms: 6.4
  },
  {
    tx_hash: "0x1a9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e",
    block_number: 19582040,
    timestamp: Date.now() / 1000 - 28,
    from_address: "0x3cffd56b47b7b41c56258d9c7731abdc360e0739",
    to_address: "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
    value_eth: 12.50,
    value_usd: 30125.00,
    value_inr: 3437500.00,
    value_inr_formatted: "₹34.38 Lakh",
    gas_price_gwei: 145.0,
    gas_inr: 1595.00,
    input_data: "0xb214faa5",
    is_erc20: false,
    ml_probability: 0.98,
    rule_risk_score: 100.0,
    composite_risk_score: 99.4,
    alert_level: "CRITICAL",
    reasons: ["CRITICAL: Sanctioned OFAC / Tornado Cash Entity interaction (+100)"],
    top_shap_drivers: [{ feature: "Sanctioned Entity Flag", shap_value: 0.85, feature_value: 1 }],
    execution_time_ms: 7.1
  }
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<"live" | "analytics">("live");
  const [transactions, setTransactions] = useState<TransactionItemINR[]>(INITIAL_TRANSACTIONS);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);

  // Authentication State
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [userToken, setUserToken] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState<boolean>(true);

  // Telemetry metrics & INR values
  const [stats, setStats] = useState({
    tps: 3.2,
    totalProcessed: 2,
    criticalCount: 1,
    avgLatencyMs: 6.9,
    totalInrMonitoredFormatted: "₹4.85 Cr",
    ethInrRateFormatted: "₹2,75,000"
  });

  const wsRef = useRef<WebSocket | null>(null);
  const isPausedRef = useRef(isPaused);
  isPausedRef.current = isPaused;

  useEffect(() => {
    // 1. Check if token exists in localStorage
    const savedToken = localStorage.getItem("evm_risk_token");
    const savedUser = localStorage.getItem("evm_risk_user");
    if (savedToken && savedUser) {
      setUserToken(savedToken);
      setCurrentUser(JSON.parse(savedUser));
    }
    setCheckingAuth(false);

    // 2. Connect to WebSocket backend on port 8000 with auto-reconnect
    let socket: WebSocket | null = null;
    let reconnectTimer: any = null;

    const connectWebSocket = () => {
      try {
        const wsUrl = "ws://localhost:8000/ws/live-transactions";
        socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          console.log("Connected to Real-Time WebSocket Risk Stream on port 8000");
          setWsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload.type === "SYSTEM_INFO" && payload.stats) {
              setStats((prev) => ({
                ...prev,
                totalInrMonitoredFormatted: payload.stats.total_inr_monitored || prev.totalInrMonitoredFormatted,
                ethInrRateFormatted: payload.stats.eth_inr_rate || prev.ethInrRateFormatted
              }));
            }

            if (payload.type === "NEW_TRANSACTION" && payload.data) {
              if (isPausedRef.current) return;

              const newTx: TransactionItemINR = payload.data;
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
          reconnectTimer = setTimeout(connectWebSocket, 2000);
        };

        socket.onerror = () => {
          setWsConnected(false);
        };
      } catch (err) {
        setWsConnected(false);
        reconnectTimer = setTimeout(connectWebSocket, 2000);
      }
    };

    connectWebSocket();

    return () => {
      if (socket) socket.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  const handleLoginSuccess = (user: any, token: string) => {
    setCurrentUser(user);
    setUserToken(token);
    localStorage.setItem("evm_risk_token", token);
    localStorage.setItem("evm_risk_user", JSON.stringify(user));
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setUserToken(null);
    localStorage.removeItem("evm_risk_token");
    localStorage.removeItem("evm_risk_user");
  };

  const handleTriggerAttack = async (attackType: string) => {
    setIsPaused(false);
    try {
      await fetch(`http://localhost:8000/api/v1/trigger-attack?attack_type=${attackType}`, {
        method: "POST"
      });
    } catch (err) {
      console.error("Trigger Attack Error:", err);
    }
  };

  // Auth Wall: If user is not logged in, display full-page Authentication Portal Interface first!
  if (!checkingAuth && !currentUser) {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        isFullPage={true}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      {/* Header */}
      <Header
        wsConnected={wsConnected}
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        currentUser={currentUser}
        onOpenLogin={() => {}}
        onLogout={handleLogout}
        onTriggerAttack={handleTriggerAttack}
      />

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === "live" ? (
          <>
            {/* Risk & INR Telemetry Metrics Bar */}
            <RiskMetrics
              tps={stats.tps}
              totalProcessed={stats.totalProcessed}
              criticalCount={stats.criticalCount}
              avgLatencyMs={stats.avgLatencyMs}
              totalInrMonitoredFormatted={stats.totalInrMonitoredFormatted}
              ethInrRateFormatted={stats.ethInrRateFormatted}
            />

            {/* Live Streaming INR Transaction Feed Table */}
            <LiveTransactions
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
    </div>
  );
}
