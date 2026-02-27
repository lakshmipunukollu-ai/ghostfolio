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
exports.default = applicationExecutor;
const ngcli_adapter_1 = require("nx/src/adapter/ngcli-adapter");
const angular_version_utils_1 = require("../utilities/angular-version-utils");
const buildable_libs_1 = require("../utilities/buildable-libs");
const builder_package_1 = require("../utilities/builder-package");
const esbuild_extensions_1 = require("../utilities/esbuild-extensions");
const normalize_options_1 = require("./utils/normalize-options");
const validate_options_1 = require("./utils/validate-options");
async function* applicationExecutor(options, context) {
    (0, validate_options_1.validateOptions)(options);
    options = (0, normalize_options_1.normalizeOptions)(options);
    const { buildLibsFromSource = true, plugins: pluginPaths, indexHtmlTransformer: indexHtmlTransformerPath, ...delegateExecutorOptions } = options;
    let dependencies;
    if (!buildLibsFromSource) {
        const { tsConfigPath, dependencies: foundDependencies } = (0, buildable_libs_1.createTmpTsConfigForBuildableLibs)(delegateExecutorOptions.tsConfig, context);
        dependencies = foundDependencies;
        delegateExecutorOptions.tsConfig = tsConfigPath;
    }
    const plugins = await (0, esbuild_extensions_1.loadPlugins)(pluginPaths, options.tsConfig);
    const indexHtmlTransformer = indexHtmlTransformerPath
        ? await (0, esbuild_extensions_1.loadIndexHtmlTransformer)(indexHtmlTransformerPath, options.tsConfig)
        : undefined;
    const builderContext = await (0, ngcli_adapter_1.createBuilderContext)({
        builderName: '@nx/angular:application',
        description: 'Build an application.',
        optionSchema: require('./schema.json'),
    }, context);
    const { major: angularMajorVersion } = (0, angular_version_utils_1.getInstalledAngularVersionInfo)();
    if (angularMajorVersion >= 20) {
        (0, builder_package_1.assertBuilderPackageIsInstalled)('@angular/build');
        const { buildApplication } = await Promise.resolve().then(() => __importStar(require('@angular/build')));
        return yield* buildApplication(delegateExecutorOptions, builderContext, {
            codePlugins: plugins,
            indexHtmlTransformer,
        });
    }
    (0, builder_package_1.assertBuilderPackageIsInstalled)('@angular-devkit/build-angular');
    const { buildApplication } = await Promise.resolve().then(() => __importStar(require('@angular-devkit/build-angular')));
    return yield* buildApplication(delegateExecutorOptions, builderContext, {
        codePlugins: plugins,
        indexHtmlTransformer,
    });
}
