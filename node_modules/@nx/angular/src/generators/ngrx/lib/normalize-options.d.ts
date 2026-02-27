import { Tree } from '@nx/devkit';
import type { NgRxGeneratorOptions } from '../schema';
export type NormalizedNgRxGeneratorOptions = NgRxGeneratorOptions & {
    parentDirectory: string;
    rxjsVersion: string;
    rxjsMajorVersion: number;
};
export declare function normalizeOptions(tree: Tree, options: NgRxGeneratorOptions): NormalizedNgRxGeneratorOptions;
//# sourceMappingURL=normalize-options.d.ts.map