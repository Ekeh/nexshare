import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { MotionProviders } from "@/components/motion/Providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "NexShare — Promote Anything. Earn From Results.",
  description:
    "NexShare is a universal performance-commerce network. Businesses publish offers, promoters distribute them, customers convert, promoters earn commission.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <MotionProviders>{children}</MotionProviders>
      </body>
    </html>
  );
}
