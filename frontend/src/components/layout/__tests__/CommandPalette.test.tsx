import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { CommandPalette } from '../CommandPalette';

describe('CommandPalette component', () => {
  it('does not render when isOpen is false', () => {
    render(
      <MemoryRouter>
        <CommandPalette isOpen={false} onClose={() => {}} />
      </MemoryRouter>
    );
    expect(screen.queryByPlaceholderText(/Search cases, evidence/i)).not.toBeInTheDocument();
  });

  it('renders modal dialog when isOpen is true', () => {
    render(
      <MemoryRouter>
        <CommandPalette isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );
    expect(screen.getByPlaceholderText(/Search cases, evidence/i)).toBeInTheDocument();
    expect(screen.getAllByText('ESC').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('New Investigation Case')).toBeInTheDocument();
  });

  it('filters results based on category buttons', () => {
    render(
      <MemoryRouter>
        <CommandPalette isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );
    const actionsBtn = screen.getByRole('button', { name: /actions/i });
    fireEvent.click(actionsBtn);
    expect(actionsBtn.className).toContain('bg-[#FCD34D]');
  });

  it('calls onClose when Escape key is pressed or backdrop is clicked', () => {
    const handleClose = vi.fn();
    const { container } = render(
      <MemoryRouter>
        <CommandPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);

    // Also test backdrop click
    const backdrop = container.firstChild as HTMLElement;
    fireEvent.click(backdrop);
    expect(handleClose).toHaveBeenCalledTimes(2);
  });
});
