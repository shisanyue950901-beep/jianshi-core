#!/usr/bin/env node
// G2-H.7I cloud inventory CLI. Default intentionally makes ZERO remote calls.
// Never pass tokens/identifiers on command line. No CI remote Cloudflare access.
// With --remote-read-only explicitly approved, token/account/zone come from
// restricted process env only, and the log stays anonymized.
import {inspectCloudflareReadOnly,summarizeReadOnlyOutcome}
 from './g2h7i_cloudflare_readonly_client.mjs';

const mask=Object.freeze({
 status:'NOT_CONNECTED',
 remoteCloudflareChecked:false,
 workerInventory:'NOT_VERIFIED',
 routeCoverage:'NOT_VERIFIED',
 accountsModified:0,
 routesModified:0,
 workerDeployments:0,
 authEnabled:false,
 safeToDeploy:false
});
const args=process.argv.slice(2);
if(args.length===0){
 console.log('G2H7I_REMOTE_INVENTORY_NOT_CONNECTED '+JSON.stringify(mask));
}else if(args.length===1&&args[0]==='--remote-read-only'){
 if(process.env.JIANSHI_H7I_REMOTE_READONLY_APPROVED!=='1'){
  console.error('G2H7I_REMOTE_READONLY_DENIED');
  process.exitCode=2;
 }else{
  try{
   const report=await inspectCloudflareReadOnly({
    accountId:process.env.JIANSHI_H7I_ACCOUNT_ID,
    zoneId:process.env.JIANSHI_H7I_ZONE_ID||undefined,
    token:process.env.JIANSHI_H7I_READ_TOKEN,
    mode:'EXPLICIT_REMOTE_READONLY',fetchImpl:globalThis.fetch
   });
   console.log('G2H7I_REMOTE_READONLY_INVENTORY_COMPLETED '+
    JSON.stringify(summarizeReadOnlyOutcome(report)));
  }catch(error){
   // No account ID, token, endpoint, API response or error body is printed.
   const codes=new Set([
    'CMS_H7I_ACCOUNT_ID_INVALID','CMS_H7I_ZONE_ID_INVALID',
    'CMS_H7I_TOKEN_ENV_REQUIRED','CMS_H7I_CLOUDFLARE_API_REJECTED',
    'CMS_H7I_WORKERS_COVERAGE_INCOMPLETE',
    'CMS_H7I_PAGES_COVERAGE_INCOMPLETE',
    'CMS_H7I_ROUTES_COVERAGE_INCOMPLETE',
    'CMS_H7I_HTTP_DENIED','CMS_H7I_NETWORK_UNAVAILABLE'
   ]);
   console.error('G2H7I_REMOTE_READONLY_FAIL_CLOSED '+
    (codes.has(error?.code)?error.code:'CMS_H7I_UNTRUSTED_REMOTE_FAILURE'));
   process.exitCode=1;
  }
 }
}else{
 console.error('G2H7I_UNSUPPORTED_ARGUMENTS');
 process.exitCode=2;
}
