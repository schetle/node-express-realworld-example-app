import { Article } from '../article/article.model';
import { Comment } from '../article/comment.model';

export interface User {
  id: number;
  username: string;
  email: string;
  password: string;
  bio: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  image: any | null;
  articles: Article[];
  favorites: Article[];
  followedBy: User[];
  following: User[];
  comments: Comment[];
  demo: boolean;
}
