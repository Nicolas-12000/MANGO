import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Fraunces, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";

import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["600"],
  variable: "--font-fraunces",
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Mango",
  description: "Segmentación de clientes del centro comercial con K-Means.",
};

export const viewport: Viewport = {
  themeColor: "#fff4ea",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" className={`${fraunces.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body className="min-h-dvh">{children}</body>
    </html>
  );
}
