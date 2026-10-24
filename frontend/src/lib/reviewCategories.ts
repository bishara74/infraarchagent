import type {ReviewCategory} from '../api/types';
export const reviewCategories:Record<ReviewCategory,string>={requirements_not_met:'requirements not met',too_expensive:'too expensive',organisational_policy:'organisational policy',security_concern:'security concern',operability:'operability',too_complex:'too complex',other:'other'};
export function categoryLabel(value:string|null|undefined){return value&&value in reviewCategories?reviewCategories[value as ReviewCategory]:'not recorded';}
