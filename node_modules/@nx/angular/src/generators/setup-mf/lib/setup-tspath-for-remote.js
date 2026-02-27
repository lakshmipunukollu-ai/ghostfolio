"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupTspathForRemote = setupTspathForRemote;
const devkit_1 = require("@nx/devkit");
const js_1 = require("@nx/js");
const module_federation_1 = require("@nx/module-federation");
function setupTspathForRemote(tree, options) {
    const project = (0, devkit_1.readProjectConfiguration)(tree, options.appName);
    const exportPath = options.standalone
        ? `./src/app/remote-entry/entry.routes.ts`
        : `./src/app/remote-entry/${options.entryModuleFileName}.ts`;
    const exportName = options.standalone ? 'Routes' : 'Module';
    (0, js_1.addTsConfigPath)(tree, `${(0, module_federation_1.normalizeProjectName)(options.appName)}/${exportName}`, [(0, devkit_1.joinPathFragments)(project.root, exportPath)]);
}
