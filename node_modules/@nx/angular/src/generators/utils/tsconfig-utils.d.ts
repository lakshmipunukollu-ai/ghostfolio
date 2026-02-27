import type { Tree } from '@nx/devkit';
import type * as ts from 'typescript';
/**
 * Gets the resolved value of a specific compiler option from the TypeScript configuration hierarchy.
 *
 * @param tree - The file system tree
 * @param tsConfigPath - Path to the tsconfig file to resolve
 * @param optionName - Name of the compiler option to retrieve
 * @returns The resolved value of the compiler option, or undefined if not set
 */
export declare function getDefinedCompilerOption(tree: Tree, tsConfigPath: string, optionName: keyof ts.CompilerOptions): any | undefined;
export declare function readCompilerOptionsFromTsConfig(tree: Tree, tsConfigPath: string): ts.CompilerOptions;
//# sourceMappingURL=tsconfig-utils.d.ts.map