"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateOptions = validateOptions;
const devkit_1 = require("@nx/devkit");
const validations_1 = require("../../utils/validations");
const version_utils_1 = require("../../utils/version-utils");
function validateOptions(tree, options) {
    validateProject(tree, options.project);
    validateBuildTarget(tree, options.project);
    const { major: angularMajorVersion, version: angularVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
    if (angularMajorVersion !== 19 && options.serverRouting !== undefined) {
        throw new Error(`The "serverRouting" option is only supported in Angular versions 19.x.x. You are using Angular ${angularVersion}.`);
    }
    if (options.serverRouting) {
        const { targets } = (0, devkit_1.readProjectConfiguration)(tree, options.project);
        const isUsingApplicationBuilder = targets.build.executor === '@angular-devkit/build-angular:application' ||
            targets.build.executor === '@angular/build:application' ||
            targets.build.executor === '@nx/angular:application';
        if (!isUsingApplicationBuilder) {
            throw new Error('Server routing APIs can only be added to a project using the "application" builder.');
        }
    }
}
function validateProject(tree, project) {
    (0, validations_1.validateProject)(tree, project);
    const { projectType } = (0, devkit_1.readProjectConfiguration)(tree, project);
    if (projectType !== 'application') {
        throw new Error(`The "${project}" project is not an application. Only application projects are supported by the "setup-ssr" generator.`);
    }
}
function validateBuildTarget(tree, project) {
    const { targets } = (0, devkit_1.readProjectConfiguration)(tree, project);
    if (!targets?.build) {
        throw new Error(`The "${project}" project does not have a "build" target. Please add a "build" target.`);
    }
}
