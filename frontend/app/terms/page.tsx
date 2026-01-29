import Link from "next/link";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            DataChat AI
          </Link>
          <Link
            href="/dashboard"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Content */}
      <div className="container mx-auto px-6 py-12 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Terms and Conditions</h1>
        <p className="text-gray-600 mb-8">Last updated: January 28, 2024</p>

        <div className="bg-white rounded-lg shadow-sm p-8 space-y-8">
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Agreement to Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              By accessing or using DataChat AI ("the Service"), you agree to be bound by these Terms and Conditions
              ("Terms"). If you disagree with any part of these terms, you may not access the Service. These Terms
              apply to all visitors, users, and others who access or use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Description of Service</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              DataChat AI provides an AI-powered platform that allows users to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>Upload Excel files for data analysis</li>
              <li>Ask questions about their data using natural language</li>
              <li>Receive AI-generated insights and analysis</li>
              <li>Interact with data through conversational interfaces</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4">
              The Service is provided "as is" and we reserve the right to modify or discontinue the Service
              at any time with or without notice.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts and Registration</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              When you create an account with us, you must provide accurate, complete, and current information.
              Failure to do so constitutes a breach of the Terms.
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>You are responsible for safeguarding your account credentials</li>
              <li>You must immediately notify us of any unauthorized use of your account</li>
              <li>You must be at least 13 years old to use this Service</li>
              <li>One person or legal entity may not maintain more than one account</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Acceptable Use Policy</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              You agree not to use the Service to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>Violate any applicable laws or regulations</li>
              <li>Upload malicious files, viruses, or harmful code</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Interfere with or disrupt the Service or servers</li>
              <li>Use the Service for any illegal or unauthorized purpose</li>
              <li>Upload files containing personally identifiable information of others without consent</li>
              <li>Reverse engineer, decompile, or attempt to extract source code</li>
              <li>Use automated systems to access the Service without permission</li>
              <li>Impersonate any person or entity or misrepresent your affiliation</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. User Content and Data</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              By uploading files or submitting content to the Service:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>You retain all ownership rights to your data and content</li>
              <li>You grant us a limited license to process your data to provide the Service</li>
              <li>You represent that you have the right to upload and process the data</li>
              <li>You are responsible for ensuring your data does not violate any laws or third-party rights</li>
              <li>We may delete uploaded files after processing or when your session ends</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Intellectual Property Rights</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              The Service and its original content, features, and functionality are owned by DataChat AI and are
              protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>Our trademarks may not be used without prior written consent</li>
              <li>You may not copy, modify, or create derivative works of our Service</li>
              <li>AI-generated responses are provided for your use, but our underlying models remain our property</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. AI-Generated Content Disclaimer</h2>
            <p className="text-gray-700 leading-relaxed">
              The insights and analysis provided by our AI are generated automatically and should be used as guidance only.
              We do not guarantee the accuracy, completeness, or reliability of AI-generated content. You are responsible
              for verifying any information before making business decisions based on our Service. We are not liable for
              any decisions made based on AI-generated insights.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Privacy and Data Security</h2>
            <p className="text-gray-700 leading-relaxed">
              Your use of the Service is also governed by our Privacy Policy. By using the Service, you consent to
              the collection and use of information as described in our Privacy Policy. We implement security measures
              to protect your data, but no system is completely secure. You use the Service at your own risk.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Limitation of Liability</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              To the maximum extent permitted by law, DataChat AI shall not be liable for:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>Any indirect, incidental, special, consequential, or punitive damages</li>
              <li>Loss of profits, revenue, data, or business opportunities</li>
              <li>Inaccurate AI-generated analysis or insights</li>
              <li>Service interruptions or data loss</li>
              <li>Unauthorized access to your data</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4">
              Our total liability shall not exceed the amount you paid us in the 12 months preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Disclaimer of Warranties</h2>
            <p className="text-gray-700 leading-relaxed">
              THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
              INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
              NON-INFRINGEMENT. We do not warrant that the Service will be uninterrupted, secure, or error-free.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Indemnification</h2>
            <p className="text-gray-700 leading-relaxed">
              You agree to defend, indemnify, and hold harmless DataChat AI and its officers, directors, employees,
              and agents from any claims, liabilities, damages, losses, and expenses arising from your use of the
              Service, violation of these Terms, or infringement of any third-party rights.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Termination</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              We may terminate or suspend your account and access to the Service immediately, without prior notice,
              for any reason, including but not limited to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>Breach of these Terms</li>
              <li>Fraudulent or illegal activity</li>
              <li>Extended period of inactivity</li>
              <li>At our sole discretion</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4">
              Upon termination, your right to use the Service will immediately cease. We may delete your data
              upon termination.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Governing Law and Jurisdiction</h2>
            <p className="text-gray-700 leading-relaxed">
              These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which
              DataChat AI operates, without regard to its conflict of law provisions. Any disputes arising from these
              Terms or the Service shall be resolved in the courts of that jurisdiction.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">14. Changes to Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              We reserve the right to modify or replace these Terms at any time at our sole discretion. We will provide
              notice of any material changes by posting the new Terms on this page and updating the "Last updated" date.
              Your continued use of the Service after changes become effective constitutes acceptance of the revised Terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">15. Severability</h2>
            <p className="text-gray-700 leading-relaxed">
              If any provision of these Terms is found to be invalid or unenforceable, the remaining provisions shall
              continue in full force and effect. The invalid provision shall be replaced with a valid provision that
              most closely matches the intent of the original provision.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">16. Entire Agreement</h2>
            <p className="text-gray-700 leading-relaxed">
              These Terms, together with our Privacy Policy, constitute the entire agreement between you and DataChat AI
              regarding the use of the Service and supersede all prior agreements and understandings.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">17. Contact Information</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              If you have any questions about these Terms, please contact us:
            </p>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-700">Email: legal@datachatai.com</p>
              <p className="text-gray-700">Website: www.datachatai.com</p>
            </div>
          </section>

          <section className="border-t pt-6">
            <p className="text-sm text-gray-600 italic">
              By using DataChat AI, you acknowledge that you have read, understood, and agree to be bound by these
              Terms and Conditions.
            </p>
          </section>
        </div>

        {/* Back to home */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-blue-600 hover:text-blue-700 font-medium">
            ← Back to Home
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12 mt-20">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <div className="text-2xl font-bold text-white mb-2">DataChat AI</div>
              <p className="text-sm">© 2024 DataChat AI. All rights reserved.</p>
            </div>
            <div className="flex gap-6">
              <Link href="/privacy" className="hover:text-white transition">
                Privacy Policy
              </Link>
              <Link href="/terms" className="hover:text-white transition">
                Terms of Service
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
