import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Perspectives from '../app/components/Perspectives';

// Mock fetch globally
global.fetch = jest.fn();

describe('Perspectives Component', () => {
  const mockOnResponse = jest.fn();
  const mockOnLoading = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
  });

  test('renders perspectives component', () => {
    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    expect(screen.getByText('Choose Your Perspective')).toBeInTheDocument();
    expect(screen.getByText('How would you like to explore Sikh wisdom?')).toBeInTheDocument();
  });

  test('displays all persona cards', () => {
    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    // Check for persona titles
    expect(screen.getByText('Adult')).toBeInTheDocument();
    expect(screen.getByText('Teen')).toBeInTheDocument();
    expect(screen.getByText('Child')).toBeInTheDocument();

    // Check for descriptions
    expect(screen.getByText(/mature reflection/i)).toBeInTheDocument();
    expect(screen.getByText(/youthful exploration/i)).toBeInTheDocument();
    expect(screen.getByText(/simple wonder/i)).toBeInTheDocument();
  });

  test('shows persona selection buttons', () => {
    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    expect(screen.getByRole('button', { name: /select adult perspective/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /select teen perspective/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /select child perspective/i })).toBeInTheDocument();
  });

  test('handles persona selection', async () => {
    const mockApiResponse = {
      query: 'Tell me about Sikhism',
      persona: 'adult',
      response: 'Sikhism is a monotheistic religion...',
      shabads: [],
      timestamp: new Date().toISOString()
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponse)
    });

    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    // Should show input field for the selected persona
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a question as an adult/i)).toBeInTheDocument();
    });

    // Fill in the question
    const input = screen.getByPlaceholderText(/Ask a question as an adult/i);
    const submitButton = screen.getByRole('button', { name: /ask as adult/i });

    fireEvent.change(input, { target: { value: 'Tell me about Sikhism' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnResponse).toHaveBeenCalledWith(mockApiResponse);
    });
  });

  test('shows different input placeholders for each persona', async () => {
    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    // Test adult persona
    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a question as an adult/i)).toBeInTheDocument();
    });

    // Go back and test teen persona
    const backButton = screen.getByRole('button', { name: /back/i });
    fireEvent.click(backButton);

    const teenButton = screen.getByRole('button', { name: /select teen perspective/i });
    fireEvent.click(teenButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a question as a teen/i)).toBeInTheDocument();
    });

    // Go back and test child persona
    fireEvent.click(backButton);

    const childButton = screen.getByRole('button', { name: /select child perspective/i });
    fireEvent.click(childButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a question as a child/i)).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Server error' })
    });

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Ask a question as an adult/i);
      const submitButton = screen.getByRole('button', { name: /ask as adult/i });

      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  test('shows loading state during API calls', async () => {
    global.fetch.mockImplementationOnce(() =>
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve({
          response: 'Test response',
          shabads: [],
          timestamp: new Date().toISOString()
        })
      }), 100))
    );

    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Ask a question as an adult/i);
      const submitButton = screen.getByRole('button', { name: /ask as adult/i });

      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(true);
    });

    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(false);
    });
  });

  test('prevents empty question submission', async () => {
    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /ask as adult/i });
      fireEvent.click(submitButton);
    });

    // Should not trigger API call or callbacks
    expect(global.fetch).not.toHaveBeenCalled();
    expect(mockOnResponse).not.toHaveBeenCalled();
    expect(mockOnLoading).not.toHaveBeenCalled();
  });

  test('maintains persona context throughout interaction', async () => {
    const mockApiResponse = {
      query: 'Test question',
      persona: 'teen',
      response: 'Test response',
      shabads: [],
      timestamp: new Date().toISOString()
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponse)
    });

    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    // Select teen persona
    const teenButton = screen.getByRole('button', { name: /select teen perspective/i });
    fireEvent.click(teenButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Ask a question as a teen/i);
      const submitButton = screen.getByRole('button', { name: /ask as teen/i });

      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockOnResponse).toHaveBeenCalledWith(
        expect.objectContaining({ persona: 'teen' })
      );
    });
  });

  test('allows switching between personas', async () => {
    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    // Select adult first
    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a question as an adult/i)).toBeInTheDocument();
    });

    // Go back and select teen
    const backButton = screen.getByRole('button', { name: /back/i });
    fireEvent.click(backButton);

    const teenButton = screen.getByRole('button', { name: /select teen perspective/i });
    fireEvent.click(teenButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a question as a teen/i)).toBeInTheDocument();
    });

    // Verify adult input is no longer visible
    expect(screen.queryByPlaceholderText(/Ask a question as an adult/i)).not.toBeInTheDocument();
  });

  test('handles network errors gracefully', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Ask a question as an adult/i);
      const submitButton = screen.getByRole('button', { name: /ask as adult/i });

      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  test('clears input after successful submission', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        response: 'Test response',
        shabads: [],
        timestamp: new Date().toISOString()
      })
    });

    render(<Perspectives onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const adultButton = screen.getByRole('button', { name: /select adult perspective/i });
    fireEvent.click(adultButton);

    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Ask a question as an adult/i);
      const submitButton = screen.getByRole('button', { name: /ask as adult/i });

      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockOnResponse).toHaveBeenCalled();
    });

    // Input should be cleared
    const input = screen.getByPlaceholderText(/Ask a question as an adult/i);
    expect(input.value).toBe('');
  });
});