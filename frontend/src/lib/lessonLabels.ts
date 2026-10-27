import type {LessonRole,LessonTag} from '../api/types';
export const lessonRoles:Record<LessonRole,string>={fixer:'Fixer',architect:'Architect',generator_cost:'Cost Generator',generator_performance:'Performance Generator',generator_security:'Security Generator',all_generators:'All Generators'};
export const lessonTags:LessonTag[]=['load_balancer','database','storage','network','kubernetes','cost','logging'];
