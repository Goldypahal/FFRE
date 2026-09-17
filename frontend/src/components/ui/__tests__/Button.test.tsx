import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Button } from '../Button';

describe('Button component', () => {
  it('renders button with children', () => {
    render(<Button>Click Me</Button>);
    const btn = screen.getByRole('button', { name: /click me/i });
    expect(btn).toBeInTheDocument();
  });

  it('handles onClick event properly', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Trigger Action</Button>);
    const btn = screen.getByRole('button', { name: /trigger action/i });
    fireEvent.click(btn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies destructive variant styles', () => {
    render(<Button variant="destructive">Delete Item</Button>);
    const btn = screen.getByRole('button', { name: /delete item/i });
    expect(btn.className).toContain('bg-[#EF4444]');
  });

  it('respects disabled attribute', () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled Button</Button>);
    const btn = screen.getByRole('button', { name: /disabled button/i });
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(handleClick).not.toHaveBeenCalled();
  });
});
