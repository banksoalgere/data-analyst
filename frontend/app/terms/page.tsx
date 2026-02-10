import Link from "next/link";

export default function TermsPage() {
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
        <h1 className="text-4xl md:text-6xl font-bold tracking-tighter mb-4">Terms and Conditions</h1>
        <p className="text-muted-foreground font-mono text-xs uppercase tracking-widest mb-12">
          Last updated: January 28, 2024
        </p>

        <div className="space-y-12">
          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">01. Agreement to Terms</h2>
            <p className="text-muted-foreground leading-relaxed text-lg">
              By accessing or using DataChat AI (&quot;the Service&quot;), you agree to be bound by these Terms and Conditions
              (&quot;Terms&quot;). If you disagree with any part of these terms, you may not access the Service. These Terms
              apply to all visitors, users, and others who access or use the Service.
            </p>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">02. Description of Service</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              DataChat AI provides an AI-powered platform that allows users to:
            </p>
            <ul className="space-y-2 text-muted-foreground ml-4 list-none">
              <li>— Upload Excel files for data analysis</li>
              <li>— Ask questions about their data using natural language</li>
              <li>— Receive AI-generated insights and analysis</li>
              <li>— Interact with data through conversational interfaces</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-4">
              The Service is provided &quot;as is&quot; and we reserve the right to modify or discontinue the Service
              at any time with or without notice.
            </p>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">03. User Accounts</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              When you create an account with us, you must provide accurate, complete, and current information.
              Failure to do so constitutes a breach of the Terms.
            </p>
            <ul className="space-y-2 text-muted-foreground ml-4 list-none">
              <li>— You are responsible for safeguarding your account credentials</li>
              <li>— You must immediately notify us of any unauthorized use of your account</li>
              <li>— You must be at least 13 years old to use this Service</li>
            </ul>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">04. Acceptable Use</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              You agree not to use the Service to:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              <div className="border border-border p-4 text-sm text-muted-foreground">Violate any applicable laws or regulations</div>
              <div className="border border-border p-4 text-sm text-muted-foreground">Upload malicious files, viruses, or harmful code</div>
              <div className="border border-border p-4 text-sm text-muted-foreground">Attempt to gain unauthorized access to our systems</div>
              <div className="border border-border p-4 text-sm text-muted-foreground">Interfere with or disrupt the Service or servers</div>
            </div>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">05. Intellectual Property</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              The Service and its original content, features, and functionality are owned by DataChat AI and are
              protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
            </p>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">06. Disclaimer of Warranties</h2>
            <p className="text-muted-foreground leading-relaxed border-l-2 border-primary pl-6 py-2 bg-card/50">
              THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
              INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
              NON-INFRINGEMENT.
            </p>
          </section>

          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-bold mb-4 tracking-tight">07. Contact Information</h2>
            <div className="bg-card border border-border p-8">
              <p className="text-foreground font-mono text-sm mb-2">EMAIL_CONTACT:</p>
              <p className="text-muted-foreground mb-6">legal@datachatai.com</p>
              <p className="text-foreground font-mono text-sm mb-2">WEB:</p>
              <p className="text-muted-foreground">www.datachatai.com</p>
            </div>
          </section>

          <section className="mt-12 pt-6 border-t border-border">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest text-center">
              By using DataChat AI, you agree to be bound by these terms.
            </p>
          </section>
        </div>

        {/* Back to home */}
        <div className="mt-12 pt-8 text-center">
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
            <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-sm text-foreground hover:text-muted-foreground transition-colors">
              Terms of Service
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
