"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getComponentType = getComponentType;
exports.getModuleTypeSeparator = getModuleTypeSeparator;
const devkit_1 = require("@nx/devkit");
const version_utils_1 = require("./version-utils");
function getComponentType(tree) {
    const nxJson = (0, devkit_1.readNxJson)(tree);
    let componentType = nxJson.generators?.['@nx/angular:component']?.type ??
        nxJson.generators?.['@nx/angular']?.component?.type;
    if (!componentType) {
        const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
        if (angularMajorVersion < 20) {
            componentType = 'component';
        }
    }
    return componentType;
}
function getModuleTypeSeparator(tree) {
    const nxJson = (0, devkit_1.readNxJson)(tree);
    // We don't have a "module" generator but the @nx/angular collection extends
    // from the @schematics/angular collection so the "module" generator is
    // available there. We check for a generator default for each collection.
    let typeSeparator = nxJson.generators?.['@nx/angular:module']?.typeSeparator ??
        nxJson.generators?.['@nx/angular']?.module?.typeSeparator ??
        nxJson.generators?.['@schematics/angular:module']?.typeSeparator ??
        nxJson.generators?.['@schematics/angular']?.module?.typeSeparator;
    if (!typeSeparator) {
        const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
        typeSeparator = angularMajorVersion >= 20 ? '-' : '.';
    }
    return typeSeparator;
}
