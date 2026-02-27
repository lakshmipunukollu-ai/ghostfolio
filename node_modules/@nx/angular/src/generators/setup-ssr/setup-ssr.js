"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupSsr = setupSsr;
const devkit_1 = require("@nx/devkit");
const lib_1 = require("./lib");
async function setupSsr(tree, schema) {
    (0, lib_1.validateOptions)(tree, schema);
    const options = await (0, lib_1.normalizeOptions)(tree, schema);
    if (!schema.skipPackageJson) {
        (0, lib_1.addDependencies)(tree, options.isUsingApplicationBuilder);
    }
    (0, lib_1.generateSSRFiles)(tree, options);
    if (options.hydration) {
        (0, lib_1.addHydration)(tree, options);
    }
    if (!options.hydration) {
        (0, lib_1.setRouterInitialNavigation)(tree, options);
    }
    if (options.isUsingApplicationBuilder) {
        (0, lib_1.updateProjectConfigForApplicationBuilder)(tree, options);
        (0, lib_1.setServerTsConfigOptionsForApplicationBuilder)(tree, options);
    }
    else {
        (0, lib_1.updateProjectConfigForBrowserBuilder)(tree, options);
        (0, lib_1.generateTsConfigServerJsonForBrowserBuilder)(tree, options);
    }
    (0, lib_1.addServerFile)(tree, options);
    if (!options.skipFormat) {
        await (0, devkit_1.formatFiles)(tree);
    }
    return () => {
        (0, devkit_1.installPackagesTask)(tree);
    };
}
exports.default = setupSsr;
