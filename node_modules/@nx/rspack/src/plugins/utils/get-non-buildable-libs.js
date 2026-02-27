"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAllowlistFromExports = createAllowlistFromExports;
exports.getNonBuildableLibs = getNonBuildableLibs;
const devkit_1 = require("@nx/devkit");
const path_1 = require("path");
const get_transitive_deps_1 = require("./get-transitive-deps");
const is_lib_buildable_1 = require("./is-lib-buildable");
function escapePackageName(packageName) {
    return packageName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
function escapeRegexAndConvertWildcard(pattern) {
    return pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\\\*/g, '.*');
}
function resolveConditionalExport(target) {
    if (typeof target === 'string') {
        return target;
    }
    if (typeof target === 'object' && target !== null) {
        // Priority order for conditions
        const conditions = ['development', 'import', 'require', 'default'];
        for (const condition of conditions) {
            if (target[condition] && typeof target[condition] === 'string') {
                return target[condition];
            }
        }
    }
    return null;
}
function createAllowlistFromExports(packageName, exports) {
    if (!exports) {
        return [packageName];
    }
    const allowlist = [];
    allowlist.push(packageName);
    if (typeof exports === 'string') {
        return allowlist;
    }
    if (typeof exports === 'object') {
        for (const [exportPath, target] of Object.entries(exports)) {
            if (typeof exportPath !== 'string')
                continue;
            const resolvedTarget = resolveConditionalExport(target);
            if (!resolvedTarget)
                continue;
            if (exportPath === '.') {
                continue;
            }
            else if (exportPath.startsWith('./')) {
                const subpath = exportPath.slice(2);
                if (subpath.includes('*')) {
                    const regexPattern = escapeRegexAndConvertWildcard(subpath);
                    allowlist.push(new RegExp(`^${escapePackageName(packageName)}/${regexPattern}$`));
                }
                else {
                    allowlist.push(`${packageName}/${subpath}`);
                }
            }
        }
    }
    return allowlist;
}
/**
 * Get all non-buildable libraries in the project graph for a given project.
 * This function retrieves all direct and transitive dependencies of a project,
 * filtering out only those that are libraries and not buildable.
 * @param graph Project graph
 * @param projectName The project name to get dependencies for
 * @returns A list of all non-buildable libraries that the project depends on, including transitive dependencies.
 */
function getNonBuildableLibs(graph, projectName) {
    const deps = graph?.dependencies?.[projectName] ?? [];
    const allNonBuildable = new Set();
    // First, find all direct non-buildable deps and add them App -> library
    const directNonBuildable = deps.filter((dep) => {
        const node = graph.nodes?.[dep.target];
        if (!node || node.type !== 'lib')
            return false;
        const hasBuildTarget = 'build' in (node.data?.targets ?? {});
        if (hasBuildTarget)
            return false;
        return !(0, is_lib_buildable_1.isBuildableLibrary)(node);
    });
    // Add direct non-buildable dependencies with expanded export patterns
    for (const dep of directNonBuildable) {
        const node = graph.nodes?.[dep.target];
        const packageName = node?.data?.metadata?.js?.packageName;
        if (packageName) {
            // Get exports from project metadata first (most reliable)
            const packageExports = node?.data?.metadata?.js?.packageExports;
            if (packageExports) {
                // Use metadata exports if available
                const allowlistPatterns = createAllowlistFromExports(packageName, packageExports);
                allowlistPatterns.forEach((pattern) => allNonBuildable.add(pattern));
            }
            else {
                // Fallback: try to read package.json directly
                try {
                    const projectRoot = node.data.root;
                    const packageJsonPath = (0, path_1.join)(projectRoot, 'package.json');
                    const packageJson = (0, devkit_1.readJsonFile)(packageJsonPath);
                    const allowlistPatterns = createAllowlistFromExports(packageName, packageJson.exports);
                    allowlistPatterns.forEach((pattern) => allNonBuildable.add(pattern));
                }
                catch (error) {
                    // Final fallback: just add base package name
                    allNonBuildable.add(packageName);
                }
            }
        }
        // Get all transitive non-buildable dependencies App -> library1 -> library2
        const transitiveDeps = (0, get_transitive_deps_1.getAllTransitiveDeps)(graph, dep.target);
        transitiveDeps.forEach((pkg) => allNonBuildable.add(pkg));
    }
    return Array.from(allNonBuildable);
}
