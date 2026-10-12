// G2-H.7G: throwaway localhost mTLS proxy for GitHub PostgreSQL E2E.
// Node-only test fixture; NOT a Cloudflare Worker / CDN / public service.
// Certificate private keys exist only in GitHub runner temp and are destroyed.
import https from 'node:https';
import {X509Certificate} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const KEY='SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET';
const REQUIRED='SYNTHETIC_H7G_MTLS_ONLY';
const ENDPOINT='https://h7g-state.example.invalid/v1/email-state';
function check(v,why){if(!v)throw Error('CMS_H7G_HARNESS_'+why);}
function openssl(args,dir){
 execFileSync('openssl',args,{cwd:dir,stdio:'ignore',timeout:25000});
}
function read(dir,f){return readFileSync(path.join(dir,f),'utf8');}
function makeCa(dir,name){
 openssl(['req','-x509','-newkey','rsa:2048','-nodes','-sha256','-days','1',
  '-keyout',name+'.key','-out',name+'.crt','-subj',
  '/CN=SYNTHETIC_H7G_'+name,
  '-addext','basicConstraints=critical,CA:TRUE',
  '-addext','keyUsage=critical,keyCertSign,cRLSign'],dir);
 return {key:read(dir,name+'.key'),cert:read(dir,name+'.crt'),
  name};
}
function signed(dir,ca,label,cn,server=false){
 openssl(['req','-new','-newkey','rsa:2048','-nodes',
  '-keyout',label+'.key','-out',label+'.csr','-subj','/CN='+cn],dir);
 const ext=label+'.ext';
 writeFileSync(path.join(dir,ext),server?
  'subjectAltName=DNS:localhost\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n':
  'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature\n');
 openssl(['x509','-req','-in',label+'.csr','-CA',ca.name+'.crt',
  '-CAkey',ca.name+'.key','-CAcreateserial',
  '-out',label+'.crt','-days','1','-sha256','-extfile',ext],dir);
 const cert=read(dir,label+'.crt');
 return {key:read(dir,label+'.key'),cert,
  fingerprint:new X509Certificate(cert).fingerprint256};
}
function emit(res,status,obj){
 const body=JSON.stringify(obj);
 res.writeHead(status,{
  'content-type':'application/json','cache-control':'no-store',
  'x-content-type-options':'nosniff','content-length':Buffer.byteLength(body),
  'connection':'close'
 });
 res.end(body);
}
// Only response shape is ever forwarded; service token is injected here, never
// accepted from caller, never passed through Cloudflare test binding.
export async function launchSyntheticMtlsProxy({upstreamUrl}={}){
 check(process.env.JIANSHI_G2F_EPHEMERAL_ONLY==='1' &&
  process.env.JIANSHI_G2H7G_MTLS_ONLY==='1','DISPOSABLE_ONLY');
 check(typeof upstreamUrl==='string'&&
  /^http:\/\/127\.0\.0\.1:[1-9][0-9]{0,4}\/v1\/email-state$/.test(upstreamUrl),
  'LOCAL_UPSTREAM_REQUIRED');
 for(const variable of ['DATABASE_URL','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY',
  'SUPABASE_SECRET_KEY','CLOUDFLARE_API_TOKEN'])
  check(!process.env[variable],'REMOTE_CREDENTIALS_DENIED');
 const dir=mkdtempSync(path.join(os.tmpdir(),'jianshi-h7g-mtls-'));
 let server;
 try{
  const serverCa=makeCa(dir,'SERVER_CA');
  const clientCa=makeCa(dir,'CLIENT_CA');
  const foreignCa=makeCa(dir,'FOREIGN_CA');
  const serverCert=signed(dir,serverCa,'server','localhost',true);
  const a=signed(dir,clientCa,'a','SYNTHETIC_H7G_WORKER_A');
  const b=signed(dir,clientCa,'b','SYNTHETIC_H7G_WORKER_B');
  const c=signed(dir,clientCa,'c','SYNTHETIC_H7G_REVOKED_OR_UNKNOWN');
  const foreign=signed(dir,foreignCa,'foreign','SYNTHETIC_H7G_FOREIGN');
  const allowed=new Set([a.fingerprint,b.fingerprint]);
  const metrics={accepted:0,rejected:0,forwarded:0};
  server=https.createServer({
   key:serverCert.key,cert:serverCert.cert,ca:clientCa.cert,
   requestCert:true,rejectUnauthorized:true,
   minVersion:'TLSv1.3',maxVersion:'TLSv1.3',
   honorCipherOrder:true
  },async(req,res)=>{
   try{
    const port=server.address().port;
    const peer=req.socket.getPeerCertificate();
    if(req.socket.encrypted!==true||req.socket.authorized!==true||
     req.socket.getProtocol()!=='TLSv1.3'||
     req.socket.remoteAddress!=='127.0.0.1'||
     !allowed.has(peer?.fingerprint256)||
     req.headers.host!=='localhost:'+port||
     req.headers['x-forwarded-host']||req.headers['x-forwarded-proto']||
     req.method!=='POST'||req.url!=='/v1/email-state'||
     req.headers['x-jianshi-test-boundary']!==REQUIRED||
     req.headers['content-type']!=='application/json'||
     req.headers.authorization||req.headers.cookie||
     !/^[1-9][0-9]{0,2}$/.test(req.headers['content-length']||'')||
     Number(req.headers['content-length'])>512){
      metrics.rejected++;return emit(res,403,{error:'DENIED'});
    }
    let size=0,buffers=[];
    for await(const chunk of req){
     size+=chunk.length;if(size>512)throw Error('BODY_LIMIT');
     buffers.push(chunk);
    }
    const raw=Buffer.concat(buffers).toString('utf8');
    const data=JSON.parse(raw);
    if(data===null||Array.isArray(data)||typeof data!=='object'||
     !['issue','consume'].includes(data.action)||
     !/^[a-f0-9]{64}$/.test(data.stateDigest||'')||
     !/^[a-f0-9]{64}$/.test(data.cookieDigest||'')||
     ![3,4].includes(Object.keys(data).length)){
     metrics.rejected++;return emit(res,403,{error:'DENIED'});
    }
    const shape=data.action==='issue'?
     'action,cookieDigest,expiresAt,stateDigest':
     'action,cookieDigest,stateDigest';
    if(Object.keys(data).sort().join(',')!==shape){
     metrics.rejected++;return emit(res,403,{error:'DENIED'});
    }
    const upstream=await fetch(upstreamUrl,{
     method:'POST',redirect:'error',cache:'no-store',signal:AbortSignal.timeout(9000),
     headers:{authorization:'Bearer '+KEY,
      'x-jianshi-test-boundary':'SYNTHETIC_H7F_ONLY',
      'content-type':'application/json'},
     body:raw
    });
    if(upstream.status!==200){
     metrics.rejected++;return emit(res,403,{error:'DENIED'});
    }
    const upstreamBody=await upstream.text();
    if(upstreamBody.length>128)throw Error('RESPONSE_TOO_LARGE');
    const output=JSON.parse(upstreamBody);
    if((data.action==='issue'&&
       (Object.keys(output).join(',')!=='issued'||output.issued!==true))||
      (data.action==='consume'&&
       (Object.keys(output).join(',')!=='used'||typeof output.used!=='boolean')))
     throw Error('UPSTREAM_SHAPE');
    metrics.accepted++;metrics.forwarded++;
    return emit(res,200,output);
   }catch{
    metrics.rejected++;return emit(res,403,{error:'DENIED'});
   }
  });
  await new Promise((resolve,reject)=>{
   server.once('error',reject);
   server.listen(0,'127.0.0.1',()=>{
    server.off('error',reject);resolve();
   });
  });
  const port=server.address().port;
  return Object.freeze({
   origin:'https://localhost:'+port,server,metrics,
   certificates:{serverCa:serverCa.cert,clientCa:clientCa.cert,
    a,b,c,foreign},
   revokeA(){allowed.delete(a.fingerprint);},
   revokeB(){allowed.delete(b.fingerprint);},
   allowB(){allowed.add(b.fingerprint);},
   async close(){
    await new Promise((resolve,reject)=>
     server.close(err=>err?reject(err):resolve()));
    rmSync(dir,{recursive:true,force:true});
   }
  });
 }catch(error){
  if(server?.listening)await new Promise(r=>server.close(r));
  rmSync(dir,{recursive:true,force:true});throw error;
 }
}
// A synthetic mTLS binding shim, not a claim of real Cloudflare execution.
// Cert material never enters the worker module: here Node's TLS client
// presents it below Fetch API and verifies the server CA and DNS SAN.
export function syntheticMtlsBinding({proxy,certificate,trust}={}){
 const ca=trust||proxy.certificates.serverCa;
 return Object.freeze({
  synthetic:true,
  async fetch(url,init){
   check(url===ENDPOINT,'UNROUTABLE_DEST_ONLY');
   check(init?.method==='POST'&&init.redirect==='error'&&
    init.headers?.['x-jianshi-test-boundary']===REQUIRED,'STRICT_FETCH_CONTRACT');
   const origin=new URL(proxy.origin);
   return new Promise((resolve,reject)=>{
    const req=https.request({
     hostname:'127.0.0.1',port:Number(origin.port),
     servername:'localhost',
     method:init.method,path:'/v1/email-state',host:'localhost',
     key:certificate?.key,cert:certificate?.cert,ca,
     rejectUnauthorized:true,minVersion:'TLSv1.3',
     maxVersion:'TLSv1.3',
     timeout:10000,
     headers:{
      host:'localhost:'+origin.port,
      'content-type':'application/json',
      'x-jianshi-test-boundary':REQUIRED,
      'content-length':Buffer.byteLength(init.body)
     }
    },response=>{
     const parts=[];let size=0;
     response.on('data',chunk=>{
      size+=chunk.length;
      if(size>256){req.destroy(Error('RESPONSE_LIMIT'));return;}
      parts.push(chunk);
     });
     response.on('end',()=>resolve(new Response(
      Buffer.concat(parts),{
       status:response.statusCode,
       headers:{'content-type':response.headers['content-type']||'text/plain'}
      }
     )));
    });
    req.on('error',reject);
    req.on('timeout',()=>req.destroy(Error('SYNTHETIC_TIMEOUT')));
    req.end(init.body);
   });
  }
 });
}
