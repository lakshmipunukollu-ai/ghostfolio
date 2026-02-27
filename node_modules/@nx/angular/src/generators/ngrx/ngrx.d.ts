import type { GeneratorCallback, Tree } from '@nx/devkit';
import type { NgRxGeneratorOptions } from './schema';
/**
 * @deprecated Use the 'ngrx-root-store' and 'ngrx-feature-store' generators instead. It will be removed in Nx v22.
 */
export declare function ngrxGenerator(tree: Tree, schema: NgRxGeneratorOptions): Promise<GeneratorCallback>;
export default ngrxGenerator;
//# sourceMappingURL=ngrx.d.ts.map