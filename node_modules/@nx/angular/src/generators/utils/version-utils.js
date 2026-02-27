"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getInstalledAngularDevkitVersion = getInstalledAngularDevkitVersion;
exports.getInstalledAngularVersion = getInstalledAngularVersion;
exports.getInstalledAngularMajorVersion = getInstalledAngularMajorVersion;
exports.getInstalledAngularVersionInfo = getInstalledAngularVersionInfo;
exports.getInstalledPackageVersionInfo = getInstalledPackageVersionInfo;
exports.versions = versions;
exports.getAngularRspackVersion = getAngularRspackVersion;
const tslib_1 = require("tslib");
const devkit_1 = require("@nx/devkit");
const semver_1 = require("semver");
const backward_compatible_versions_1 = require("../../utils/backward-compatible-versions");
const latestVersions = tslib_1.__importStar(require("../../utils/versions"));
const versions_1 = require("../../utils/versions");
function getInstalledAngularDevkitVersion(tree) {
    return ((0, devkit_1.getDependencyVersionFromPackageJson)(tree, '@angular-devkit/build-angular') ?? (0, devkit_1.getDependencyVersionFromPackageJson)(tree, '@angular/build'));
}
function getInstalledAngularVersion(tree) {
    const installedAngularVersion = (0, devkit_1.getDependencyVersionFromPackageJson)(tree, '@angular/core');
    if (!installedAngularVersion ||
        installedAngularVersion === 'latest' ||
        installedAngularVersion === 'next') {
        return (0, semver_1.clean)(versions_1.angularVersion) ?? (0, semver_1.coerce)(versions_1.angularVersion).version;
    }
    return ((0, semver_1.clean)(installedAngularVersion) ?? (0, semver_1.coerce)(installedAngularVersion).version);
}
function getInstalledAngularMajorVersion(tree) {
    return (0, semver_1.major)(getInstalledAngularVersion(tree));
}
function getInstalledAngularVersionInfo(tree) {
    const installedVersion = getInstalledAngularVersion(tree);
    return {
        version: installedVersion,
        major: (0, semver_1.major)(installedVersion),
    };
}
function getInstalledPackageVersionInfo(tree, pkgName) {
    const version = (0, devkit_1.getDependencyVersionFromPackageJson)(tree, pkgName);
    return version ? { major: (0, semver_1.major)((0, semver_1.coerce)(version)), version } : null;
}
function versions(tree, options) {
    const majorAngularVersion = getInstalledAngularMajorVersion(tree);
    if (options?.minAngularMajorVersion &&
        majorAngularVersion < options.minAngularMajorVersion) {
        throw new Error(`This operation requires Angular ${options.minAngularMajorVersion}+, but found version ${majorAngularVersion}. ` +
            `This shouldn't happen. Please report it as a bug and include the stack trace.`);
    }
    return backward_compatible_versions_1.backwardCompatibleVersions[majorAngularVersion] ?? latestVersions;
}
/**
 * Temporary helper to abstract away the version of angular-rspack to be installed
 * until we stop supporting Angular 19.
 */
function getAngularRspackVersion(tree) {
    const majorAngularVersion = getInstalledAngularMajorVersion(tree);
    // Starting with Angular 20, we can use an Angular Rspack version that is
    // aligned with the Nx version
    return majorAngularVersion === 19
        ? backward_compatible_versions_1.backwardCompatibleVersions[19].angularRspackVersion
        : latestVersions.nxVersion;
}
