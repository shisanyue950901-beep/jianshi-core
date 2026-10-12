// JIANSHI G2-H.7C — disposable, loopback-only HTTPS confirmation preview.
// NOT Cloudflare Pages Functions; NOT a deployed Staging or Production route.
// All auth, identities, providers and SQL stores MUST be synthetic/injected.
// No HTTP endpoint initiates login; mail send is only callable by isolated tests.
import https from 'node:https';

const SAFE_HEADERS=Object.freeze({
 'cache-control':'no-store, max-age=0',
 'pragma':'no-cache',
 'referrer-policy':'no-referrer',
 'x-content-type-options':'nosniff',
 'x-frame-options':'DENY',
 'x-robots-tag':'noindex, nofollow, noarchive',
 'strict-transport-security':'max-age=0',
 'content-security-policy':"default-src 'none'; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
});
const CONFIRM_PAGE='<!doctype html>\n<html lang="zh-CN"><head>'+
 '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
 '<meta name="robots" content="noindex,nofollow">'+
 '<title>见势隔离邮箱确认</title></head><body><main>'+
 '<h1>隔离邮箱登录确认</h1>'+
 '<p>这只是合成环境的安全测试，并非正式见势 CMS 登录。</p>'+
 '<p>只有在你主动点击后，系统才会尝试完成一次性邮箱验证。</p>'+
 '<form method="post" action="/auth/confirm"><button type="submit">确认测试登录</button></form>'+
 '</main></body></html>';
const DENIED_PAGE='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'+
 '<title>测试不可用</title></head><body><p>验证请求无效或已失效，请重新开始隔离测试。</p></body></html>';
const INTENT_COOKIE=/^__Host-jianshi_mail_intent=v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;
const STATE_COOKIE=/^__Host-jianshi_mail_state=[A-Za-z0-9_-]{43}$/;
function cookiesArePresent(header) {
 const parts=String(header||'').split(';').map(p=>p.trim());
 return parts.filter(p=>INTENT_COOKIE.test(p)).length===1 &&
        parts.filter(p=>STATE_COOKIE.test(p)).length===1;
}
function answer(res,status,body='',headers={}) {
 const normalized=typeof body==='string'?body:'';
 res.writeHead(status,{
  ...SAFE_HEADERS,'content-type':'text/html; charset=utf-8',
  'content-length':Buffer.byteLength(normalized),
  ...headers
 });
 res.end(normalized);
}
function rejectExternalCredentials(){
 for(const k of [
  'DATABASE_URL','SUPABASE_URL','SUPABASE_DB_URL','SUPABASE_SERVICE_ROLE_KEY',
  'SUPABASE_SECRET_KEY','SUPABASE_ACCESS_TOKEN','CLOUDFLARE_API_TOKEN'
 ])if(process.env[k])throw Error('CMS_H7C_EXTERNAL_CREDENTIALS_DENIED');
}
export function createLoopbackEmailHttpsPreview({tls,makeController}={}){
 if(process.env.JIANSHI_G2H7C_SYNTHETIC_ONLY!=='1')throw Error('CMS_H7C_LIVE_DISABLED');
 rejectExternalCredentials();
 if(!tls?.key||!tls?.cert||typeof makeController!=='function')
  throw Error('CMS_H7C_TEST_TLS_AND_FACTORY_REQUIRED');
 let controller=null,origin=null;
 const server=https.createServer({key:tls.key,cert:tls.cert},
  async(req,res)=>{
   // No request URL, Cookie, query, token_hash, state, or HTTP body may be logged.
   try {
    const address=server.address();
    if(!address||req.socket.encrypted!==true||
       req.socket.remoteAddress!=='127.0.0.1'||
       req.headers.host!=='localhost:'+address.port||
       req.headers['x-forwarded-host']||req.headers['x-forwarded-proto']||
       !controller) {
      return answer(res,403,DENIED_PAGE);
    }
    if(typeof req.url!=='string'||req.url.length>2048)
      return answer(res,404,DENIED_PAGE);
    // HTTPS only; the hostname and port must be controlled by the server,
    // never inferred from client-supplied Forwarded / Host headers.
    const target=new URL(req.url,origin);
    if(target.pathname!=='/auth/confirm'||target.hash)
      return answer(res,404,DENIED_PAGE);
    if(req.method==='GET'&&target.search){
     const result=await controller.receiveLink({
      url:req.url,cookieHeader:req.headers.cookie,requestOrigin:origin
     });
     if(result.status!==303||result.location!=='/auth/confirm'||
        !Array.isArray(result.setCookies)||result.setCookies.length!==1)
      throw Error('CMS_H7C_BAD_RECEIVE_ADAPTER');
     return answer(res,303,'',{
      location:'/auth/confirm','set-cookie':result.setCookies
     });
    }
    if(req.method==='GET'&&!target.search){
     if(!cookiesArePresent(req.headers.cookie))
      return answer(res,403,DENIED_PAGE);
     return answer(res,200,CONFIRM_PAGE);
    }
    if(req.method==='POST'&&!target.search){
     if(req.headers['content-type']!== 'application/x-www-form-urlencoded')
      return answer(res,415,DENIED_PAGE);
     let size=0;
     for await(const chunk of req){
      size+=chunk.length;
      if(size>0)return answer(res,413,DENIED_PAGE);
     }
     const result=await controller.confirm({
      url:'/auth/confirm',method:'POST',
      requestOrigin:req.headers.origin,
      fetchSite:req.headers['sec-fetch-site'],
      cookieHeader:req.headers.cookie
     });
     if(result.status!==303||result.location!=='/cms/'||
       !Array.isArray(result.setCookies)||result.setCookies.length!==3)
      throw Error('CMS_H7C_BAD_CONFIRM_ADAPTER');
     return answer(res,303,'',{
      location:'/cms/','set-cookie':result.setCookies
     });
    }
    return answer(res,405,DENIED_PAGE,{allow:'GET, POST'});
   } catch {
    // A generic response prevents leaking SQL / GoTrue / cookie error values.
    return answer(res,403,DENIED_PAGE);
   }
  });
 return Object.freeze({
  server,
  async listen(){
   if(origin)throw Error('CMS_H7C_ALREADY_LISTENING');
   await new Promise((resolve,reject)=>{
    server.once('error',reject);
    server.listen(0,'127.0.0.1',()=>{
     server.removeListener('error',reject);resolve();
    });
   });
   origin='https://localhost:'+server.address().port;
   try{
    controller=makeController(origin);
    if(!controller||typeof controller.start!=='function'||
       typeof controller.receiveLink!=='function'||typeof controller.confirm!=='function')
     throw Error('CMS_H7C_BAD_CONFIRM_ADAPTER');
   }catch(error){
    await new Promise(resolve=>server.close(resolve));
    throw error;
   }
   return Object.freeze({origin,controller});
  }
 });
}
