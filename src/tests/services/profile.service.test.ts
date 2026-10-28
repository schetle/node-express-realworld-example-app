import prismaMock from '../prisma-mock';
import { followUser, getProfile, unfollowUser } from '../../app/routes/profile/profile.service';
import HttpException from '../../app/models/http-exception.model';

describe('ProfileService', () => {
  describe('getProfile', () => {
    test('should return a following property', async () => {
      // Given
      const username = 'RealWorld';
      const id = 123;

      const mockedResponse = {
        id: 123,
        username: 'RealWorld',
        email: 'realworld@me',
        password: '1234',
        bio: null,
        image: null,
        token: '',
        demo: false,
        followedBy: [],
      };

      // When
      // @ts-ignore
      prismaMock.user.findUnique.mockResolvedValue(mockedResponse);

      // Then
      await expect(getProfile(username, id)).resolves.toHaveProperty('following');
    });

    test('should throw an error if no user is found', async () => {
      // Given
      const username = 'RealWorld';
      const id = 123;

      // When
      prismaMock.user.findUnique.mockResolvedValue(null);

      // Then
      await expect(getProfile(username, id)).rejects.toThrowError();
    });

    test('should return following true when the caller follows the user', async () => {
      // Given
      const username = 'RealWorld';
      const id = 456;

      const mockedResponse = {
        id: 123,
        username: 'RealWorld',
        email: 'realworld@me',
        password: '1234',
        bio: null,
        image: null,
        demo: false,
        followedBy: [
          {
            id: 456,
            username: 'Follower',
            email: 'follower@me',
            password: '1234',
            bio: null,
            image: null,
            demo: false,
          },
        ],
      };

      // When
      prismaMock.user.findUnique.mockResolvedValue(mockedResponse);

      // Then
      await expect(getProfile(username, id)).resolves.toHaveProperty('following', true);
    });

    test('should return following false for an anonymous caller', async () => {
      // Given
      const username = 'RealWorld';

      const mockedResponse = {
        id: 123,
        username: 'RealWorld',
        email: 'realworld@me',
        password: '1234',
        bio: null,
        image: null,
        demo: false,
        followedBy: [
          {
            id: 456,
            username: 'Follower',
            email: 'follower@me',
            password: '1234',
            bio: null,
            image: null,
            demo: false,
          },
        ],
      };

      // When
      prismaMock.user.findUnique.mockResolvedValue(mockedResponse);

      // Then
      await expect(getProfile(username)).resolves.toHaveProperty('following', false);
    });

    test('should throw an HttpException with a 404 errorCode if no user is found', async () => {
      // Given
      const username = 'RealWorld';
      const id = 123;

      // When
      prismaMock.user.findUnique.mockResolvedValue(null);

      // Then
      const promise = getProfile(username, id);
      await expect(promise).rejects.toBeInstanceOf(HttpException);
      await expect(promise).rejects.toHaveProperty('errorCode', 404);
    });
  });

  describe('followUser', () => {
    test('shoud return a following property', async () => {
      // Given
      const usernamePayload = 'AnotherUser';
      const id = 123;

      const mockedAuthUser = {
        id: 123,
        username: 'RealWorld',
        email: 'realworld@me',
        password: '1234',
        bio: null,
        image: null,
        token: '',
        demo: false,
        followedBy: [],
      };

      const mockedResponse = {
        id: 123,
        username: 'AnotherUser',
        email: 'another@me',
        password: '1234',
        bio: null,
        image: null,
        token: '',
        demo: false,
        followedBy: [],
      };

      // When
      prismaMock.user.findUnique.mockResolvedValue(mockedAuthUser);
      prismaMock.user.update.mockResolvedValue(mockedResponse);

      // Then
      await expect(followUser(usernamePayload, id)).resolves.toHaveProperty('following');
    });

    test('shoud throw an error if no user is found', async () => {
      // Given
      const usernamePayload = 'AnotherUser';
      const id = 123;

      // When
      prismaMock.user.findUnique.mockResolvedValue(null);

      // Then
      await expect(followUser(usernamePayload, id)).rejects.toThrowError();
    });

    test('should call prisma.user.update with connect', async () => {
      // Given
      const usernamePayload = 'AnotherUser';
      const id = 123;

      const mockedResponse = {
        id: 456,
        username: 'AnotherUser',
        email: 'another@me',
        password: '1234',
        bio: null,
        image: null,
        demo: false,
        followedBy: [],
      };

      // When
      prismaMock.user.update.mockResolvedValue(mockedResponse);
      await followUser(usernamePayload, id);

      // Then
      expect(prismaMock.user.update).toHaveBeenCalledTimes(1);
      expect(prismaMock.user.update).toHaveBeenCalledWith({
        where: {
          username: usernamePayload,
        },
        data: {
          followedBy: {
            connect: {
              id,
            },
          },
        },
        include: {
          followedBy: true,
        },
      });
    });
  });

  describe('unfollowUser', () => {
    test('shoud return a following property', async () => {
      // Given
      const usernamePayload = 'AnotherUser';
      const id = 123;

      const mockedAuthUser = {
        id: 123,
        username: 'RealWorld',
        email: 'realworld@me',
        password: '1234',
        bio: null,
        image: null,
        token: '',
        demo: false,
        followedBy: [],
      };

      const mockedResponse = {
        id: 123,
        username: 'AnotherUser',
        email: 'another@me',
        password: '1234',
        bio: null,
        image: null,
        token: '',
        demo: false,
        followedBy: [],
      };

      // When
      prismaMock.user.findUnique.mockResolvedValue(mockedAuthUser);
      prismaMock.user.update.mockResolvedValue(mockedResponse);

      // Then
      await expect(unfollowUser(usernamePayload, id)).resolves.toHaveProperty('following');
    });

    test('shoud throw an error if no user is found', async () => {
      // Given
      const usernamePayload = 'AnotherUser';
      const id = 123;

      // When
      prismaMock.user.findUnique.mockResolvedValue(null);

      // Then
      await expect(unfollowUser(usernamePayload, id)).rejects.toThrowError();
    });

    test('should call prisma.user.update with disconnect', async () => {
      // Given
      const usernamePayload = 'AnotherUser';
      const id = 123;

      const mockedResponse = {
        id: 456,
        username: 'AnotherUser',
        email: 'another@me',
        password: '1234',
        bio: null,
        image: null,
        demo: false,
        followedBy: [],
      };

      // When
      prismaMock.user.update.mockResolvedValue(mockedResponse);
      await unfollowUser(usernamePayload, id);

      // Then
      expect(prismaMock.user.update).toHaveBeenCalledTimes(1);
      expect(prismaMock.user.update).toHaveBeenCalledWith({
        where: {
          username: usernamePayload,
        },
        data: {
          followedBy: {
            disconnect: {
              id,
            },
          },
        },
        include: {
          followedBy: true,
        },
      });
    });
  });
});
