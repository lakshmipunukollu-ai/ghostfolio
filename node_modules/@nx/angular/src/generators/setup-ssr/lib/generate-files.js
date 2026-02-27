"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateSSRFiles = generateSSRFiles;
const devkit_1 = require("@nx/devkit");
const ts_solution_setup_1 = require("@nx/js/src/utils/typescript/ts-solution-setup");
const path_1 = require("path");
const semver_1 = require("semver");
const app_components_info_1 = require("../../utils/app-components-info");
const artifact_types_1 = require("../../utils/artifact-types");
const version_utils_1 = require("../../utils/version-utils");
function generateSSRFiles(tree, options) {
    const project = (0, devkit_1.readProjectConfiguration)(tree, options.project);
    if (project.targets.server ||
        (options.isUsingApplicationBuilder &&
            project.targets.build.options?.server !== undefined)) {
        // server has already been added
        return;
    }
    const { major: angularMajorVersion, version: angularVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
    const baseFilesPath = (0, path_1.join)(__dirname, '..', 'files');
    let pathToFiles;
    if (angularMajorVersion >= 20) {
        pathToFiles = (0, path_1.join)(baseFilesPath, 'v20+', options.isUsingApplicationBuilder
            ? 'application-builder'
            : 'server-builder', options.standalone ? 'standalone-src' : 'ngmodule-src');
    }
    else {
        pathToFiles = (0, path_1.join)(baseFilesPath, 'v19', options.isUsingApplicationBuilder
            ? 'application-builder'
            : 'server-builder', options.standalone ? 'standalone-src' : 'ngmodule-src');
    }
    const sourceRoot = (0, ts_solution_setup_1.getProjectSourceRoot)(project, tree);
    const ssrVersion = (0, devkit_1.getDependencyVersionFromPackageJson)(tree, '@angular/ssr');
    const cleanedSsrVersion = ssrVersion
        ? ((0, semver_1.clean)(ssrVersion) ?? (0, semver_1.coerce)(ssrVersion).version)
        : null;
    const componentType = (0, artifact_types_1.getComponentType)(tree);
    const appComponentInfo = (0, app_components_info_1.getAppComponentInfo)(tree, componentType ? `.${componentType}` : '', project);
    const moduleTypeSeparator = (0, artifact_types_1.getModuleTypeSeparator)(tree);
    const useBootstrapContext = 
    // https://github.com/angular/angular-cli/releases/tag/20.3.0
    (0, semver_1.gte)(angularVersion, '20.3.0') ||
        // https://github.com/angular/angular-cli/releases/tag/19.2.16
        (angularMajorVersion === 19 && (0, semver_1.gte)(angularVersion, '19.2.16'));
    (0, devkit_1.generateFiles)(tree, pathToFiles, sourceRoot, {
        ...options,
        provideServerRoutingFn: !cleanedSsrVersion || (0, semver_1.gte)(cleanedSsrVersion, '19.2.0')
            ? 'provideServerRouting'
            : 'provideServerRoutesConfig',
        appFileName: appComponentInfo.extensionlessFileName,
        appSymbolName: appComponentInfo.symbolName,
        moduleTypeSeparator,
        useBootstrapContext,
        tpl: '',
    });
    if (angularMajorVersion === 19 && !options.serverRouting) {
        tree.delete((0, devkit_1.joinPathFragments)(sourceRoot, 'app/app.routes.server.ts'));
    }
}
