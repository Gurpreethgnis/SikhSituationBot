import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Logo from '../app/components/Logo';

describe('Logo Component', () => {
  test('renders logo with correct text', () => {
    render(<Logo />);

    expect(screen.getByText('Sikh')).toBeInTheDocument();
    expect(screen.getByText('Situation')).toBeInTheDocument();
    expect(screen.getByText('Bot')).toBeInTheDocument();
  });

  test('renders logo with correct styling classes', () => {
    const { container } = render(<Logo />);

    // Check main logo container
    const logoContainer = container.firstChild;
    expect(logoContainer).toHaveClass('logo');

    // Check individual word spans
    const sikhSpan = screen.getByText('Sikh');
    const situationSpan = screen.getByText('Situation');
    const botSpan = screen.getByText('Bot');

    expect(sikhSpan).toHaveClass('logo-word');
    expect(situationSpan).toHaveClass('logo-word');
    expect(botSpan).toHaveClass('logo-word');
  });

  test('renders logo with correct structure', () => {
    const { container } = render(<Logo />);

    // Should have a div with class 'logo'
    const logoDiv = container.querySelector('.logo');
    expect(logoDiv).toBeInTheDocument();

    // Should contain three spans with class 'logo-word'
    const wordSpans = container.querySelectorAll('.logo-word');
    expect(wordSpans).toHaveLength(3);

    // Check the text content of each span
    expect(wordSpans[0]).toHaveTextContent('Sikh');
    expect(wordSpans[1]).toHaveTextContent('Situation');
    expect(wordSpans[2]).toHaveTextContent('Bot');
  });

  test('logo is accessible', () => {
    render(<Logo />);

    // Check that the logo text is readable by screen readers
    const logoElement = screen.getByText('Sikh').closest('.logo');
    expect(logoElement).toBeInTheDocument();
  });

  test('logo renders without crashing', () => {
    expect(() => render(<Logo />)).not.toThrow();
  });

  test('logo has consistent rendering', () => {
    const { container: container1 } = render(<Logo />);
    const { container: container2 } = render(<Logo />);

    // Both should have the same structure
    expect(container1.innerHTML).toBe(container2.innerHTML);
  });
});