import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EVM Real-Time Risk Intelligence Platform",
  description: "Sub-second streaming Ethereum risk analysis powered by XGBoost, TreeSHAP, and Redis sliding windows.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
