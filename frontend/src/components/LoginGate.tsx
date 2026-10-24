import {Navigate, useLocation} from 'react-router';
import {Authentication} from './Authentication';

function deepLink(path: string) {
 return /^\/(?:recent|settings\/[a-z-]+|runs\/[^/?#]+(?:\/compare|\/packages\/(?:cost|performance|security))?)(?:[?#]|$)/.test(path);
}

/** A return target belongs to one signed-out navigation, never to preferences. */
export function LoginGate({authenticated=false,setup=false,allowLocal=false,onLocal}:{authenticated?:boolean;setup?:boolean;allowLocal?:boolean;onLocal?:()=>void}) {
 const location=useLocation();
 if(authenticated){
  const target=(location.state as {returnTo?:unknown}|null)?.returnTo;
  return <Navigate replace to={typeof target==='string'&&deepLink(target)?target:'/'} state={null}/>;
 }
 if(location.pathname!=='/login'){
  const target=location.pathname+location.search+location.hash;
  return <Navigate replace to="/login" state={deepLink(target)?{returnTo:target}:null}/>;
 }
 return <><Authentication setup={setup} onSaved={()=>undefined}/>{allowLocal&&<button onClick={onLocal}>Continue in local mode</button>}</>;
}
