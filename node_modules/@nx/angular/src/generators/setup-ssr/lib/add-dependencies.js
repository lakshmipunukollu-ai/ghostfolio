"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.addDependencies = addDependencies;
const devkit_1 = require("@nx/devkit");
const version_utils_1 = require("../../utils/version-utils");
function addDependencies(tree, isUsingApplicationBuilder) {
    const pkgVersions = (0, version_utils_1.versions)(tree);
    const dependencies = {
        '@angular/platform-server': (0, devkit_1.getDependencyVersionFromPackageJson)(tree, '@angular/platform-server') ??
            pkgVersions.angularVersion,
        express: pkgVersions.expressVersion,
    };
    const devDependencies = {
        '@types/express': pkgVersions.typesExpressVersion,
        '@types/node': pkgVersions.typesNodeVersion,
    };
    const angularDevkitVersion = (0, version_utils_1.getInstalledAngularDevkitVersion)(tree) ?? pkgVersions.angularDevkitVersion;
    dependencies['@angular/ssr'] = angularDevkitVersion;
    if (!isUsingApplicationBuilder) {
        devDependencies['browser-sync'] = pkgVersions.browserSyncVersion;
    }
    else {
        const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
        if (angularMajorVersion >= 20) {
            dependencies['@angular-devkit/build-angular'] = angularDevkitVersion;
        }
    }
    (0, devkit_1.addDependenciesToPackageJson)(tree, dependencies, devDependencies, undefined, true);
}
