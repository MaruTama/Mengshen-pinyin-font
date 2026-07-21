/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0b0e14',
          raised: '#131722',
          overlay: '#1a2030',
        },
        line: '#252c3d',
        accent: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
        },
      },
    },
  },
  plugins: [],
}
