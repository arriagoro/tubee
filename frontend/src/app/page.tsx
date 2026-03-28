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

const pricing = [
  {
    name: 'Starter',
    price: 29,
    features: ['10 edits per month', '1080p export', 'All style presets', 'Email support'],
    cta: 'Get Started',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: 79,
    features: ['50 edits per month', '4K export', 'Style presets', 'DaVinci XML export', 'Priority support'],
    cta: 'Go Pro',
    highlighted: true,
  },
  {
    name: 'Agency',
    price: 199,
    features: ['Unlimited edits', '4K export', 'White label', 'Team seats', 'API access', 'Dedicated support'],
    cta: 'Contact Us',
    highlighted: false,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-dark/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight">
            tubee<span className="text-accent">.</span>
          </span>
          <div className="hidden sm:flex items-center gap-8 text-sm text-secondary">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <Link
              href="/editor"
              className="bg-accent text-dark font-semibold px-4 py-2 rounded-lg hover:brightness-110 transition-all"
            >
              Start Editing
            </Link>
          </div>
          <Link
            href="/editor"
            className="sm:hidden bg-accent text-dark font-semibold px-4 py-2 rounded-lg text-sm"
          >
            Start Editing
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-40 pb-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block mb-6 px-4 py-1.5 rounded-full border border-white/10 bg-card text-sm text-secondary">
            AI-powered editing • Now in beta
          </div>
          <h1 className="text-5xl sm:text-7xl font-black tracking-tight leading-[1.05] mb-6">
            Drop Footage.{' '}
            <br className="hidden sm:block" />
            Type a Prompt.{' '}
            <br className="hidden sm:block" />
            <span className="text-accent">Get a Reel.</span>
          </h1>
          <p className="text-lg sm:text-xl text-secondary max-w-2xl mx-auto mb-10">
            AI-powered video editing for creators and videographers.
            Upload your clips, describe what you want, and let Tubee handle the rest.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/editor"
              className="bg-accent text-dark font-bold text-lg px-8 py-4 rounded-2xl hover:brightness-110 hover:scale-[1.02] transition-all shadow-[0_0_40px_rgba(200,241,53,0.15)]"
            >
              Start Editing Free →
            </Link>
            <a
              href="#features"
              className="border border-white/10 text-white font-semibold text-lg px-8 py-4 rounded-2xl hover:bg-white/5 transition-all"
            >
              See How It Works
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
                className="bg-card border border-white/5 rounded-2xl p-8 hover:border-accent/20 transition-colors"
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
      <section className="py-24 px-6 border-t border-white/5">
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

      {/* Pricing */}
      <section id="pricing" className="py-24 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-4">
            Simple pricing
          </h2>
          <p className="text-secondary text-center mb-16 max-w-xl mx-auto">
            Start free during beta. Pick a plan when you&#39;re hooked.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {pricing.map((p) => (
              <div
                key={p.name}
                className={`rounded-2xl p-8 border transition-colors ${
                  p.highlighted
                    ? 'bg-accent/5 border-accent/30 ring-1 ring-accent/20'
                    : 'bg-card border-white/5 hover:border-white/10'
                }`}
              >
                {p.highlighted && (
                  <div className="text-accent text-xs font-bold uppercase tracking-wider mb-4">
                    Most Popular
                  </div>
                )}
                <h3 className="text-xl font-bold mb-1">{p.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-black">${p.price}</span>
                  <span className="text-secondary text-sm">/mo</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-secondary">
                      <span className="text-accent">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/editor"
                  className={`block text-center font-semibold py-3 rounded-xl transition-all ${
                    p.highlighted
                      ? 'bg-accent text-dark hover:brightness-110'
                      : 'border border-white/10 text-white hover:bg-white/5'
                  }`}
                >
                  {p.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
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
