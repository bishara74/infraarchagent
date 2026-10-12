// app/domain/input_rules.py: count trimmed Unicode code points, not UTF-16 units.
export const MIN_INPUT=10; export const MAX_INPUT=2000;
export const inputLength=(value:string)=>Array.from(value.trim()).length;
