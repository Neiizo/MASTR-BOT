import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import TopMenu from "./components/TopMenu";
import { DataProvider } from "./context/DataContext";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "MASTR-Bot",
  description: "Control page for the MASTR-Bot simulation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="winter">
      <body>
        <DataProvider>
          <TopMenu />
          <div className="mx-[10%] md:mx-[15%] lg:mx-[15%] mt-8" id="parent-div">{children}</div>
        </DataProvider></body>
    </html>
  );
}
