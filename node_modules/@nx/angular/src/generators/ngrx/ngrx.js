"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ngrxGenerator = ngrxGenerator;
const devkit_1 = require("@nx/devkit");
const lib_1 = require("./lib");
/**
 * @deprecated Use the 'ngrx-root-store' and 'ngrx-feature-store' generators instead. It will be removed in Nx v22.
 */
async function ngrxGenerator(tree, schema) {
    (0, lib_1.validateOptions)(tree, schema);
    const options = (0, lib_1.normalizeOptions)(tree, schema);
    if (!options.minimal || !options.root) {
        (0, lib_1.generateNgrxFilesFromTemplates)(tree, options);
    }
    if (!options.skipImport) {
        (0, lib_1.addImportsToModule)(tree, options);
        (0, lib_1.addExportsToBarrel)(tree, options);
    }
    let packageInstallationTask = () => { };
    if (!options.skipPackageJson) {
        packageInstallationTask = (0, lib_1.addNgRxToPackageJson)(tree, options);
    }
    if (!options.skipFormat) {
        await (0, devkit_1.formatFiles)(tree);
    }
    return packageInstallationTask;
}
exports.default = ngrxGenerator;
