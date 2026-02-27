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
exports.executeDevServerBuilder = executeDevServerBuilder;
const devkit_1 = require("@nx/devkit");
const js_1 = require("@nx/js");
const webpack_nx_build_coordination_plugin_1 = require("@nx/webpack/src/plugins/webpack-nx-build-coordination-plugin");
const fs_1 = require("fs");
const configuration_1 = require("nx/src/config/configuration");
const operators_1 = require("nx/src/project-graph/operators");
const project_graph_1 = require("nx/src/project-graph/project-graph");
const path_1 = require("path");
const rxjs_1 = require("rxjs");
const operators_2 = require("rxjs/operators");
const builder_package_1 = require("../../executors/utilities/builder-package");
const esbuild_extensions_1 = require("../../executors/utilities/esbuild-extensions");
const patch_builder_context_1 = require("../../executors/utilities/patch-builder-context");
const buildable_libs_1 = require("../utilities/buildable-libs");
const webpack_1 = require("../utilities/webpack");
const lib_1 = require("./lib");
function executeDevServerBuilder(rawOptions, context) {
    (0, lib_1.validateOptions)(rawOptions);
    process.env.NX_TSCONFIG_PATH = (0, js_1.getRootTsConfigPath)();
    const options = (0, lib_1.normalizeOptions)(rawOptions);
    const projectGraph = (0, devkit_1.readCachedProjectGraph)();
    const parsedBuildTarget = (0, devkit_1.parseTargetString)(options.buildTarget, {
        cwd: context.currentDirectory,
        projectGraph,
        projectName: context.target.project,
        projectsConfigurations: (0, devkit_1.readProjectsConfigurationFromProjectGraph)(projectGraph),
        root: context.workspaceRoot,
        nxJsonConfiguration: (0, configuration_1.readNxJson)(devkit_1.workspaceRoot),
        isVerbose: false,
    });
    const browserTargetProjectConfiguration = (0, project_graph_1.readCachedProjectConfiguration)(parsedBuildTarget.project);
    const buildTarget = browserTargetProjectConfiguration.targets[parsedBuildTarget.target];
    const buildTargetOptions = {
        ...buildTarget.options,
        ...(parsedBuildTarget.configuration
            ? buildTarget.configurations[parsedBuildTarget.configuration]
            : buildTarget.defaultConfiguration
                ? buildTarget.configurations[buildTarget.defaultConfiguration]
                : {}),
    };
    const buildLibsFromSource = options.buildLibsFromSource ??
        buildTargetOptions.buildLibsFromSource ??
        true;
    process.env.NX_BUILD_LIBS_FROM_SOURCE = `${buildLibsFromSource}`;
    process.env.NX_BUILD_TARGET = options.buildTarget;
    let pathToWebpackConfig;
    if (buildTargetOptions.customWebpackConfig?.path) {
        pathToWebpackConfig = (0, devkit_1.joinPathFragments)(context.workspaceRoot, buildTargetOptions.customWebpackConfig.path);
        if (pathToWebpackConfig && !(0, fs_1.existsSync)(pathToWebpackConfig)) {
            throw new Error(`Custom Webpack Config File Not Found!\nTo use a custom webpack config, please ensure the path to the custom webpack file is correct: \n${pathToWebpackConfig}`);
        }
    }
    const normalizedIndexHtmlTransformer = buildTargetOptions.indexHtmlTransformer ??
        buildTargetOptions.indexFileTransformer;
    let pathToIndexFileTransformer;
    if (normalizedIndexHtmlTransformer) {
        pathToIndexFileTransformer = (0, devkit_1.joinPathFragments)(context.workspaceRoot, normalizedIndexHtmlTransformer);
        if (pathToIndexFileTransformer && !(0, fs_1.existsSync)(pathToIndexFileTransformer)) {
            throw new Error(`File containing Index File Transformer function Not Found!\n Please ensure the path to the file containing the function is correct: \n${pathToIndexFileTransformer}`);
        }
    }
    let dependencies;
    if (!buildLibsFromSource) {
        const { tsConfigPath, dependencies: foundDependencies } = (0, buildable_libs_1.createTmpTsConfigForBuildableLibs)(buildTargetOptions.tsConfig, context, {
            target: parsedBuildTarget.target,
        });
        dependencies = foundDependencies;
        const relativeTsConfigPath = (0, devkit_1.normalizePath)((0, path_1.relative)(context.workspaceRoot, tsConfigPath));
        // We can't just pass the tsconfig path in memory to the angular builder
        // function because we can't pass the build target options to it, the build
        // targets options will be retrieved by the builder from the project
        // configuration. Therefore, we patch the method in the context to retrieve
        // the target options to overwrite the tsconfig path to use the generated
        // one with the updated path mappings.
        const originalGetTargetOptions = context.getTargetOptions;
        context.getTargetOptions = async (target) => {
            const options = await originalGetTargetOptions(target);
            options.tsConfig = relativeTsConfigPath;
            return options;
        };
        // The buildTargetConfiguration also needs to use the generated tsconfig path
        // otherwise the build will fail if customWebpack function/file is referencing
        // local libs. This synchronize the behavior with webpack-browser and
        // webpack-server implementation.
        buildTargetOptions.tsConfig = relativeTsConfigPath;
    }
    const delegateBuilderOptions = getDelegateBuilderOptions(options);
    const isUsingWebpackBuilder = ![
        '@angular/build:application',
        '@angular-devkit/build-angular:application',
        '@angular-devkit/build-angular:browser-esbuild',
        '@nx/angular:application',
        '@nx/angular:browser-esbuild',
    ].includes(buildTarget.executor);
    /**
     * The Angular CLI dev-server builder make some decisions based on the build
     * target builder but it only considers `@angular-devkit/build-angular:*`
     * builders. Since we are using a custom builder, we patch the context to
     * handle `@nx/angular:*` executors.
     */
    (0, patch_builder_context_1.patchBuilderContext)(context, !isUsingWebpackBuilder, parsedBuildTarget);
    (0, builder_package_1.assertBuilderPackageIsInstalled)('@angular-devkit/build-angular');
    return (0, rxjs_1.combineLatest)([
        (0, rxjs_1.from)(Promise.resolve().then(() => __importStar(require('@angular-devkit/build-angular')))),
        (0, rxjs_1.from)((0, esbuild_extensions_1.loadPlugins)(buildTargetOptions.plugins, buildTargetOptions.tsConfig)),
        (0, rxjs_1.from)((0, esbuild_extensions_1.loadMiddleware)(options.esbuildMiddleware, buildTargetOptions.tsConfig)),
        (0, rxjs_1.from)(loadIndexHtmlFileTransformer(pathToIndexFileTransformer, buildTargetOptions.tsConfig, context, isUsingWebpackBuilder)),
    ]).pipe((0, operators_2.switchMap)(([{ executeDevServerBuilder }, plugins, middleware, indexHtmlTransformer,]) => executeDevServerBuilder(delegateBuilderOptions, context, {
        webpackConfiguration: isUsingWebpackBuilder
            ? async (baseWebpackConfig) => {
                if (!buildLibsFromSource) {
                    const workspaceDependencies = dependencies
                        .filter((dep) => !(0, operators_1.isNpmProject)(dep.node))
                        .map((dep) => dep.node.name);
                    // default for `nx run-many` is --all projects
                    // by passing an empty string for --projects, run-many will default to
                    // run the target for all projects.
                    // This will occur when workspaceDependencies = []
                    if (workspaceDependencies.length > 0) {
                        baseWebpackConfig.plugins.push(new webpack_nx_build_coordination_plugin_1.WebpackNxBuildCoordinationPlugin(`nx run-many --target=${parsedBuildTarget.target} --projects=${workspaceDependencies.join(',')}`, { skipWatchingDeps: !options.watchDependencies }) // TODO(Colum): this can be removed when angular 20.2 is merged
                        );
                    }
                }
                if (!pathToWebpackConfig) {
                    return baseWebpackConfig;
                }
                return (0, webpack_1.mergeCustomWebpackConfig)(baseWebpackConfig, pathToWebpackConfig, buildTargetOptions, context.target);
            }
            : undefined,
        ...(indexHtmlTransformer
            ? {
                indexHtml: indexHtmlTransformer,
            }
            : {}),
    }, {
        buildPlugins: plugins,
        middleware,
    })));
}
exports.default = require('@angular-devkit/architect').createBuilder(executeDevServerBuilder);
function getDelegateBuilderOptions(options) {
    const delegateBuilderOptions = {
        ...options,
    };
    // delete extra option not supported by the delegate builder
    delete delegateBuilderOptions.buildLibsFromSource;
    delete delegateBuilderOptions.watchDependencies;
    return delegateBuilderOptions;
}
async function loadIndexHtmlFileTransformer(pathToIndexFileTransformer, tsConfig, context, isUsingWebpackBuilder) {
    if (!pathToIndexFileTransformer) {
        return undefined;
    }
    return isUsingWebpackBuilder
        ? (0, webpack_1.resolveIndexHtmlTransformer)(pathToIndexFileTransformer, tsConfig, context.target)
        : await (0, esbuild_extensions_1.loadIndexHtmlTransformer)(pathToIndexFileTransformer, tsConfig);
}
