import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ColorModeScript } from "@chakra-ui/react";
import { Providers } from "./providers";
import AuthGuard from "@/components/AuthGuard";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "ClaimAssist AI - Automated Health Insurance Claim Appeals",
  description:
    "AI-powered platform for automated health insurance claim appeal generation using policy-medical evidence alignment and insurance knowledge graphs.",
  keywords: [
    "health insurance",
    "claim appeal",
    "IRDAI",
    "insurance claim denial",
    "AI",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body style={{ fontFamily: "var(--font-inter), sans-serif" }}>
        <ColorModeScript initialColorMode="light" />
        <Providers>
          <AuthGuard>{children}</AuthGuard>
        </Providers>
      </body>
    </html>
  );
}
