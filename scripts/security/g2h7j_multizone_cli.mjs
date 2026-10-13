#!/usr/bin/env node
// G2-H.7J: no-network by default; explicitly requested Cloudflare GET-only
// scoped verification is possible only with a read-scoped environment token.
// No log of token/account ID/zone IDs/hostnames; no cloud mutation.
import {inspectMultiZoneReadOnly} from './g2h7j_multizone_readonly.mjs';
const argv=process.argv.slice(2);
if(argv.length===0){
 console.log('G2H7J_NOT_CONNECTED '+JSON.stringify({
  status:'NOT_CONNECTED',workerRead:false,zonesRead:false,
  customDomainsRead:false,safeToDeploy:false,
  cloudflareCalls:0
 }));
}else if(argv.length===1&&argv[0]==='--remote-read-only'){
 if(process.env.JIANSHI_H7J_REMOTE_READONLY_APPROVED!=='1'){
  console.error('G2H7J_REMOTE_READONLY_DENIED');
  process.exitCode=2;
 }else{
  try{
   const r=await inspectMultiZoneReadOnly({
    accountId:process.env.JIANSHI_H7J_ACCOUNT_ID,
    token:process.env.JIANSHI_H7J_READ_TOKEN,
    mode:'EXPLICIT_REMOTE_READONLY',
    fetchImpl:globalThis.fetch
   });
   // Explicit deny fields verified in output contract; no input, raw reply,
   // certificate metadata, hostname or Worker source enters console.
   console.log('G2H7J_READONLY_SCOPED_INVENTORY '+JSON.stringify(r));
  }catch(error){
   // Never show raw HTTP errors, API response, credential or path.
   console.error('G2H7J_CLOUD_READONLY_FAIL_CLOSED');
   process.exitCode=1;
  }
 }
}else{
 console.error('G2H7J_INVALID_ARGUMENTS');
 process.exitCode=2;
}
