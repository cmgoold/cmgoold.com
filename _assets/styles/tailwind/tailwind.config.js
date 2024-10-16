/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../../templates/**/*.{html,js}"],
  theme: {
      screens: {
          'sm': "300px",
          'md': '640px',
          'lg': '1024px',
          'xl': '1280px',
          '2xl': '1536px',
      },
      fontFamily: {
          'mono': ['Inconsolata'],
      },
      extend: {},
  },
  plugins: [],
}

