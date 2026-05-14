import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        body: ['var(--font-body)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Georgia', 'serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      colors: {
        bg:          'var(--bg)',
        'bg-alt':    'var(--bg-alt)',
        surface:     'var(--surface)',
        card:        'var(--card)',
        hover:       'var(--hover)',
        ink:         'var(--ink)',
        'ink-2':     'var(--ink-2)',
        'ink-3':     'var(--ink-3)',
        'ink-4':     'var(--ink-4)',
        accent:      'var(--accent)',
        'accent-hover': 'var(--accent-hover)',
      },
    },
  },
  plugins: [],
};

export default config;
