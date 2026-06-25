/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Modern Premium Dark/Light UI Theme
        brand: {
          50: '#f5f7ff',
          100: '#ebefff',
          200: '#dce3ff',
          300: '#c2cdff',
          400: '#9db0ff',
          500: '#6d84ff',
          600: '#4d5eff',
          700: '#3945eb',
          800: '#2f37c2',
          900: '#2b319c',
          950: '#1a1c5c',
        },
        slate: {
          950: '#0b0f19',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(12px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
