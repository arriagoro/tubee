import Link from 'next/link';

const features = [
  {
    icon: '🎬',
    title: 'AI Edit Decisions',
    desc: 'Claude AI analyzes your footage and builds the perfect cut',
  },
  {
    icon: '🎵',
    title: 'Beat Sync',
    desc: 'Cuts automatically sync to your music',
  },
  {
    icon: '📱',
    title: 'Reel Ready',
    desc: '1080×1920 vertical format, ready to post',
  },
];

const testimonials = [
  {
    quote: 'Cut my editing time from 4 hours to 15 minutes. Worth every penny.',
    name: 'Marcus T.',
    role: 'Miami Videographer',
  },
  {
    quote: "My clients can't believe how fast I deliver now. Tubee changed my whole workflow.",
    name: 'Jasmine R.',
    role: 'Content Creator',
  },
  {
    quote: 'Finally an AI editor that actually understands what I want. Game changer.',
    name: 'Carlos M.',
    role: 'Wedding Videographer',
  },
];

const pricing = [
  {
    name: 'Starter',
    price: 29,
    features: [
      '10 AI edits per month',
      '1080p HD Export',
      'All 7 style presets',
      'Instagram Reel format (9:16)',
      'Beat-sync to music',
    ],
    cta: 'Get Starter Access',
    href: 'https://www.fanbasis.com/agency-checkout/Dicipline/l7PQ5',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: 79,
    features: [
      'Unlimited AI edits',
      '2K & 4K Ultra Export',
      'All export formats (Reels, Landscape, Square)',
      'AI video generation',
      'DaVinci Resolve XML export',
      'Priority processing',
      'Everything in Starter',
    ],
    cta: 'Get Pro Access',
    href: 'https://www.fanbasis.com/agency-checkout/Dicipline/oyPRj',
    highlighted: true,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-dark/80 backdrop-blur-xl border-b border-[rgba(0,170,255,0.15)]">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight">
            tubee<span className="text-accent">.</span>
          </span>
          <div className="hidden sm:flex items-center gap-8 text-sm text-secondary">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <Link
              href="/editor"
              className="bg-accent text-white font-semibold px-4 py-2 rounded-lg hover:shadow-[0_0_20px_rgba(0,170,255,0.3)] transition-all"
            >
              Start Editing
            </Link>
          </div>
          <Link
            href="/editor"
            className="sm:hidden bg-accent text-white font-semibold px-4 py-2 rounded-lg text-sm"
          >
            Start Editing
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-40 pb-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-1.5 rounded-full border border-[rgba(0,170,255,0.15)] bg-card text-sm text-secondary">
            AI-powered editing • Now in beta
          </div>
          <h1 className="text-5xl sm:text-7xl font-black tracking-tight leading-[1.05] mb-6">
            The AI Video Editor{' '}
            <br className="hidden sm:block" />
            Built for{' '}
            <span className="text-accent">Creators</span>
          </h1>
          <p className="text-lg sm:text-xl text-secondary max-w-2xl mx-auto mb-10">
            Upload footage. Type a prompt. Get a Reel-ready edit in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/editor"
              className="bg-gradient-to-r from-[#00AAFF] to-[#00D4FF] text-white font-bold text-lg px-8 py-4 rounded-2xl hover:shadow-[0_0_40px_rgba(0,170,255,0.3)] hover:scale-[1.02] transition-all"
            >
              Start Editing Free →
            </Link>
            <a
              href="#pricing"
              className="border border-[rgba(0,170,255,0.15)] text-white font-semibold text-lg px-8 py-4 rounded-2xl hover:bg-[rgba(0,170,255,0.05)] transition-all"
            >
              See Pricing ↓
            </a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-4">
            Edit smarter, not harder
          </h2>
          <p className="text-secondary text-center mb-16 max-w-xl mx-auto">
            Three ingredients: your footage, a prompt, and AI that actually understands editing.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl p-8 hover:border-accent/30 hover:shadow-[0_0_20px_rgba(0,170,255,0.1)] transition-all"
              >
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-bold mb-2">{f.title}</h3>
                <p className="text-secondary text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 px-6 border-t border-[rgba(0,170,255,0.15)]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-16">
            Three steps. One reel.
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Upload', desc: 'Drag your raw footage and optional music into the editor.' },
              { step: '02', title: 'Prompt', desc: 'Tell the AI what you want: style, pacing, vibe, length.' },
              { step: '03', title: 'Download', desc: 'Get a polished, beat-synced reel ready for Instagram.' },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="text-accent font-mono text-sm font-bold mb-3">{s.step}</div>
                <h3 className="text-xl font-bold mb-2">{s.title}</h3>
                <p className="text-secondary text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof / Testimonials */}
      <section className="py-24 px-6 border-t border-[rgba(0,170,255,0.15)]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-4">
            Join videographers already using{' '}
            <span className="text-accent">Tubee</span>
          </h2>
          <p className="text-secondary text-center mb-16 max-w-xl mx-auto">
            Creators are saving hours every week with AI-powered editing.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t) => (
              <div
                key={t.name}
                className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl p-8 hover:border-accent/30 hover:shadow-[0_0_20px_rgba(0,170,255,0.1)] transition-all relative"
              >
                <div className="text-accent text-4xl font-serif leading-none mb-4">&ldquo;</div>
                <p className="text-white/90 text-sm leading-relaxed mb-6">
                  {t.quote}
                </p>
                <div className="mt-auto">
                  <p className="font-semibold text-sm">{t.name}</p>
                  <p className="text-secondary text-xs">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 px-6 border-t border-[rgba(0,170,255,0.15)]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-4">
            Simple pricing
          </h2>
          <p className="text-secondary text-center mb-16 max-w-xl mx-auto">
            Pick the plan that fits your workflow. Cancel anytime.
          </p>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {pricing.map((p) => (
              <div
                key={p.name}
                className={`rounded-2xl p-8 border transition-all ${
                  p.highlighted
                    ? 'bg-[rgba(0,170,255,0.05)] border-accent/30 ring-1 ring-accent/20 scale-[1.02] shadow-[0_0_60px_rgba(0,170,255,0.08)]'
                    : 'bg-card border-[rgba(0,170,255,0.15)] hover:border-accent/30'
                }`}
              >
                {p.highlighted && (
                  <div className="inline-block bg-accent text-white text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full mb-4">
                    Most Popular
                  </div>
                )}
                <h3 className="text-xl font-bold mb-1">{p.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-black">${p.price}</span>
                  <span className="text-secondary text-sm">/month</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-secondary">
                      <span className="text-accent mt-0.5">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <a
                  href={p.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block text-center font-semibold py-3 rounded-xl transition-all ${
                    p.highlighted
                      ? 'bg-accent text-white hover:shadow-[0_0_20px_rgba(0,170,255,0.3)]'
                      : 'border border-[rgba(0,170,255,0.15)] text-white hover:bg-[rgba(0,170,255,0.05)]'
                  }`}
                >
                  {p.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Built for itsthatseason */}
      <section className="py-16 px-6 border-t border-[rgba(0,170,255,0.15)]">
        <div className="max-w-5xl mx-auto text-center">
          <p className="text-secondary text-sm">
            Part of the{' '}
            <a
              href="https://itsthatseason.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              itsthatseason.com
            </a>{' '}
            ecosystem — built by Film Tuck Tubee
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-[rgba(0,170,255,0.15)]">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-xl font-bold tracking-tight">
            tubee<span className="text-accent">.</span>
          </span>
          <p className="text-secondary text-sm">
            © 2026 Tubee. Built by Film Tuck Tubee.
          </p>
        </div>
      </footer>
    </main>
  );
}
