import type { Metadata } from "next";

import {
  Bebas_Neue,
  Geist,
} from "next/font/google";

import "./globals.css";


const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});


const bebas = Bebas_Neue({
  variable: "--font-bebas",
  subsets: ["latin"],
  weight: "400",
});


export const metadata: Metadata = {
  title: "SHARP.PY",
  description:
    "Merchant return risk management",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (
    <html lang="en">

      <body
        className={`${geist.variable} ${bebas.variable}`}
      >
        {children}
      </body>

    </html>
  );
}