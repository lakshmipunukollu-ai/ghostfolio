"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getStylesheetProcessorFactoryProvider = getStylesheetProcessorFactoryProvider;
const ng_packagr_version_1 = require("./ng-packagr-version");
const package_imports_1 = require("./package-imports");
function getStylesheetProcessorFactoryProvider() {
    const { major: ngPackagrMajorVersion } = (0, ng_packagr_version_1.getNgPackagrVersionInfo)();
    const { STYLESHEET_PROCESSOR_TOKEN } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/styles/stylesheet-processor.di', ngPackagrMajorVersion);
    return {
        provide: STYLESHEET_PROCESSOR_TOKEN,
        useFactory: () => {
            const { getStylesheetProcessor } = require('./stylesheet-processor');
            return getStylesheetProcessor();
        },
        deps: [],
    };
}
