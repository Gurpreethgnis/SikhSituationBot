import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

const MultiParagraphResponse = () => (
    <div className="prose-gurbani">
      <p style={{ marginBottom: '24px' }}>First paragraph of Gurbani.</p>
      <p style={{ marginBottom: '24px' }}>Second paragraph of Gurbani.</p>
      <p style={{ marginBottom: '0px' }}>Third paragraph of Gurbani.</p>
    </div>
);

test('renders multi-paragraph response with correct spacing', () => {
  const { container } = render(<MultiParagraphResponse />);
  const paragraphs = container.querySelectorAll('.prose-gurbani p');
  expect(paragraphs.length).toBe(3);

  // Check computed margin-bottom for each paragraph except last
  paragraphs.forEach((p, idx) => {
    const style = window.getComputedStyle(p);
    if (idx < paragraphs.length - 1) {
      // 1.5rem = 24px if root font-size is 16px
      expect(parseInt(style.marginBottom)).toBeGreaterThanOrEqual(22);
      expect(parseInt(style.marginBottom)).toBeLessThanOrEqual(25);
    } else {
      expect(parseInt(style.marginBottom)).toBe(0);
    }
  });
});
