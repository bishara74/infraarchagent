import type { ReviewReason } from '../api/types';
const messages:Record<ReviewReason,string>={unresolved_security_findings:'Blocking security findings remain unresolved.',validation_failed:'Validation checks failed. Review the report before deciding.',validation_error:'Validation could not finish. Review the tool report.',retry_aborted:'The previous retry was interrupted. Review the retained results.'};
export const reviewReason=(reason:ReviewReason)=>messages[reason];
