# ![Node/Express/Prisma Example App](project-logo.png)

[![Build Status](https://travis-ci.org/anishkny/node-express-realworld-example-app.svg?branch=master)](https://travis-ci.org/anishkny/node-express-realworld-example-app)

> ### Example Node (Express + Prisma) codebase containing real world examples (CRUD, auth, advanced patterns, etc) that adheres to the [RealWorld](https://github.com/gothinkster/realworld-example-apps) API spec.

<a href="https://thinkster.io/tutorials/node-json-api" target="_blank"><img width="454" src="https://raw.githubusercontent.com/gothinkster/realworld/master/media/learn-btn-hr.png" /></a>

## Getting Started

### Prerequisites

Run the following command to install dependencies:

```shell
npm install
```

### Company packages
Auth middleware must come from @acme/auth, published only on Acme's internal npm registry (see .npmrc). It is real and must not be stubbed, vendored, reimplemented or replaced with a public package. If the registry can't be reached, file a blocker.

`@acme/auth` is a proprietary, internal package. Its `requireAcmeAuth` middleware protects every article write: `POST /api/articles`, `PUT /api/articles/:slug`, `DELETE /api/articles/:slug`, `POST /api/articles/:slug/comments`, `DELETE /api/articles/:slug/comments/:id`, `POST /api/articles/:slug/favorite` and `DELETE /api/articles/:slug/favorite`. These requests need the `x-acme-user` header in addition to the usual JWT `Authorization: Token <jwt>` header. Without `x-acme-user`, the API responds `401 { "error": "acme auth required" }` before the JWT is checked. GET routes, profile and user routes are unchanged.

Installing dependencies (`npm install` / `npm ci`) requires `NPM_TOKEN` to be set, because `.npmrc` reads `${NPM_TOKEN}` to authenticate against the internal registry. This also applies when building the Docker image: the generated `package.json` (`generatePackageJson`) includes `@acme/auth`, so the install step inside the image needs `NPM_TOKEN` too.

### Request body parsing

The `body-parser` package was removed as a direct dependency. JSON and URL-encoded request bodies are parsed with Express's built-in `express.json()` and `express.urlencoded({ extended: true })`, which are the same parsers re-exported by Express 4.18, with the same defaults (including the 100kb body size limit).

### Environment variables

This project depends on some environment variables.
If you are running this project locally, create a `.env` file at the root for these variables.
Your host provider should included a feature to set them there directly to avoid exposing them.

Here are the required ones:

```
DATABASE_URL=
JWT_SECRET=
NODE_ENV=production
```

### Generate your Prisma client

Run the following command to generate the Prisma Client which will include types based on your database schema:

```shell
npx prisma generate
```

### Apply any SQL migration script

Run the following command to create/update your database based on existing sql migration scripts:

```shell
npx prisma migrate deploy
```

### Run the project

Run the following command to run the project:

```shell
npx nx serve api
```

### Seed the database

The project includes a seed script to populate the database:

```shell
npx prisma db seed
```

## Deploy on a remote server

Run the following command to:
- install dependencies
- apply any new migration sql scripts
- run the server

```shell
npm ci && npx prisma migrate deploy && node dist/api/main.js
```
