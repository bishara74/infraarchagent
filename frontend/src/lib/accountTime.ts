export function accountTime(value:string|null|undefined,empty='Never') {
 if(!value)return empty;
 const timestamp=new Date(value);
 return Number.isNaN(timestamp.getTime())?'Unavailable':timestamp.toLocaleString();
}
