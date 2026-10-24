import {expect,it} from 'vitest';
import cases from '../test/fixtures/model-routing.json';
import {catalogueId,movingAlias} from './modelRouting';
it.each(cases)('FR-P-04 metadata lookup $provider $id',item=>expect(catalogueId(item.provider,item.id)).toBe(item.catalog_id));
it('FR-UI-01 aliases are recognised beneath routing suffixes',()=>{expect(movingAlias('~moving:nitro')).toBe(true);expect(movingAlias('vendor/model-latest:floor')).toBe(true);expect(movingAlias('vendor/model-20261024')).toBe(false);});
