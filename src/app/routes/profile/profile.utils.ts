import { User } from '../auth/user.model';
import { Profile } from './profile.model';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const profileMapper = (user: any, id: number | undefined): Profile => ({
  username: user.username,
  bio: user.bio,
  image: user.image,
  following: id
    ? user?.followedBy.some((followingUser: Partial<User>) => followingUser.id === id)
    : false,
});

export default profileMapper;
