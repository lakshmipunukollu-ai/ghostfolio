import * as latestVersions from './versions';
export declare const supportedVersions: readonly [21, 20, 19];
export type SupportedVersion = (typeof supportedVersions)[number];
export type PackageVersionNames = Exclude<keyof typeof latestVersions, 'nxVersion'>;
export type VersionMap = {
    21: Record<PackageVersionNames, string>;
    20: Record<PackageVersionNames, string>;
    19: Record<PackageVersionNames | 'angularRspackVersion', string>;
};
export type PackageCompatVersions = VersionMap[SupportedVersion];
export declare const backwardCompatibleVersions: VersionMap;
//# sourceMappingURL=backward-compatible-versions.d.ts.map