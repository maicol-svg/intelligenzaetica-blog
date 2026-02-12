import { defineCollection, z } from 'astro:content';

const articlesCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    author: z.enum(['marco', 'elena', 'luca', 'sofia', 'alessandro']),
    publishedAt: z.string().or(z.date()),
    category: z.enum([
      'ia-etica',
      'tech',
      'tutorial',
      'finanza',
      'psicologia',
      'ecosostenibile',
      // Nuove categorie
      'sport',
      'salute',
      'creativita',
      'quotidiano'
    ]),
    tags: z.array(z.string()).optional().default([]),
    featuredImage: z.string().optional(),
    imageCredit: z.string().optional(),
    imageCreditUrl: z.string().optional(),
    aiGenerated: z.boolean().default(true),
    reviewedBy: z.string().optional().default('alessandro'),
    humanReview: z.boolean().default(false),
  }),
});

export const collections = {
  articles: articlesCollection,
};
