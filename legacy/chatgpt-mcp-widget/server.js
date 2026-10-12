import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from '@modelcontextprotocol/ext-apps/server';
import { z } from 'zod';

const here = dirname(fileURLToPath(import.meta.url));
const image = readFileSync(join(here, '../../assets/pets/lumi-actions-v3/spritesheet.webp')).toString('base64');
const widgetHtml = readFileSync(join(here, 'public/lumi-widget.html'), 'utf8')
  .replace('__LUMI_SPRITESHEET__', `data:image/webp;base64,${image}`);
const RESOURCE_URI = 'ui://lumi/pet-v1.html';
const modes = ['companion', 'focus', 'comfort'];
const actions = ['idle', 'running-right', 'running-left', 'waving', 'jumping', 'failed', 'waiting', 'running', 'review'];
const defaultMessages = {
  companion: '我在这里。想从哪个念头开始？',
  focus: '我会安静陪着你。',
  comfort: '先缓一口气，我们慢慢来。',
};

function makeServer() {
  const server = new McpServer({
    name: 'lumi-chatgpt-pet',
    version: '0.2.0',
    instructions: 'When the user asks to summon, show, or update Lumi, call show_lumi. Lumi is a small companion widget. It can use conversation context provided to the tool, but it cannot observe chats in the background. Keep companion messages short and gentle.',
  });

  registerAppResource(server, 'lumi-pet', RESOURCE_URI, {}, async () => ({
    contents: [{
      uri: RESOURCE_URI,
      mimeType: RESOURCE_MIME_TYPE,
      text: widgetHtml,
      _meta: { ui: { prefersBorder: false } },
    }],
  }));

  registerAppTool(server, 'show_lumi', {
    title: 'Show Lumi',
    description: 'Show or update the Lumi companion pet inside this ChatGPT conversation. Use when the user asks to call Lumi, change her mood, keep her company while working, or have Lumi gently respond to the current discussion. The pet can be pinned in picture-in-picture by the user. Do not call for unrelated requests.',
    inputSchema: {
      action: z.enum(actions).optional().describe('Animation state for Lumi; defaults to idle'),
      mode: z.enum(modes).optional().describe('companion for ordinary company, focus for quiet work, comfort for emotional support'),
      message: z.string().max(100).optional().describe('One short, gentle sentence for Lumi to say, based only on conversation context available to you'),
    },
    outputSchema: {
      action: z.enum(actions),
      mode: z.enum(modes),
      message: z.string(),
    },
    _meta: {
      ui: { resourceUri: RESOURCE_URI },
      'openai/toolInvocation/invoking': 'Lumi 正在过来…',
      'openai/toolInvocation/invoked': 'Lumi 已来到对话中',
    },
  }, async ({ mode, message, action }) => {
    const safeMode = modes.includes(mode) ? mode : 'companion';
    const safeMessage = message?.trim().slice(0, 100) || defaultMessages[safeMode];
    return {
      structuredContent: { mode: safeMode, message: safeMessage, action: actions.includes(action) ? action : 'idle' },
      content: [{ type: 'text', text: `Lumi is visible in ${safeMode} mode and says: ${safeMessage}` }],
    };
  });
  return server;
}

export function createHttpServer() {
return createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
  if (req.method === 'GET' && url.pathname === '/') {
    res.writeHead(200, { 'content-type': 'text/plain; charset=utf-8' }).end('Lumi mini app is running. Preview: /preview | MCP: /mcp');
    return;
  }
  if (req.method === 'GET' && url.pathname === '/preview') {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }).end(widgetHtml);
    return;
  }
  if (req.method === 'OPTIONS' && url.pathname === '/mcp') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'content-type, mcp-session-id, mcp-protocol-version, authorization',
      'Access-Control-Expose-Headers': 'Mcp-Session-Id',
    }).end();
    return;
  }
  if (url.pathname !== '/mcp' || !['POST', 'GET', 'DELETE'].includes(req.method || '')) {
    res.writeHead(404).end('Not found');
    return;
  }
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Expose-Headers', 'Mcp-Session-Id');
  const server = makeServer();
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  res.on('close', () => { transport.close(); server.close(); });
  try {
    await server.connect(transport);
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('MCP request failed:', error);
    if (!res.headersSent) res.writeHead(500).end('Internal server error');
  }
});
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 8787);
  const host = process.env.HOST || '127.0.0.1';
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be an integer between 0 and 65535');
  const httpServer = createHttpServer();
  httpServer.on('error', error => { console.error(error.message); process.exitCode = 1; });
  httpServer.listen(port, host, () => {
    const actualPort = httpServer.address().port;
    console.log(`Lumi preview: http://${host}:${actualPort}/preview`);
    console.log(`Lumi MCP server: http://${host}:${actualPort}/mcp`);
  });
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => httpServer.close());
}
