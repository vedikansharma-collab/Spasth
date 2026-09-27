import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../styles/globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Policy Cost Estimator — AI-Powered Treatment Cost Transparency',
  description:
    'Upload your health insurance policy and instantly see exactly what your insurer will pay, what sub-limits apply, and your out-of-pocket expenses — powered by a deterministic calculation engine with full LLM-extracted citations.',
  keywords: ['health insurance', 'treatment cost', 'policy analysis', 'co-pay calculator', 'room rent cap'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
