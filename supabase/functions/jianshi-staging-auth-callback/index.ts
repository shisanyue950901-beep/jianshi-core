// Staging-only HTTP redirect. Do not deploy to production Supabase.
// Supabase Edge gateways sandbox text/html as text/plain. Never render HTML here.
// The browser inherits the original URL fragment on 302 (RFC 9110), preserving
// Auth tokens *only in the browser*; fragments are never sent to this server.
const STAGING_REF = 'apuibjhxinumxbfnqlkp';
const DESTINATION = 'https://staging-auth-callback.jianshi-bua.pages.dev/_qa/staging-auth/';
const headers = {
  'cache-control': 'no-store, max-age=0',
  'referrer-policy': 'no-referrer',
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY'
};
Deno.serve((req: Request) => {
  const u = new URL(req.url);
  if (u.hostname !== STAGING_REF + '.supabase.co') {
    return new Response(null, {status:403,headers});
  }
  if (req.method !== 'GET') {
    return new Response(null, {status:405,headers:{...headers,allow:'GET'}});
  }
  return new Response(null, {status:302,headers:{...headers,location:DESTINATION}});
});
