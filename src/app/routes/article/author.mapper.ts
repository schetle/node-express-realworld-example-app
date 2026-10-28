import { User } from '../auth/user.model';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const authorMapper = (author: any, id?: number) => ({
  username: author.username,
  bio: author.bio,
  image: author.image,
  following: id
    ? author?.followedBy.some((followingUser: Partial<User>) => followingUser.id === id)
    : false,
});

export default authorMapper;
