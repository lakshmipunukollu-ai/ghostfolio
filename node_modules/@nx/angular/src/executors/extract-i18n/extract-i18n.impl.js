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
exports.default = extractI18nExecutor;
const devkit_1 = require("@nx/devkit");
const ngcli_adapter_1 = require("nx/src/adapter/ngcli-adapter");
const project_graph_1 = require("nx/src/project-graph/project-graph");
const builder_package_1 = require("../utilities/builder-package");
const patch_builder_context_1 = require("../utilities/patch-builder-context");
async function* extractI18nExecutor(options, context) {
    const parsedBuildTarget = (0, devkit_1.parseTargetString)(options.buildTarget, context);
    const buildTargetProjectConfiguration = (0, project_graph_1.readCachedProjectConfiguration)(parsedBuildTarget.project);
    const buildTarget = buildTargetProjectConfiguration.targets[parsedBuildTarget.target];
    const isUsingEsbuildBuilder = [
        '@angular/build:application',
        '@angular-devkit/build-angular:application',
        '@angular-devkit/build-angular:browser-esbuild',
        '@nx/angular:application',
        '@nx/angular:browser-esbuild',
    ].includes(buildTarget.executor);
    const builderContext = await (0, ngcli_adapter_1.createBuilderContext)({
        builderName: '@nx/angular:extract-i18n',
        description: 'Extracts i18n messages from source code.',
        optionSchema: require('./schema.json'),
    }, context);
    /**
     * The Angular CLI extract-i18n builder make some decisions based on the build
     * target builder but it only considers `@angular-devkit/build-angular:*`
     * builders. Since we are using a custom builder, we patch the context to
     * handle `@nx/angular:*` executors.
     */
    (0, patch_builder_context_1.patchBuilderContext)(builderContext, isUsingEsbuildBuilder, parsedBuildTarget);
    (0, builder_package_1.assertBuilderPackageIsInstalled)('@angular-devkit/build-angular');
    const { executeExtractI18nBuilder } = await Promise.resolve().then(() => __importStar(require('@angular-devkit/build-angular')));
    return await executeExtractI18nBuilder(options, builderContext);
}
