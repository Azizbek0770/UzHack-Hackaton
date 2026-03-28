import dns from "node:dns";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

dns.setDefaultResultOrder("verbatim");

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ["react", "react-dom"]
  },
  server: {
    host: "localhost",
    port: 5173,
    strictPort: true,
    allowedHosts: ["localhost", "127.0.0.1"],
    hmr: {
      host: "localhost",
      protocol: "ws",
      clientPort: 5173
    }
  }
});
