import type {PackageResult} from '../api/types';
export function ProfileAssessments({item}:{item:PackageResult}) {
 const views=item.profile_assessments;
 if(!views)return <p className="muted">Profile assessments unavailable.</p>;
 return <div><p>Strict: {views.strict.remaining_blocking} blocking</p><p className="muted">Experimental — contextual-v1: {views['contextual-v1'].remaining_blocking} blocking · contextual-v2: {views['contextual-v2'] ? `${views['contextual-v2'].remaining_blocking} blocking` : 'unavailable'}</p><p className="muted">Contextual assessment is experimental. Strict checks control the official label.</p></div>;
}
