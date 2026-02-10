import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://intelligenzaetica.blog',
  integrations: [tailwind()],
  markdown: {
    shikiConfig: {
      theme: 'github-light',
    },
  },
});
