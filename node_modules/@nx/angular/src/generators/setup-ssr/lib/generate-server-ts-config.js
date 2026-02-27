"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setServerTsConfigOptionsForApplicationBuilder = setServerTsConfigOptionsForApplicationBuilder;
exports.generateTsConfigServerJsonForBrowserBuilder = generateTsConfigServerJsonForBrowserBuilder;
const devkit_1 = require("@nx/devkit");
const ensure_typescript_1 = require("@nx/js/src/utils/typescript/ensure-typescript");
const path_1 = require("path");
const tsconfig_utils_1 = require("../../utils/tsconfig-utils");
const version_utils_1 = require("../../utils/version-utils");
function setServerTsConfigOptionsForApplicationBuilder(tree, options) {
    const { targets } = (0, devkit_1.readProjectConfiguration)(tree, options.project);
    const tsConfigPath = targets.build.options.tsConfig;
    (0, devkit_1.updateJson)(tree, tsConfigPath, (json) => {
        json.compilerOptions ??= {};
        const types = new Set(json.compilerOptions.types ?? []);
        types.add('node');
        json.compilerOptions.types = Array.from(types);
        if (json.include?.includes('src/**/*.ts')) {
            // server file is already included, no need to add it
            return json;
        }
        const files = new Set(json.files ?? []);
        files.add((0, devkit_1.joinPathFragments)('src', options.main));
        files.add((0, devkit_1.joinPathFragments)('src', options.serverFileName));
        json.files = Array.from(files);
        return json;
    });
}
function generateTsConfigServerJsonForBrowserBuilder(tree, options) {
    const project = (0, devkit_1.readProjectConfiguration)(tree, options.project);
    const { major: angularMajorVersion } = (0, version_utils_1.getInstalledAngularVersionInfo)(tree);
    const packageJson = (0, devkit_1.readJson)(tree, 'package.json');
    const hasLocalizePackage = !!packageJson.dependencies?.['@angular/localize'] ||
        !!packageJson.devDependencies?.['@angular/localize'];
    const baseFilesPath = (0, path_1.join)(__dirname, '..', 'files');
    let pathToFiles;
    if (angularMajorVersion >= 20) {
        pathToFiles = (0, path_1.join)(baseFilesPath, 'v20+', 'server-builder', 'root');
    }
    else {
        pathToFiles = (0, path_1.join)(baseFilesPath, 'v19', 'server-builder', 'root');
    }
    (0, devkit_1.generateFiles)(tree, pathToFiles, project.root, {
        ...options,
        rootOffset: (0, devkit_1.offsetFromRoot)(project.root),
        hasLocalizePackage,
        tpl: '',
    });
    const tsconfigServerPath = (0, devkit_1.joinPathFragments)(project.root, 'tsconfig.server.json');
    (0, devkit_1.updateJson)(tree, (0, devkit_1.joinPathFragments)(project.root, 'tsconfig.json'), (json) => {
        json.references ??= [];
        json.references.push({
            path: tsconfigServerPath,
        });
        return json;
    });
    if (angularMajorVersion >= 20) {
        (0, devkit_1.updateJson)(tree, options.buildTargetTsConfigPath, (json) => {
            const exclude = new Set(json.exclude ?? []);
            exclude.add(`src/${options.main}`);
            exclude.add(`src/${options.serverFileName}`);
            if (options.standalone) {
                exclude.add('src/app/app.config.server.ts');
            }
            json.exclude = Array.from(exclude);
            return json;
        });
    }
    if (angularMajorVersion >= 21) {
        // remove module and moduleResolution from tsconfig.server.json
        (0, devkit_1.updateJson)(tree, tsconfigServerPath, (json) => {
            delete json.compilerOptions.module;
            delete json.compilerOptions.moduleResolution;
            return json;
        });
        // read the parsed compiler options from tsconfig.server.json
        const compilerOptions = (0, tsconfig_utils_1.readCompilerOptionsFromTsConfig)(tree, tsconfigServerPath);
        const ts = (0, ensure_typescript_1.ensureTypescript)();
        if (compilerOptions.module === ts.ModuleKind.Preserve &&
            compilerOptions.moduleResolution === ts.ModuleResolutionKind.Bundler) {
            return;
        }
        (0, devkit_1.updateJson)(tree, tsconfigServerPath, (json) => {
            json.compilerOptions.module = 'preserve';
            json.compilerOptions.moduleResolution = 'bundler';
            return json;
        });
    }
}
