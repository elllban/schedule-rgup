import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// GitHub Pages проекта-сайта: https://<user>.github.io/<repo>/
export default defineConfig({
  site: 'https://elllban.github.io',
  base: '/schedule-rgup/',
  vite: {
    plugins: [tailwindcss()],
  },
});
