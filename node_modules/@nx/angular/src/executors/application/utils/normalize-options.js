"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.normalizeOptions = normalizeOptions;
const angular_version_utils_1 = require("../../utilities/angular-version-utils");
function normalizeOptions(options) {
    const { major: angularMajorVersion } = (0, angular_version_utils_1.getInstalledAngularVersionInfo)();
    let sourceMap = options.sourceMap;
    if (sourceMap &&
        typeof sourceMap === 'object' &&
        sourceMap.sourcesContent !== undefined &&
        angularMajorVersion < 20) {
        delete sourceMap.sourcesContent;
    }
    return { ...options, sourceMap };
}
