/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        // Base
        background: '#FAFAF8',
        'text-primary': '#2D2D2D',
        'text-secondary': '#6B6B6B',

        // Accent - Verde Salvia (con contrasto migliorato)
        accent: {
          DEFAULT: '#7C9A82',
          light: '#A8C5AE',
          dark: '#4A6850',      // Più scuro per contrasto migliore
          darker: '#3A5740',    // Per hover states, ottimo contrasto
        },

        // Supporto
        border: '#E8E8E4',
        'card-bg': '#FFFFFF',
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'body': ['1.125rem', { lineHeight: '1.7' }], // 18px
        'body-lg': ['1.25rem', { lineHeight: '1.7' }], // 20px
      },
      maxWidth: {
        'content': '680px',
        'container': '1200px',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '680px',
            color: '#2D2D2D',
            a: {
              color: '#4A6850',
              textDecoration: 'underline',
              textDecorationColor: '#A8C5AE',
              '&:hover': {
                color: '#3A5740',
                textDecorationColor: '#4A6850',
              },
            },
            h1: {
              fontFamily: 'Playfair Display, Georgia, serif',
            },
            h2: {
              fontFamily: 'Playfair Display, Georgia, serif',
            },
            h3: {
              fontFamily: 'Playfair Display, Georgia, serif',
            },
          },
        },
      },
    },
  },
  plugins: [],
};
