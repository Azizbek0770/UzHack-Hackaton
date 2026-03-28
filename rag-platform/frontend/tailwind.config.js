export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        slate: {
          950: "#0b0f1a"
        }
      },
      boxShadow: {
        card: "0 12px 32px rgba(15, 23, 42, 0.35)"
      }
    }
  },
  plugins: []
};
