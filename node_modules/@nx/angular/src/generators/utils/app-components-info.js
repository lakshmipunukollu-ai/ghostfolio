"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getAppComponentInfo = getAppComponentInfo;
exports.getNxWelcomeComponentInfo = getNxWelcomeComponentInfo;
const devkit_1 = require("@nx/devkit");
const ts_solution_setup_1 = require("@nx/js/src/utils/typescript/ts-solution-setup");
const node_path_1 = require("node:path");
const version_utils_1 = require("./version-utils");
function getAppComponentInfo(tree, componentFileSuffix, project) {
    return getComponentInfo(tree, 'app', componentFileSuffix, project);
}
function getNxWelcomeComponentInfo(tree, componentFileSuffix, project) {
    return getComponentInfo(tree, 'nx-welcome', componentFileSuffix, project);
}
// TODO(leo): follow this up and improve it by using static analysis
function getComponentInfo(tree, component, componentFileSuffix, project) {
    const sourceRoot = (0, ts_solution_setup_1.getProjectSourceRoot)(project, tree);
    let componentPath = (0, devkit_1.joinPathFragments)(sourceRoot, `app/${component}.component.ts`);
    if (!tree.exists(componentPath)) {
        componentPath = (0, devkit_1.joinPathFragments)(sourceRoot, `app/${component}.ts`);
    }
    if (!tree.exists(componentPath)) {
        if (componentFileSuffix) {
            componentPath = (0, devkit_1.joinPathFragments)(sourceRoot, `app/${component}${componentFileSuffix}.ts`);
        }
    }
    if (!tree.exists(componentPath)) {
        const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
        componentPath = (0, devkit_1.joinPathFragments)(sourceRoot, angularMajorVersion >= 20
            ? `app/${component}.ts`
            : `app/${component}.component.ts`);
    }
    const fileName = (0, node_path_1.basename)(componentPath);
    const extensionlessFileName = fileName.slice(0, -3);
    return {
        fileName,
        extensionlessFileName,
        path: componentPath,
        symbolName: (0, devkit_1.names)(extensionlessFileName).className,
    };
}
