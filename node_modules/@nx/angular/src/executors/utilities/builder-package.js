"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.assertBuilderPackageIsInstalled = assertBuilderPackageIsInstalled;
function assertBuilderPackageIsInstalled(packageName) {
    try {
        require.resolve(packageName);
    }
    catch {
        throw new Error(`This executor requires the package ${packageName} to be installed. Please make sure it is installed and try again.`);
    }
}
