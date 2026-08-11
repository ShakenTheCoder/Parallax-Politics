import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/lib/SessionContext";
import { ThemeProvider } from "@/lib/ThemeContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Parallax Politics",
  description: "Professional political analysis and advisory services with clarity and certainty",
  icons: {
    icon: [
      { url: "/Parallax-assets/Parallax politics/3.png", type: "image/png" },
      { url: "/favicon.ico", type: "image/x-icon" },
    ],
    shortcut: "/Parallax-assets/Parallax politics/3.png",
    apple: "/Parallax-assets/Parallax politics/3.png",
  },
  manifest: "/site.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <SessionProvider>
            <Navbar />
            {children}
            <Footer />
          </SessionProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
