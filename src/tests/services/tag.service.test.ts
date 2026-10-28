import prismaMock from '../prisma-mock';
import getTags from '../../app/routes/tag/tag.service';

describe('TagService', () => {
  describe('getTags', () => {
    test('should return a list of strings', async () => {
      // Given
      const mockedResponse = [
        { id: 1, name: 'dragons' },
        { id: 2, name: 'training' },
      ];

      // When
      // @ts-expect-error TS2615 (circular Prisma types) or mock payload shape
      prismaMock.tag.findMany.mockResolvedValue(mockedResponse);

      // Then
      await expect(getTags()).resolves.toEqual(['dragons', 'training']);
    });

    test('should only filter on demo authors when no id is given', async () => {
      // Given
      prismaMock.tag.findMany.mockResolvedValue([]);

      // When
      await getTags();

      // Then
      expect(prismaMock.tag.findMany).toHaveBeenCalledTimes(1);
      expect(prismaMock.tag.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: {
            articles: {
              some: {
                author: {
                  OR: [{ demo: true }],
                },
              },
            },
          },
        }),
      );
    });

    test('should also filter on the given user id', async () => {
      // Given
      const id = 123;
      prismaMock.tag.findMany.mockResolvedValue([]);

      // When
      await getTags(id);

      // Then
      expect(prismaMock.tag.findMany).toHaveBeenCalledTimes(1);
      expect(prismaMock.tag.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: {
            articles: {
              some: {
                author: {
                  OR: [{ demo: true }, { id: { equals: id } }],
                },
              },
            },
          },
        }),
      );
    });

    test('should take 10 tags ordered by article count', async () => {
      // Given
      prismaMock.tag.findMany.mockResolvedValue([]);

      // When
      await getTags();

      // Then
      expect(prismaMock.tag.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          select: { name: true },
          orderBy: {
            articles: {
              _count: 'desc',
            },
          },
          take: 10,
        }),
      );
    });

    test('should return an empty list when there are no tags', async () => {
      // Given
      prismaMock.tag.findMany.mockResolvedValue([]);

      // When
      const tags = await getTags();

      // Then
      expect(tags).toEqual([]);
    });
  });
});
