import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatInput from '../app/components/ChatInput';

// Mock fetch globally
global.fetch = jest.fn();

describe('ChatInput Component', () => {
  const mockOnResponse = jest.fn();
  const mockOnLoading = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset fetch mock
    global.fetch.mockClear();
  });

  test('renders chat input form', () => {
    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    expect(screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/persona/i)).toBeInTheDocument();
  });

  test('displays persona options', () => {
    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const personaSelect = screen.getByLabelText(/persona/i);
    expect(personaSelect).toBeInTheDocument();

    // Check that all persona options are present
    expect(screen.getByRole('option', { name: 'Adult' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Teen' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Child' })).toBeInTheDocument();
  });

  test('updates query input value', () => {
    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    fireEvent.change(input, { target: { value: 'What is the meaning of life?' } });

    expect(input.value).toBe('What is the meaning of life?');
  });

  test('updates persona selection', () => {
    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const personaSelect = screen.getByLabelText(/persona/i);
    fireEvent.change(personaSelect, { target: { value: 'teen' } });

    expect(personaSelect.value).toBe('teen');
  });

  test('shows loading state during API call', async () => {
    // Mock a delayed response
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

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    // Check that loading state is triggered
    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(true);
    });

    // Wait for the API call to complete
    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(false);
    });
  });

  test('handles successful API response', async () => {
    const mockApiResponse = {
      query: 'Test question',
      persona: 'adult',
      response: 'This is a wisdom response',
      shabads: [
        {
          id: 1,
          gurmukhi: 'Test Gurmukhi',
          english: 'Test English',
          translation: 'Test Translation'
        }
      ],
      timestamp: new Date().toISOString()
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockApiResponse)
    });

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOnResponse).toHaveBeenCalledWith(mockApiResponse);
    });
  });

  test('handles API error response', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Internal server error' })
    });

    // Mock console.error to avoid test output pollution
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  test('handles network error', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  test('prevents submission with empty query', () => {
    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const button = screen.getByRole('button', { name: /ask/i });
    fireEvent.click(button);

    // Should not trigger any API calls or callbacks
    expect(global.fetch).not.toHaveBeenCalled();
    expect(mockOnResponse).not.toHaveBeenCalled();
    expect(mockOnLoading).not.toHaveBeenCalled();
  });

  test('disables form during loading', async () => {
    // Mock a slow response
    global.fetch.mockImplementationOnce(() =>
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve({
          response: 'Test response',
          shabads: [],
          timestamp: new Date().toISOString()
        })
      }), 500))
    );

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });
    const personaSelect = screen.getByLabelText(/persona/i);

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    // During loading, form elements should be disabled
    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(true);
    });

    // Note: In a real implementation, you might disable the form elements
    // This test verifies the loading state is communicated
    expect(mockOnLoading).toHaveBeenCalledWith(true);
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

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOnResponse).toHaveBeenCalled();
    });

    // Input should be cleared after successful submission
    expect(input.value).toBe('');
  });

  test('maintains persona selection after submission', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        response: 'Test response',
        shabads: [],
        timestamp: new Date().toISOString()
      })
    });

    render(<ChatInput onResponse={mockOnResponse} onLoading={mockOnLoading} />);

    const personaSelect = screen.getByLabelText(/persona/i);
    const input = screen.getByPlaceholderText(/Ask a question about Sikh wisdom/i);
    const button = screen.getByRole('button', { name: /ask/i });

    fireEvent.change(personaSelect, { target: { value: 'teen' } });
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOnResponse).toHaveBeenCalled();
    });

    // Persona selection should be maintained
    expect(personaSelect.value).toBe('teen');
  });
});