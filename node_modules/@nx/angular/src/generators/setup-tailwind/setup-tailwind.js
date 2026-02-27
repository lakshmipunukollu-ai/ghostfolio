"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupTailwindGenerator = setupTailwindGenerator;
const devkit_1 = require("@nx/devkit");
const lib_1 = require("./lib");
async function setupTailwindGenerator(tree, rawOptions) {
    devkit_1.logger.warn(`The 'setup-tailwind' generator is deprecated. Generating Tailwind configuration is no longer maintained. This generator will be removed in Nx 23.`);
    const options = (0, lib_1.normalizeOptions)(rawOptions);
    const project = (0, devkit_1.readProjectConfiguration)(tree, options.project);
    if (rawOptions.buildTarget && !project.targets?.[rawOptions.buildTarget]) {
        throw new Error(`The provided target "${options.buildTarget}" was not found for project "${options.project}". Please provide a valid build target.`);
    }
    const tailwindInstalledVersion = (0, lib_1.detectTailwindInstalledVersion)(tree);
    let installTask = () => { };
    if (!options.skipPackageJson) {
        if (tailwindInstalledVersion === undefined) {
            installTask = (0, lib_1.addTailwindRequiredPackages)(tree);
        }
    }
    (0, lib_1.addTailwindConfig)(tree, options, project, tailwindInstalledVersion ?? '3');
    if (project.projectType === 'application') {
        (0, lib_1.updateApplicationStyles)(tree, options, project);
    }
    else if (project.projectType === 'library') {
        (0, lib_1.validateBuildTarget)(options, project);
    }
    if (!options.skipFormat) {
        await (0, devkit_1.formatFiles)(tree);
    }
    return installTask;
}
exports.default = setupTailwindGenerator;
