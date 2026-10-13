// F2.1 G2-H.7H isolated Cloudflare Worker scaffold: NEVER AUTHENTICATES.
// Non-functional denial endpoint. No imports, secret bindings, network, cookies,
// tenant data, analytics, passwords or routes. A cloud deploy is NOT authorized.
const HEADERS=Object.freeze({
 'content-type':'text/plain; charset=utf-8',
 'cache-control':'no-store, max-age=0',
 'referrer-policy':'no-referrer',
 'x-robots-tag':'noindex, nofollow, noarchive',
 'content-security-policy':"default-src 'none'; frame-ancestors 'none'",
 'x-content-type-options':'nosniff',
});
export default {
 async fetch(_request,_env,_ctx){
  // Deliberately reject even a valid /auth/confirm or /cms/ request.
  return new Response('Not Found',{status:404,headers:HEADERS});
 }
};
