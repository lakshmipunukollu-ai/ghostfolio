"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateOptions = validateOptions;
const semver_1 = require("semver");
const angular_version_utils_1 = require("../../utilities/angular-version-utils");
function validateOptions(options) {
    const { version: angularVersion } = (0, angular_version_utils_1.getInstalledAngularVersionInfo)();
    if ((0, semver_1.lt)(angularVersion, '20.0.0')) {
        if (options.i18nDuplicateTranslation) {
            throw new Error(`The "i18nDuplicateTranslation" option requires Angular version 20.0.0 or greater. You are currently using version ${angularVersion}.`);
        }
    }
}
