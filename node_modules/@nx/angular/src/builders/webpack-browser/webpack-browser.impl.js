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
exports.executeWebpackBrowserBuilder = executeWebpackBrowserBuilder;
const devkit_1 = require("@nx/devkit");
const webpack_nx_build_coordination_plugin_1 = require("@nx/webpack/src/plugins/webpack-nx-build-coordination-plugin");
const fs_1 = require("fs");
const operators_1 = require("nx/src/project-graph/operators");
const utils_1 = require("nx/src/tasks-runner/utils");
const path_1 = require("path");
const rxjs_1 = require("rxjs");
const operators_2 = require("rxjs/operators");
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
function shouldSkipInitialTargetRun(projectGraph, project, target) {
    const allTargetNames = new Set();
    for (const projectName in projectGraph.nodes) {
        const project = projectGraph.nodes[projectName];
        for (const targetName in project.data.targets ?? {}) {
            allTargetNames.add(targetName);
        }
    }
    const projectDependencyConfigs = (0, utils_1.getDependencyConfigs)({ project, target }, {}, projectGraph, Array.from(allTargetNames));
    // if the task runner already ran the target, skip the initial run
    return projectDependencyConfigs.some((d) => d.target === target && d.projects === 'dependencies');
}
function executeWebpackBrowserBuilder(options, context) {
    options.buildLibsFromSource ??= true;
    options.watchDependencies ??= true;
    const { buildLibsFromSource, customWebpackConfig, indexHtmlTransformer, watchDependencies, ...delegateBuilderOptions } = options;
    process.env.NX_BUILD_LIBS_FROM_SOURCE = `${buildLibsFromSource}`;
    process.env.NX_BUILD_TARGET = (0, devkit_1.targetToTargetString)({ ...context.target });
    const pathToWebpackConfig = customWebpackConfig?.path &&
        (0, devkit_1.joinPathFragments)(context.workspaceRoot, customWebpackConfig.path);
    if (pathToWebpackConfig && !(0, fs_1.existsSync)(pathToWebpackConfig)) {
        throw new Error(`Custom Webpack Config File Not Found!\nTo use a custom webpack config, please ensure the path to the custom webpack file is correct: \n${pathToWebpackConfig}`);
    }
    const pathToIndexFileTransformer = indexHtmlTransformer &&
        (0, devkit_1.joinPathFragments)(context.workspaceRoot, indexHtmlTransformer);
    if (pathToIndexFileTransformer && !(0, fs_1.existsSync)(pathToIndexFileTransformer)) {
        throw new Error(`File containing Index File Transformer function Not Found!\n Please ensure the path to the file containing the function is correct: \n${pathToIndexFileTransformer}`);
    }
    let dependencies;
    let projectGraph;
    if (!buildLibsFromSource) {
        projectGraph = (0, devkit_1.readCachedProjectGraph)();
        const { tsConfigPath, dependencies: foundDependencies } = (0, buildable_libs_1.createTmpTsConfigForBuildableLibs)(delegateBuilderOptions.tsConfig, context, { projectGraph });
        dependencies = foundDependencies;
        delegateBuilderOptions.tsConfig = (0, devkit_1.normalizePath)((0, path_1.relative)(context.workspaceRoot, tsConfigPath));
    }
    (0, builder_package_1.assertBuilderPackageIsInstalled)('@angular-devkit/build-angular');
    return (0, rxjs_1.from)(Promise.resolve().then(() => __importStar(require('@angular-devkit/build-angular')))).pipe((0, operators_2.switchMap)(({ executeBrowserBuilder }) => executeBrowserBuilder(delegateBuilderOptions, context, {
        webpackConfiguration: (baseWebpackConfig) => {
            if (!buildLibsFromSource && delegateBuilderOptions.watch) {
                const workspaceDependencies = dependencies
                    .filter((dep) => !(0, operators_1.isNpmProject)(dep.node))
                    .map((dep) => dep.node.name);
                // default for `nx run-many` is --all projects
                // by passing an empty string for --projects, run-many will default to
                // run the target for all projects.
                // This will occur when workspaceDependencies = []
                if (workspaceDependencies.length > 0) {
                    const skipInitialRun = shouldSkipInitialTargetRun(projectGraph, context.target.project, context.target.target);
                    baseWebpackConfig.plugins.push(
                    // @ts-expect-error - difference between angular and webpack plugin definitions bc of webpack versions
                    new webpack_nx_build_coordination_plugin_1.WebpackNxBuildCoordinationPlugin(`nx run-many --target=${context.target.target} --projects=${workspaceDependencies.join(',')}`, { skipInitialRun, skipWatchingDeps: !watchDependencies }));
                }
            }
            if (!pathToWebpackConfig) {
                return baseWebpackConfig;
            }
            return (0, webpack_1.mergeCustomWebpackConfig)(baseWebpackConfig, pathToWebpackConfig, delegateBuilderOptions, context.target);
        },
        ...(pathToIndexFileTransformer
            ? {
                indexHtml: (0, webpack_1.resolveIndexHtmlTransformer)(pathToIndexFileTransformer, delegateBuilderOptions.tsConfig, context.target),
            }
            : {}),
    })));
}
exports.default = require('@angular-devkit/architect').createBuilder(executeWebpackBrowserBuilder);
