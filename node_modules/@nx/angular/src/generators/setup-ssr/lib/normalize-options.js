"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.normalizeOptions = normalizeOptions;
const devkit_1 = require("@nx/devkit");
const prompt_1 = require("@nx/devkit/src/generators/prompt");
const ast_utils_1 = require("../../../utils/nx-devkit/ast-utils");
const version_utils_1 = require("../../utils/version-utils");
async function normalizeOptions(tree, options) {
    const { targets, root } = (0, devkit_1.readProjectConfiguration)(tree, options.project);
    const isUsingApplicationBuilder = targets.build.executor === '@angular-devkit/build-angular:application' ||
        targets.build.executor === '@angular/build:application' ||
        targets.build.executor === '@nx/angular:application';
    if (options.serverRouting === undefined && isUsingApplicationBuilder) {
        const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
        if (angularMajorVersion === 19) {
            options.serverRouting = await (0, prompt_1.promptWhenInteractive)({
                type: 'confirm',
                name: 'serverRouting',
                message: 'Would you like to use the Server Routing and App Engine APIs (Developer Preview) for this server application?',
                initial: false,
            }, { serverRouting: false }).then(({ serverRouting }) => serverRouting);
        }
        else {
            options.serverRouting = true;
        }
    }
    const isStandaloneApp = (0, ast_utils_1.isNgStandaloneApp)(tree, options.project);
    return {
        project: options.project,
        appId: options.appId ?? 'serverApp',
        main: options.main ?? 'main.server.ts',
        serverFileName: options.serverFileName ?? 'server.ts',
        serverPort: options.serverPort ?? 4000,
        rootModuleFileName: options.rootModuleFileName ?? 'app.server.module.ts',
        rootModuleClassName: options.rootModuleClassName ?? 'AppServerModule',
        skipFormat: options.skipFormat ?? false,
        standalone: options.standalone ?? isStandaloneApp,
        hydration: options.hydration ?? true,
        serverRouting: options.serverRouting,
        isUsingApplicationBuilder,
        buildTargetTsConfigPath: targets.build.options?.tsConfig ??
            (0, devkit_1.joinPathFragments)(root, 'tsconfig.app.json'),
    };
}
