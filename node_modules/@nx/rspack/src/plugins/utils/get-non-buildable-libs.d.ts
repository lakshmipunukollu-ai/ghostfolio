import { type ProjectGraph } from '@nx/devkit';
export declare function createAllowlistFromExports(packageName: string, exports: Record<string, any> | string | undefined): (string | RegExp)[];
/**
 * Get all non-buildable libraries in the project graph for a given project.
 * This function retrieves all direct and transitive dependencies of a project,
 * filtering out only those that are libraries and not buildable.
 * @param graph Project graph
 * @param projectName The project name to get dependencies for
 * @returns A list of all non-buildable libraries that the project depends on, including transitive dependencies.
 */
export declare function getNonBuildableLibs(graph: ProjectGraph, projectName: string): (string | RegExp)[];
//# sourceMappingURL=get-non-buildable-libs.d.ts.map