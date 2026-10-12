import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import App from './App';

describe('application shell', () => {
  it('renders the input screen in the main landmark', () => {
    render(<App />);

    expect(screen.getByRole('main')).toContainElement(
      screen.getByRole('heading', { name: 'Generate infrastructure', level: 1 }),
    );
  });

  it('offers a keyboard-reachable skip link to the focusable main content', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.tab();

    expect(screen.getByRole('link', { name: 'Skip to content' })).toHaveFocus();
    expect(screen.getByRole('link', { name: 'Skip to content' })).toHaveAttribute(
      'href',
      `#${screen.getByRole('main').id}`,
    );
    expect(screen.getByRole('main')).toHaveAttribute('tabindex', '-1');
  });
});
