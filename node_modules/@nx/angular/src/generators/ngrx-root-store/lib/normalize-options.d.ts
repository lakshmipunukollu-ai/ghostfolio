import type { Tree } from '@nx/devkit';
import type { Schema } from '../schema';
export type NormalizedNgRxRootStoreGeneratorOptions = Schema & {
    parent: string;
    rxjsVersion: string;
};
export declare function normalizeOptions(tree: Tree, options: Schema): NormalizedNgRxRootStoreGeneratorOptions;
//# sourceMappingURL=normalize-options.d.ts.map