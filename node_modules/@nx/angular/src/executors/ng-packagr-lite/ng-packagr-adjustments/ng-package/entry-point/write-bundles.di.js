"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getWriteBundlesTransformProvider = getWriteBundlesTransformProvider;
const ng_packagr_version_1 = require("../../../../utilities/ng-packagr/ng-packagr-version");
const package_imports_1 = require("../../../../utilities/ng-packagr/package-imports");
const write_bundles_transform_1 = require("./write-bundles.transform");
function getWriteBundlesTransformProvider() {
    const { major: ngPackagrMajorVersion } = (0, ng_packagr_version_1.getNgPackagrVersionInfo)();
    const { provideTransform } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/graph/transform.di', ngPackagrMajorVersion);
    const { WRITE_BUNDLES_TRANSFORM_TOKEN } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/ng-package/entry-point/write-bundles.di', ngPackagrMajorVersion);
    const { OPTIONS_TOKEN } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/ng-package/options.di', ngPackagrMajorVersion);
    return provideTransform({
        provide: WRITE_BUNDLES_TRANSFORM_TOKEN,
        useFactory: write_bundles_transform_1.writeBundlesTransform,
        deps: [OPTIONS_TOKEN],
    });
}
