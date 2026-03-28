import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tubee — AI-Powered Video Editing',
  description: 'Drop footage. Type a prompt. Get a reel. AI-powered video editing for creators and videographers.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
