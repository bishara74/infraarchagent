import type {ReviewCategory} from '../api/types';
export const rejectionCategories={requirements_not_met:'requirements not met',too_expensive:'too expensive',organisational_policy:'organisational policy',security_concern:'security concern',operability:'operability',too_complex:'too complex',other:'other'};
export const approvalCategories={meets_requirements:'meets requirements',accepted_risk:'accepted risk',approved_with_follow_ups:'approved with follow-ups',organisational_exception:'organisational exception',other:'other'};
export const reviewCategories:Record<ReviewCategory,string>={...rejectionCategories,...approvalCategories};
export function categoryLabel(value:string|null|undefined){return value&&value in reviewCategories?reviewCategories[value as ReviewCategory]:'not recorded';}
