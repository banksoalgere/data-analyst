import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DataChat AI - Chat with Your Excel Files & Get Instant Insights",
  description: "Upload your Excel files and ask questions in plain English. Our AI analyzes your data and delivers actionable insights in seconds—no coding required. Transform complex data into clear answers.",
  keywords: ["Excel AI", "data analysis", "spreadsheet chat", "AI assistant", "data insights", "business intelligence"],
  authors: [{ name: "DataChat AI" }],
  openGraph: {
    title: "DataChat AI - Chat with Your Excel Files",
    description: "Get instant insights from your Excel files using AI. No coding required.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "DataChat AI - Chat with Your Excel Files",
    description: "Get instant insights from your Excel files using AI. No coding required.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
      </body>
    </html>
  );
}
