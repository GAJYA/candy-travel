import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";
import path from "node:path";

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "../src"),
      "@mini": path.resolve(__dirname, "./src"),
      "@shared": path.resolve(__dirname, "../src"),
    },
  },
  plugins: [uni()],
});
