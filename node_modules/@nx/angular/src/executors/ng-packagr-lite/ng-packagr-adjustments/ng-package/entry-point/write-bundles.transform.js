"use strict";
/**
 * Adapted from the original ng-packagr.
 *
 * Changes made:
 * - Removed bundling altogether.
 * - Write the ESM2022 outputs to the file system.
 * - Fake the FESM2022 outputs pointing them to the ESM2022 outputs.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.writeBundlesTransform = void 0;
const promises_1 = require("node:fs/promises");
const node_path_1 = require("node:path");
const ng_packagr_version_1 = require("../../../../utilities/ng-packagr/ng-packagr-version");
const package_imports_1 = require("../../../../utilities/ng-packagr/package-imports");
const entry_point_1 = require("./entry-point");
async function shouldWriteFile(filePath, newContent) {
    try {
        const existingContent = await (0, promises_1.readFile)(filePath, 'utf-8');
        return existingContent !== newContent;
    }
    catch (error) {
        // If we can't read the existing file (including if it doesn't exist), write the new one
        return true;
    }
}
const writeBundlesTransform = (_options) => {
    const { major: ngPackagrMajorVersion } = (0, ng_packagr_version_1.getNgPackagrVersionInfo)();
    const { transformFromPromise } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/graph/transform', ngPackagrMajorVersion);
    const { isEntryPointInProgress, isPackage } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/ng-package/nodes', ngPackagrMajorVersion);
    const { NgPackage } = (0, package_imports_1.importNgPackagrPath)('ng-packagr/src/lib/ng-package/package', ngPackagrMajorVersion);
    return transformFromPromise(async (graph) => {
        const entryPointNode = graph.find(isEntryPointInProgress());
        if (!entryPointNode) {
            return;
        }
        const entryPoint = toCustomNgEntryPoint(entryPointNode.data.entryPoint);
        entryPointNode.data.entryPoint = entryPoint;
        entryPointNode.data.destinationFiles = entryPoint.destinationFiles;
        for (const [path, outputCache,] of entryPointNode.cache.outputCache.entries()) {
            const normalizedPath = normalizeEsm2022Path(path, entryPoint);
            // Only write if content has changed
            if (await shouldWriteFile(normalizedPath, outputCache.content)) {
                await (0, promises_1.mkdir)((0, node_path_1.dirname)(normalizedPath), { recursive: true });
                await (0, promises_1.writeFile)(normalizedPath, outputCache.content);
            }
        }
        if (!entryPointNode.cache.outputCache.size &&
            entryPoint.isSecondaryEntryPoint) {
            await (0, promises_1.mkdir)(entryPoint.destinationPath, { recursive: true });
        }
        // Update package node only when processing the primary entry point
        if (!entryPoint.isSecondaryEntryPoint) {
            const packageNode = graph.find(isPackage);
            if (packageNode) {
                packageNode.data = new NgPackage(packageNode.data.src, toCustomNgEntryPoint(packageNode.data.primary), packageNode.data.secondaries.map((secondary) => toCustomNgEntryPoint(secondary)));
            }
        }
    });
};
exports.writeBundlesTransform = writeBundlesTransform;
function normalizeEsm2022Path(path, entryPoint) {
    const normalizedPath = (0, node_path_1.normalize)(path);
    if (!entryPoint.primaryDestinationPath) {
        return normalizedPath;
    }
    if (normalizedPath.startsWith((0, node_path_1.join)(entryPoint.primaryDestinationPath, 'tmp-esm2022'))) {
        return normalizedPath.replace('tmp-esm2022', 'esm2022');
    }
    if (normalizedPath.startsWith((0, node_path_1.join)(entryPoint.primaryDestinationPath, 'tmp-typings'))) {
        return normalizedPath.replace('tmp-typings', '');
    }
    return normalizedPath;
}
function toCustomNgEntryPoint(entryPoint) {
    return (0, entry_point_1.createNgEntryPoint)(entryPoint.packageJson, entryPoint.ngPackageJson, entryPoint.basePath, 
    // @ts-expect-error this is a TS private property, but it can be accessed at runtime
    entryPoint.secondaryData);
}
