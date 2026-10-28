import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Mono} from "next/font/google";
import "./globals.css";
import Header from "../components/Header";

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "uORover Dashboard",
  description: "uOttawa Mars Rover Team mission control dashboard",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${plexSans.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-page text-ink font-sans">
        <Header />
        {children}</body>
    </html>
  );
}
