"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeWebpackServerBuilder = executeWebpackServerBuilder;
const devkit_1 = require("@nx/devkit");
const fs_1 = require("fs");
const path_1 = require("path");
const rxjs_1 = require("rxjs");
const operators_1 = require("rxjs/operators");
const builder_package_1 = require("../../executors/utilities/builder-package");
const buildable_libs_1 = require("../utilities/buildable-libs");
const webpack_1 = require("../utilities/webpack");
// This is required to ensure that the webpack version used by the Module Federation is the same as the one used by the builders.
const Module = require('module');
const originalResolveFilename = Module._resolveFilename;
const patchedWebpackPath = require.resolve('webpack', {
    paths: [require.resolve('@angular-devkit/build-angular')],
});
// Override the resolve function
Module._resolveFilename = function (request, parent, isMain, options) {
    // Intercept webpack specifically
    if (request === 'webpack') {
        // Force webpack to resolve from your specific path
        return patchedWebpackPath;
    }
    // For all other modules, use the original resolver
    return originalResolveFilename.call(this, request, parent, isMain, options);
};
function buildServerApp(options, context) {
    (0, builder_package_1.assertBuilderPackageIsInstalled)('@angular-devkit/build-angular');
    const { buildLibsFromSource, customWebpackConfig, ...delegateOptions } = options;
    // If there is a path to custom webpack config
    // Invoke our own support for custom webpack config
    if (customWebpackConfig && customWebpackConfig.path) {
        const pathToWebpackConfig = (0, devkit_1.joinPathFragments)(context.workspaceRoot, customWebpackConfig.path);
        if ((0, fs_1.existsSync)(pathToWebpackConfig)) {
            return buildServerAppWithCustomWebpackConfiguration(delegateOptions, context, pathToWebpackConfig);
        }
        else {
            throw new Error(`Custom Webpack Config File Not Found!\nTo use a custom webpack config, please ensure the path to the custom webpack file is correct: \n${pathToWebpackConfig}`);
        }
    }
    return (0, rxjs_1.from)(Promise.resolve().then(() => __importStar(require('@angular-devkit/build-angular')))).pipe((0, operators_1.switchMap)(({ executeServerBuilder }) => executeServerBuilder(delegateOptions, context)));
}
function buildServerAppWithCustomWebpackConfiguration(options, context, pathToWebpackConfig) {
    return (0, rxjs_1.from)(Promise.resolve().then(() => __importStar(require('@angular-devkit/build-angular')))).pipe((0, operators_1.switchMap)(({ executeServerBuilder }) => executeServerBuilder(options, context, {
        webpackConfiguration: async (baseWebpackConfig) => {
            // Angular auto includes code from @angular/platform-server
            // This includes the code outside the shared scope created by ModuleFederation
            // This code will be included in the generated code from our generators,
            // maintaining it within the shared scope.
            // Therefore, if the build is an MF Server build, remove the auto-includes from
            // the base webpack config from Angular
            let mergedConfig = await (0, webpack_1.mergeCustomWebpackConfig)(baseWebpackConfig, pathToWebpackConfig, options, context.target);
            if (mergedConfig.target === 'async-node') {
                mergedConfig.entry.main = mergedConfig.entry.main.filter((m) => !m.startsWith('@angular/platform-server/init'));
                mergedConfig.module.rules = mergedConfig.module.rules.filter((m) => !m.loader
                    ? true
                    : !m.loader.endsWith('@angular-devkit/build-angular/src/builders/server/platform-server-exports-loader.js'));
            }
            return mergedConfig;
        },
    })));
}
function executeWebpackServerBuilder(options, context) {
    options.buildLibsFromSource ??= true;
    process.env.NX_BUILD_LIBS_FROM_SOURCE = `${options.buildLibsFromSource}`;
    process.env.NX_BUILD_TARGET = (0, devkit_1.targetToTargetString)({ ...context.target });
    if (!options.buildLibsFromSource) {
        const { tsConfigPath } = (0, buildable_libs_1.createTmpTsConfigForBuildableLibs)(options.tsConfig, context);
        options.tsConfig = (0, devkit_1.normalizePath)((0, path_1.relative)(context.workspaceRoot, tsConfigPath));
    }
    return buildServerApp(options, context);
}
exports.default = require('@angular-devkit/architect').createBuilder(executeWebpackServerBuilder);
