import React from 'react';
import './privacy.css';

export const metadata = {
  title: 'Privacy Policy | Giani Ji',
  description: 'Privacy Policy for Giani Ji app.',
};

export default function PrivacyPage() {
  return (
    <div className="policy-container">
      <div className="policy-content">
        <h1>Privacy Policy</h1>
        <p className="last-updated">Last Updated: April 10, 2026</p>

        <section>
          <h2>Introduction</h2>
          <p>
            Giani Ji is committed to your spiritual journey and your privacy.
            This Privacy Policy explains how we collect, use, and protect your information
            when you use our mobile application and website.
          </p>
        </section>

        <section>
          <h2>Information We Collect</h2>
          <ul>
            <li><strong>Account Information:</strong> We collect your name and email address when you sign in (typically via Google) to synchronize your account across devices.</li>
            <li><strong>Profile Data:</strong> We may collect your birth year to help the AI persona customize the tone of its spiritual guidance (e.g., Child, Teen, Adult).</li>
            <li><strong>Chat History & Memories:</strong> We securely store your conversations with Giani Ji. This allows the AI to "remember" past insights and provide a continuous, contextual spiritual journey.</li>
          </ul>
        </section>

        <section>
          <h2>How We Use Your Information</h2>
          <p>We use your information solely for <strong>App Functionality</strong> and <strong>Product Personalization</strong>. Specifically:</p>
          <ul>
            <li>To provide and maintain the core AI guidance features.</li>
            <li>To personalize your spiritual reflections.</li>
          </ul>
          <p>
            <strong>We do not sell your data.</strong> We do not use your data for third-party tracking or advertising networks.
          </p>
        </section>

        <section>
          <h2>Data Security</h2>
          <p>
            All conversations with Giani Ji are processed securely. We employ standard security measures to protect your personal information from unauthorized access or disclosure.
          </p>
        </section>

        <section>
          <h2>Your Rights</h2>
          <p>
            You can modify your profile settings (such as your birth year) directly in the app.
            You can also clear your AI "memories" or delete your account at any time through the in-app settings menu.
          </p>
        </section>

        <section>
          <h2>Contact Us</h2>
          <p>
            If you have any questions or concerns about this Privacy Policy, please contact us at <a href="/support">Support</a>.
          </p>
        </section>
      </div>
    </div>
  );
}
