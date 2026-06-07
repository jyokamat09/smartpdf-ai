import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartPDF AI — Document Intelligence",
  description: "AI-powered document analysis and chat",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
