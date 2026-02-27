import { type Tree } from '@nx/devkit';
import { type PackageCompatVersions, type SupportedVersion, supportedVersions, type VersionMap } from '../../utils/backward-compatible-versions';
export declare function getInstalledAngularDevkitVersion(tree: Tree): string | null;
export declare function getInstalledAngularVersion(tree: Tree): string;
export declare function getInstalledAngularMajorVersion(tree: Tree): number;
export declare function getInstalledAngularVersionInfo(tree: Tree): {
    version: string;
    major: number;
};
export declare function getInstalledPackageVersionInfo(tree: Tree, pkgName: string): {
    major: number;
    version: string;
};
export declare function versions(tree: Tree): PackageCompatVersions;
export declare function versions<V extends SupportedVersion>(tree: Tree, options: {
    minAngularMajorVersion: V;
}): MinVersionReturnType<V>;
/**
 * Temporary helper to abstract away the version of angular-rspack to be installed
 * until we stop supporting Angular 19.
 */
export declare function getAngularRspackVersion(tree: Tree): string;
type TakeUntil<Arr extends readonly any[], Target> = Arr extends readonly [
    infer Head,
    ...infer Rest
] ? Head extends Target ? [Head] : [Head, ...TakeUntil<Rest, Target>] : [];
type VersionsAtLeast<MinV extends SupportedVersion> = Extract<SupportedVersion, TakeUntil<typeof supportedVersions, MinV>[number]>;
type MinVersionReturnType<MinV extends SupportedVersion> = VersionMap[VersionsAtLeast<MinV>];
export {};
//# sourceMappingURL=version-utils.d.ts.map