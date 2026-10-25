import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import {manifest} from '../test/fixtures/lessons';
import {LessonUsage} from './LessonUsage';

it('FR-UI-02 states no lesson use for an unconfigured run',()=>{
  render(<LessonUsage/>);expect(screen.getByTestId('lesson-usage')).toHaveTextContent('Lessons used: none');
});
it('NFR-01 shows exact set use and self-approval provenance without hiding prior use',()=>{
  render(<LessonUsage manifest={{...manifest,self_approved:true,disabled_during_run:true}}/>);
  expect(screen.getByTestId('lesson-usage')).toHaveTextContent('Lessons used: set v1 (1 lesson)');
  expect(screen.getByText(/Includes self-approved lessons/)).toBeVisible();
  expect(screen.getByText(/Earlier use remains recorded/)).toBeVisible();
});
