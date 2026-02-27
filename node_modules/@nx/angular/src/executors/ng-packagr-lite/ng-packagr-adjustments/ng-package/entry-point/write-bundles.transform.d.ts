/**
 * Adapted from the original ng-packagr.
 *
 * Changes made:
 * - Removed bundling altogether.
 * - Write the ESM2022 outputs to the file system.
 * - Fake the FESM2022 outputs pointing them to the ESM2022 outputs.
 */
import type { NgPackagrOptions } from 'ng-packagr/src/lib/ng-package/options.di';
export declare const writeBundlesTransform: (_options: NgPackagrOptions) => import("ng-packagr/src/lib/graph/transform").Transform;
//# sourceMappingURL=write-bundles.transform.d.ts.map