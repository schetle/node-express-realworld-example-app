// prisma-mock must be imported before the app so the real Prisma client is never loaded.
import prismaMock from '../prisma-mock';
import * as http from 'http';
import { AddressInfo } from 'net';
import * as jwt from 'jsonwebtoken';
import app from '../../app';

const secret = process.env.JWT_SECRET ?? 'superSecret';
const token = jwt.sign({ user: { id: 1 } }, secret, { expiresIn: '60d' });

// Untyped view of the deep mock: accessing Prisma delegates through DeepMockProxy's
// generated types triggers TS2615 (circular mapped type), so look methods up by name.
const prismaMocks = prismaMock as unknown as Record<
  string,
  Record<string, jest.Mock>
>;
const prismaMethodMock = (prismaMethod: string): jest.Mock => {
  const [model, method] = prismaMethod.split('.');
  return prismaMocks[model][method];
};

interface WriteRouteCase {
  method: 'POST' | 'PUT' | 'DELETE';
  path: string;
  body?: unknown;
  prismaMethod: string;
}

const cases: WriteRouteCase[] = [
  {
    method: 'POST',
    path: '/api/articles',
    body: {
      article: {
        title: 'Title',
        description: 'Desc',
        body: 'Body',
        tagList: [],
      },
    },
    prismaMethod: 'article.create',
  },
  {
    method: 'PUT',
    path: '/api/articles/some-slug',
    body: { article: { title: 'New title' } },
    prismaMethod: 'article.update',
  },
  {
    method: 'DELETE',
    path: '/api/articles/some-slug',
    prismaMethod: 'article.delete',
  },
  {
    method: 'POST',
    path: '/api/articles/some-slug/comments',
    body: { comment: { body: 'Nice article' } },
    prismaMethod: 'comment.create',
  },
  {
    method: 'DELETE',
    path: '/api/articles/some-slug/comments/1',
    prismaMethod: 'comment.delete',
  },
  {
    method: 'POST',
    path: '/api/articles/some-slug/favorite',
    prismaMethod: 'article.update',
  },
  {
    method: 'DELETE',
    path: '/api/articles/some-slug/favorite',
    prismaMethod: 'article.update',
  },
];

describe('Article write routes require @acme/auth', () => {
  let server: http.Server;
  let baseUrl: string;

  beforeAll(async () => {
    server = http.createServer(app);
    await new Promise<void>((resolve) => server.listen(0, resolve));
    const { port } = server.address() as AddressInfo;
    baseUrl = `http://127.0.0.1:${port}`;
  });

  afterAll(async () => {
    await new Promise<void>((resolve, reject) =>
      server.close((err) => (err ? reject(err) : resolve()))
    );
  });

  const send = (
    method: string,
    path: string,
    headers: Record<string, string>,
    body?: unknown
  ): Promise<Response> =>
    fetch(`${baseUrl}${path}`, {
      method,
      headers: {
        ...headers,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });

  test.each(cases)(
    '$method $path returns 401 without x-acme-user and does not call prisma.$prismaMethod',
    async ({ method, path, body, prismaMethod }) => {
      const res = await send(
        method,
        path,
        { Authorization: `Token ${token}` },
        body
      );

      expect(res.status).toBe(401);
      expect(await res.json()).toEqual({ error: 'acme auth required' });
      expect(prismaMethodMock(prismaMethod)).not.toHaveBeenCalled();
    }
  );

  test('passes the Acme check when x-acme-user is present with a valid JWT', async () => {
    prismaMethodMock('article.update').mockResolvedValue({
      slug: 'some-slug',
      tagList: [],
      author: { username: 'RealWorld', bio: null, image: null, followedBy: [] },
      favoritedBy: [{ id: 1 }],
      _count: { favoritedBy: 1 },
    });

    const res = await send('POST', '/api/articles/some-slug/favorite', {
      Authorization: `Token ${token}`,
      'x-acme-user': 'acme-user-1',
    });
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json).not.toEqual({ error: 'acme auth required' });
    expect(json.article.favorited).toBe(true);
    expect(prismaMethodMock('article.update')).toHaveBeenCalledTimes(1);
  });

  test('still requires a JWT when x-acme-user is present', async () => {
    const res = await send('POST', '/api/articles/some-slug/favorite', {
      'x-acme-user': 'acme-user-1',
    });

    expect(res.status).toBe(401);
    expect(await res.json()).toEqual({
      status: 'error',
      message: 'missing authorization credentials',
    });
    expect(prismaMethodMock('article.update')).not.toHaveBeenCalled();
  });
});
