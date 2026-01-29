import Link from "next/link";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary selection:text-primary-foreground">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="container mx-auto px-6 h-16 flex justify-between items-center">
          <Link href="/" className="text-lg font-bold tracking-tighter">
            DATACHAT_AI
          </Link>
          <Link
            href="/dashboard"
            className="text-foreground hover:text-muted-foreground transition-colors uppercase text-[10px] tracking-widest font-medium"
          >
            [ Get Started ]
          </Link>
        </div>
      </nav>

      {/* Content */}
      <div className="container mx-auto px-6 py-20 max-w-4xl">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tighter mb-4">Privacy Policy</h1>
        <p className="text-muted-foreground font-mono text-xs uppercase tracking-widest mb-12">
          Last updated: January 28, 2024
        </p>

        <div className="space-y-12">
          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">01. Introduction</h2>
            <p className="text-muted-foreground leading-relaxed text-lg">
              Welcome to DataChat AI. We respect your privacy and are committed to protecting your personal data.
              This privacy policy will inform you about how we handle your personal data when you visit our website
              and use our services, and tell you about your privacy rights.
            </p>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">02. Data We Collect</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We collect and process the following types of data:
            </p>
            <ul className="space-y-2 text-muted-foreground ml-4 list-none">
              <li><span className="text-foreground font-medium">Usage Data:</span> Information about how you use our website and services</li>
              <li><span className="text-foreground font-medium">File Data:</span> Excel files you upload for analysis (processed temporarily)</li>
              <li><span className="text-foreground font-medium">Conversation Data:</span> Your chat interactions with our AI assistant</li>
              <li><span className="text-foreground font-medium">Technical Data:</span> IP address, browser type, device information, and access times</li>
              <li><span className="text-foreground font-medium">Cookie Data:</span> Information collected through cookies and similar technologies</li>
            </ul>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">03. How We Use Your Data</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We use your data for the following purposes:
            </p>
            <ul className="space-y-2 text-muted-foreground ml-4 list-none">
              <li>— To provide and maintain our AI-powered data analysis service</li>
              <li>— To process and analyze your uploaded Excel files</li>
              <li>— To improve our service quality and user experience</li>
              <li>— To communicate with you about service updates</li>
              <li>— To ensure the security and integrity of our platform</li>
              <li>— To comply with legal obligations</li>
            </ul>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">04. Data Storage and Security</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We take data security seriously and implement appropriate measures:
            </p>
            <ul className="space-y-2 text-muted-foreground ml-4 list-none">
              <li>— Your uploaded files are processed in memory and not permanently stored on our servers</li>
              <li>— Conversation contexts are stored temporarily for session continuity</li>
              <li>— We use industry-standard encryption for data transmission (HTTPS/SSL)</li>
              <li>— Access to data is restricted to authorized personnel only</li>
              <li>— We regularly review and update our security practices</li>
            </ul>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">05. Data Sharing and Third Parties</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We do not sell your personal data. We may share data with:
            </p>
            <ul className="space-y-2 text-muted-foreground ml-4 list-none">
              <li><span className="text-foreground font-medium">AI Service Providers:</span> We use third-party AI services to process your queries</li>
              <li><span className="text-foreground font-medium">Cloud Hosting Providers:</span> For infrastructure and service delivery</li>
              <li><span className="text-foreground font-medium">Analytics Providers:</span> To understand service usage and improve performance</li>
              <li><span className="text-foreground font-medium">Legal Authorities:</span> When required by law or to protect our rights</li>
            </ul>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">06. Your Privacy Rights</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              You have the following rights regarding your personal data:
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-card border border-border p-4">
                <span className="block text-foreground font-bold text-sm uppercase tracking-wider mb-2">Access</span>
                <span className="text-muted-foreground text-sm">Request access to your personal data</span>
              </div>
              <div className="bg-card border border-border p-4">
                <span className="block text-foreground font-bold text-sm uppercase tracking-wider mb-2">Correction</span>
                <span className="text-muted-foreground text-sm">Request correction of inaccurate data</span>
              </div>
              <div className="bg-card border border-border p-4">
                <span className="block text-foreground font-bold text-sm uppercase tracking-wider mb-2">Deletion</span>
                <span className="text-muted-foreground text-sm">Request deletion of your personal data</span>
              </div>
              <div className="bg-card border border-border p-4">
                <span className="block text-foreground font-bold text-sm uppercase tracking-wider mb-2">Objection</span>
                <span className="text-muted-foreground text-sm">Object to processing of your data</span>
              </div>
            </div>
          </section>
        </div>

        {/* Back to home */}
        <div className="mt-20 pt-8 border-t border-border">
          <Link href="/" className="inline-block text-foreground hover:text-muted-foreground transition-colors uppercase text-xs tracking-widest font-bold">
            ← Back to Home
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-12 border-t border-border mt-20">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-end gap-6">
          <div>
            <div className="font-bold tracking-tighter text-xl mb-4">DATACHAT_AI</div>
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest">
              © 2024 DataChat AI.<br />All rights reserved.
            </p>
          </div>
          <div className="flex gap-8">
            <Link href="/privacy" className="text-sm text-foreground hover:text-muted-foreground transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Terms of Service
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
