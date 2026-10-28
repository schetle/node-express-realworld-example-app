import authorMapper from './author.mapper';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const articleMapper = (article: any, id?: number) => ({
  slug: article.slug,
  title: article.title,
  description: article.description,
  body: article.body,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  tagList: article.tagList.map((tag: any) => tag.name),
  createdAt: article.createdAt,
  updatedAt: article.updatedAt,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  favorited: article.favoritedBy.some((item: any) => item.id === id),
  favoritesCount: article.favoritedBy.length,
  author: authorMapper(article.author, id),
});

export default articleMapper;
