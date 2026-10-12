import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { createHttpServer } from '../server.js';

let server, base;
before(async () => {
  server = createHttpServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  base = `http://127.0.0.1:${server.address().port}`;
});
after(async () => {
  server.closeAllConnections();
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
});

test('local preview embeds the v3 sprite without external asset dependencies', async () => {
  const response = await fetch(`${base}/preview`);
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(response.headers.get('content-type'), /text\/html/);
  assert.match(html, /data:image\/webp;base64,/);
  assert.match(html, /<canvas id="pet"/);
  assert.doesNotMatch(html, /__LUMI_/);
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.ok(scripts.length > 0);
  for (const script of scripts) new Function(script[1]);
  assert.equal((await fetch(`${base}/missing`)).status, 404);
});

test('MCP initialization, tool validation and widget resources work end to end', async () => {
  const client = new Client({ name: 'lumi-integration-test', version: '1.0.0' });
  try {
    await client.connect(new StreamableHTTPClientTransport(new URL(`${base}/mcp`)));
    const { tools } = await client.listTools();
    const tool = tools.find(value => value.name === 'show_lumi');
    assert.ok(tool);
    const result = await client.callTool({ name: 'show_lumi', arguments: { mode: 'comfort', message: ' 慢慢来 ', action: 'waving' } });
    assert.deepEqual(result.structuredContent, { mode: 'comfort', message: '慢慢来', action: 'waving' });
    const defaults = await client.callTool({ name: 'show_lumi', arguments: {} });
    assert.equal(defaults.structuredContent.mode, 'companion');
    assert.equal(defaults.structuredContent.action, 'idle');
    const invalid = await client.callTool({ name: 'show_lumi', arguments: { mode: 'invalid' } });
    assert.equal(invalid.isError, true);
    const resource = await client.readResource({ uri: tool._meta.ui.resourceUri });
    assert.match(resource.contents[0].mimeType, /text\/html/);
    assert.match(resource.contents[0].text, /data:image\/webp;base64,/);
  } finally {
    await client.close();
  }
});
