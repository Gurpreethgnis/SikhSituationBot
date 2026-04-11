import React from 'react';
import '../privacy/privacy.css'; // Reusing privacy styles for consistency

export const metadata = {
  title: 'Support | Giani Ji',
  description: 'Support and contact information for Giani Ji.',
};

export default function SupportPage() {
  return (
    <div className="policy-container">
      <div className="policy-content">
        <h1>Giani Ji Support</h1>
        
        <section>
          <h2>How can we help?</h2>
          <p>
            If you are experiencing issues with the Giani Ji app, have questions about your account, or want to provide feedback, please reach out to us.
          </p>
        </section>

        <section>
          <h2>Contact Information</h2>
          <p>
            Email us directly at: <a href="mailto:support@gianiji.com">support@gianiji.com</a>
          </p>
        </section>

        <section>
          <h2>Frequently Asked Questions</h2>
          <ul>
            <li><strong>How do I change my persona tone?</strong> You can update your birth year in the Settings tab of the mobile app to adjust the tone (Child, Teen, Adult).</li>
            <li><strong>How do I delete my data?</strong> You can clear all AI memories or delete your account entirely from the Settings tab in the mobile app.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
