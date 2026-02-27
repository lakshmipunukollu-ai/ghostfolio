"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createNgEntryPoint = createNgEntryPoint;
const node_path_1 = require("node:path");
const ng_packagr_version_1 = require("../../../../utilities/ng-packagr/ng-packagr-version");
const package_imports_1 = require("../../../../utilities/ng-packagr/package-imports");
function createNgEntryPoint(packageJson, ngPackageJson, basePath, secondaryData) {
    const { major: ngPackagrMajorVersion } = (0, ng_packagr_version_1.getNgPackagrVersionInfo)();
    const { NgEntryPoint: NgEntryPointBase } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/ng-package/entry-point/entry-point', ngPackagrMajorVersion);
    if (ngPackagrMajorVersion < 20) {
        class NgEntryPoint extends NgEntryPointBase {
            /**
             * Point the FESM2022 files to the ESM2022 files.
             */
            get destinationFiles() {
                const result = super.destinationFiles;
                result.fesm2022 = result.esm2022;
                result.fesm2022Dir = (0, node_path_1.dirname)(result.esm2022);
                return result;
            }
        }
        return new NgEntryPoint(packageJson, ngPackageJson, basePath, secondaryData);
    }
    const { ensureUnixPath } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/utils/path', ngPackagrMajorVersion);
    class NgEntryPoint extends NgEntryPointBase {
        constructor(packageJson, ngPackageJson, basePath, _secondaryData) {
            super(packageJson, ngPackageJson, basePath, _secondaryData);
            this.packageJson = packageJson;
            this.ngPackageJson = ngPackageJson;
            this.basePath = basePath;
            this._secondaryData = _secondaryData;
        }
        get primaryDestinationPath() {
            return (this._secondaryData?.primaryDestinationPath ?? this.destinationPath);
        }
        get destinationFiles() {
            let primaryDestPath = this.destinationPath;
            let secondaryDir = '';
            if (this._secondaryData) {
                primaryDestPath = this._secondaryData.primaryDestinationPath;
                secondaryDir = (0, node_path_1.relative)(primaryDestPath, this._secondaryData.destinationPath);
            }
            const flatModuleFile = this.flatModuleFile;
            const pathJoinWithDest = (...paths) => (0, node_path_1.join)(primaryDestPath, ...paths);
            return {
                directory: ensureUnixPath(secondaryDir),
                declarations: pathJoinWithDest('tmp-typings', secondaryDir, `${flatModuleFile}.d.ts`),
                // changed to use esm2022
                declarationsBundled: pathJoinWithDest(secondaryDir, `${flatModuleFile}.d.ts`),
                declarationsDir: pathJoinWithDest(secondaryDir),
                esm2022: pathJoinWithDest('tmp-esm2022', secondaryDir, `${flatModuleFile}.js`),
                // changed to use esm2022
                fesm2022: pathJoinWithDest('esm2022', secondaryDir, `${flatModuleFile}.js`),
                // changed to use esm2022
                fesm2022Dir: pathJoinWithDest('esm2022'),
            };
        }
    }
    return new NgEntryPoint(packageJson, ngPackageJson, basePath, secondaryData);
}
