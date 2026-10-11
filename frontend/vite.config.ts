import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "DevLab",
        short_name: "DevLab",
        theme_color: "#111",
        background_color: "#111",
        display: "standalone",
        start_url: "/",
        icons: [],
      },
    }),
  ],
  server: { port: 5173 },
});