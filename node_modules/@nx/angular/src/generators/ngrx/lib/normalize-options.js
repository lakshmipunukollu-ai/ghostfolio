"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.normalizeOptions = normalizeOptions;
const devkit_1 = require("@nx/devkit");
const semver_1 = require("@nx/devkit/src/utils/semver");
const path_1 = require("path");
const semver_2 = require("semver");
const versions_1 = require("../../../utils/versions");
function normalizeOptions(tree, options) {
    let rxjsVersion;
    try {
        rxjsVersion = (0, semver_1.checkAndCleanWithSemver)(tree, 'rxjs', (0, devkit_1.readJson)(tree, 'package.json').dependencies['rxjs']);
    }
    catch {
        rxjsVersion = (0, semver_1.checkAndCleanWithSemver)(tree, 'rxjs', versions_1.rxjsVersion);
    }
    const rxjsMajorVersion = (0, semver_2.major)(rxjsVersion);
    return {
        ...options,
        parentDirectory: options.module
            ? (0, path_1.dirname)(options.module)
            : options.parent
                ? (0, path_1.dirname)(options.parent)
                : undefined,
        route: options.route === '' ? `''` : (options.route ?? `''`),
        directory: (0, devkit_1.names)(options.directory).fileName,
        rxjsVersion,
        rxjsMajorVersion,
    };
}
