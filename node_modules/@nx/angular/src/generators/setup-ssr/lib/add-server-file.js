"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.addServerFile = addServerFile;
const devkit_1 = require("@nx/devkit");
const ts_solution_setup_1 = require("@nx/js/src/utils/typescript/ts-solution-setup");
const path_1 = require("path");
const zoneless_1 = require("../../../utils/zoneless");
const version_utils_1 = require("../../utils/version-utils");
const constants_1 = require("./constants");
function addServerFile(tree, options) {
    const project = (0, devkit_1.readProjectConfiguration)(tree, options.project);
    const { outputPath } = project.targets.build.options;
    const browserDistDirectory = options.isUsingApplicationBuilder
        ? getApplicationBuilderBrowserOutputPath(outputPath)
        : outputPath;
    const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
    const baseFilesPath = (0, path_1.join)(__dirname, '..', 'files');
    let pathToFiles;
    if (angularMajorVersion >= 20) {
        pathToFiles = (0, path_1.join)(baseFilesPath, 'v20+', options.isUsingApplicationBuilder
            ? 'application-builder'
            : 'server-builder', 'server');
    }
    else {
        pathToFiles = (0, path_1.join)(baseFilesPath, 'v19', options.isUsingApplicationBuilder
            ? 'application-builder' +
                (options.serverRouting ? '' : '-common-engine')
            : 'server-builder', 'server');
    }
    const sourceRoot = (0, ts_solution_setup_1.getProjectSourceRoot)(project, tree);
    const zoneless = (0, zoneless_1.isZonelessApp)(project);
    (0, devkit_1.generateFiles)(tree, pathToFiles, sourceRoot, {
        ...options,
        browserDistDirectory,
        zoneless,
        useDefaultImport: angularMajorVersion >= 21,
        angularMajorVersion,
        tpl: '',
    });
}
function getApplicationBuilderBrowserOutputPath(outputPath) {
    if (outputPath) {
        if (typeof outputPath === 'string') {
            // when `outputPath` is a string, it's the base path, so we return the default browser path
            return constants_1.DEFAULT_BROWSER_DIR;
        }
        return outputPath.browser ?? constants_1.DEFAULT_BROWSER_DIR;
    }
    return constants_1.DEFAULT_BROWSER_DIR;
}
