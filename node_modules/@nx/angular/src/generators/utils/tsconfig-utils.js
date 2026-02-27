"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getDefinedCompilerOption = getDefinedCompilerOption;
exports.readCompilerOptionsFromTsConfig = readCompilerOptionsFromTsConfig;
const ensure_typescript_1 = require("@nx/js/src/utils/typescript/ensure-typescript");
const node_path_1 = require("node:path");
/**
 * Gets the resolved value of a specific compiler option from the TypeScript configuration hierarchy.
 *
 * @param tree - The file system tree
 * @param tsConfigPath - Path to the tsconfig file to resolve
 * @param optionName - Name of the compiler option to retrieve
 * @returns The resolved value of the compiler option, or undefined if not set
 */
function getDefinedCompilerOption(tree, tsConfigPath, optionName) {
    const compilerOptions = readCompilerOptionsFromTsConfig(tree, tsConfigPath);
    return compilerOptions[optionName];
}
function readCompilerOptionsFromTsConfig(tree, tsConfigPath) {
    const ts = (0, ensure_typescript_1.ensureTypescript)();
    const tsSysFromTree = {
        ...ts.sys,
        readDirectory: () => [],
        readFile: (path) => tree.read(path, 'utf-8'),
        fileExists: (path) => tree.exists(path),
    };
    const parsed = ts.parseJsonConfigFileContent(ts.readConfigFile(tsConfigPath, tsSysFromTree.readFile).config, tsSysFromTree, (0, node_path_1.dirname)(tsConfigPath));
    return parsed.options;
}
