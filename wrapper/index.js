const express = require('express');
const cookieParser = require('cookie-parser');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

// configure target - in Docker Compose / container group we will call wiki service "wiki"
const WIKI_TARGET = process.env.WIKI_TARGET || 'http://wiki:3000';

// simple TOS html (replace with your real TOS)
const TOS_HTML = `
  <html>
  <head><title>Accept Terms</title></head>
  <body>
    <h1>Terms of Service</h1>
    <p>Please accept to continue.</p>
    <form method="POST" action="/accept-tos">
      <button type="submit">Accept</button>
    </form>
  </body>
  </html>
`;

// health
app.get('/healthz', (req, res) => res.json({ ok: true }));

// show TOS if no cookie
app.get('/', (req, res, next) => {
  if (req.cookies && req.cookies.tos_accepted === '1') {
    // proxy root to wiki
    return proxy(req, res);
  }
  res.send(TOS_HTML);
});

// accept TOS and set cookie (HttpOnly false so browser UI possible)
app.post('/accept-tos', (req, res) => {
  // set cookie for 365 days
  res.cookie('tos_accepted', '1', { maxAge: 365 * 24 * 3600 * 1000, httpOnly: false });
  res.redirect('/');
});

// any path under /wiki/* or everything else should be proxied to wiki
const proxyMiddleware = createProxyMiddleware({
  target: WIKI_TARGET,
  changeOrigin: true,
  ws: true,
  logLevel: 'warn',
  onError(err, req, res) {
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad gateway: ' + err.message);
  }
});

function proxy(req, res) {
  return proxyMiddleware(req, res);
}

// Mount the proxy for all routes except /tos assets etc (we handled / and /accept-tos)
app.use((req, res, next) => {
  // Allow direct health checks
  if (req.path.startsWith('/healthz')) return next();
  // if tos not accepted, show TOS
  if (!(req.cookies && req.cookies.tos_accepted === '1')) {
    return res.redirect('/');
  }
  return proxyMiddleware(req, res);
});

const port = process.env.PORT || 3001;
app.listen(port, () => {
  console.log(`TOS wrapper listening on ${port}, proxy => ${WIKI_TARGET}`);
});