import { AssetGlobPattern, FileReplacement, NormalizedNxAppRspackPluginOptions, NxAppRspackPluginOptions } from '../models';
export declare function normalizeOptions(options: NxAppRspackPluginOptions): NormalizedNxAppRspackPluginOptions;
export declare function normalizeAssets(assets: any[], root: string, sourceRoot: string, projectRoot: string, resolveRelativePathsToProjectRoot?: boolean): AssetGlobPattern[];
export declare function normalizeFileReplacements(root: string, fileReplacements: FileReplacement[]): FileReplacement[];
//# sourceMappingURL=normalize-options.d.ts.map