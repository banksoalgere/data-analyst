import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary selection:text-primary-foreground">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="container mx-auto px-6 h-16 flex justify-between items-center">
          <div className="text-lg font-bold tracking-tighter">
            DATACHAT_AI
          </div>
          <div className="flex gap-8 text-sm font-medium tracking-wide">
            <Link href="/privacy" className="text-muted-foreground hover:text-foreground transition-colors uppercase text-[10px] tracking-widest">
              Privacy
            </Link>
            <Link href="/terms" className="text-muted-foreground hover:text-foreground transition-colors uppercase text-[10px] tracking-widest">
              Terms
            </Link>
            <Link
              href="/dashboard"
              className="text-foreground hover:text-muted-foreground transition-colors uppercase text-[10px] tracking-widest"
            >
              [ Get Started ]
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 pt-32 pb-40 border-b border-border">
        <div className="max-w-5xl">
          <h1 className="text-6xl md:text-9xl font-semibold tracking-tighter mb-12 leading-[0.9]">
            Instant data <br />
            intelligence.
          </h1>
          <div className="flex flex-col md:flex-row gap-12 items-start md:items-end justify-between border-t border-border pt-8">
            <p className="text-xl md:text-2xl text-muted-foreground max-w-xl leading-relaxed font-light">
              Upload Excel files. Ask questions in plain English.
              <span className="text-foreground block mt-2">No coding required.</span>
            </p>

            <div className="flex gap-4">
              <Link
                href="/dashboard"
                className="group flex items-center gap-4 text-lg font-medium border border-border px-8 py-4 hover:bg-foreground hover:text-background transition-colors duration-300"
              >
                <span>Start Analyzing</span>
                <span className="block w-2 h-2 bg-foreground group-hover:bg-background transition-colors rounded-full"></span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="border-b border-border">
        <div className="grid md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-border">
          {/* Feature 01 */}
          <div className="p-12 hover:bg-muted/10 transition-colors">
            <span className="font-mono text-xs text-muted-foreground mb-8 block">01 / SPEED</span>
            <h3 className="text-2xl font-medium mb-4 tracking-tight">Lightning Fast</h3>
            <p className="text-muted-foreground leading-relaxed">
              Processing architecture designed for immediate insights. Zero latency data parsing.
            </p>
          </div>

          {/* Feature 02 */}
          <div className="p-12 hover:bg-muted/10 transition-colors">
            <span className="font-mono text-xs text-muted-foreground mb-8 block">02 / ACCESS</span>
            <h3 className="text-2xl font-medium mb-4 tracking-tight">No Code Required</h3>
            <p className="text-muted-foreground leading-relaxed">
              Natural language processing interface. Eliminate the need for SQL or complex formulas.
            </p>
          </div>

          {/* Feature 03 */}
          <div className="p-12 hover:bg-muted/10 transition-colors">
            <span className="font-mono text-xs text-muted-foreground mb-8 block">03 / SECURITY</span>
            <h3 className="text-2xl font-medium mb-4 tracking-tight">Private & Secure</h3>
            <p className="text-muted-foreground leading-relaxed">
              Enterprise-grade encryption. Data isolation protocols. We never store sensitive keys.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works - List View */}
      <section className="container mx-auto px-6 py-32 border-b border-border">
        <div className="grid md:grid-cols-12 gap-12">
          <div className="md:col-span-4">
            <h2 className="text-4xl font-semibold tracking-tighter mb-4">Methodology</h2>
            <p className="text-muted-foreground">Three steps to intelligence.</p>
          </div>

          <div className="md:col-span-8 space-y-12">
            <div className="border-t border-border pt-8 group">
              <div className="flex items-baseline justify-between mb-2">
                <h3 className="text-2xl font-medium">Upload</h3>
                <span className="font-mono text-sm text-muted-foreground">STEP 01</span>
              </div>
              <p className="text-muted-foreground text-lg max-w-md">Drag and drop your Excel file. System auto-detects schema and data types.</p>
            </div>

            <div className="border-t border-border pt-8 group">
              <div className="flex items-baseline justify-between mb-2">
                <h3 className="text-2xl font-medium">Query</h3>
                <span className="font-mono text-sm text-muted-foreground">STEP 02</span>
              </div>
              <p className="text-muted-foreground text-lg max-w-md">Interact with your data using natural language. Like talking to a senior analyst.</p>
            </div>

            <div className="border-t border-border pt-8 group">
              <div className="flex items-baseline justify-between mb-2">
                <h3 className="text-2xl font-medium">Insight</h3>
                <span className="font-mono text-sm text-muted-foreground">STEP 03</span>
              </div>
              <p className="text-muted-foreground text-lg max-w-md">Receive generated charts, trends, and actionable summaries instantly.</p>
            </div>

            <div className="border-t border-border"></div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-40 text-center border-b border-border bg-foreground text-background">
        <div className="container mx-auto px-6">
          <h2 className="text-5xl md:text-7xl font-bold tracking-tighter mb-8">
            Start analysing.
          </h2>
          <Link
            href="/dashboard"
            className="inline-block border-2 border-background px-12 py-5 text-lg font-bold tracking-widest uppercase hover:bg-background hover:text-foreground transition-colors duration-300"
          >
            Get STarted
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-end gap-6">
          <div>
            <div className="font-bold tracking-tighter text-xl mb-4">DATACHAT_AI</div>
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest">
              © 2026 DataChat AI.<br />All rights reserved.
            </p>
          </div>
          <div className="flex gap-8">
            <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}