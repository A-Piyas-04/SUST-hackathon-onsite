import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Liquidity & Coordination Platform — Demo",
  description: "Decision-support demo UI for multi-provider agent liquidity and coordination.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
