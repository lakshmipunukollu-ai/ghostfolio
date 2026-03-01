#!/usr/bin/env node
/**
 * Set a known access token for the first admin user so we can get a bearer token.
 * Uses the same HMAC-SHA512 hashing as Ghostfolio.
 *
 * Usage: node scripts/set-access-token.js [plain_token]
 * Default token: openfinance
 */

const crypto = require('crypto');
const { Client } = require('pg');

const ACCESS_TOKEN_SALT = process.env.ACCESS_TOKEN_SALT || 'e54b56e57e2a69ec3eb94281479de1692235a37dfa06c818b50fde8a8c9a10f3';
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://ghostfolio:password123@localhost:5432/ghostfolio?sslmode=prefer';
const plainToken = process.argv[2] || 'openfinance';

function createAccessToken(password, salt) {
  const hash = crypto.createHmac('sha512', salt);
  hash.update(password);
  return hash.digest('hex');
}

async function main() {
  const hashedAccessToken = createAccessToken(plainToken, ACCESS_TOKEN_SALT);
  const client = new Client({ connectionString: DATABASE_URL });
  await client.connect();

  const res = await client.query(
    'UPDATE "User" SET "accessToken" = $1 WHERE id = (SELECT id FROM "User" LIMIT 1) RETURNING id, role',
    [hashedAccessToken]
  );

  if (res.rowCount === 0) {
    console.error('No user found in database');
    process.exit(1);
  }

  console.log(`Updated user ${res.rows[0].id} (${res.rows[0].role}) with access token.`);
  console.log(`\nUse this token to authenticate:`);
  console.log(`  Plain access token: ${plainToken}`);
  console.log(`\nGet bearer token with:`);
  console.log(`  curl -s -X POST http://localhost:3333/api/v1/auth/anonymous \\`);
  console.log(`    -H "Content-Type: application/json" \\`);
  console.log(`    -d '{"accessToken":"${plainToken}"}'`);
  await client.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
