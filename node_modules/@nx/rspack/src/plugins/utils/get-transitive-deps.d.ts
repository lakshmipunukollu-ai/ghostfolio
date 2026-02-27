import { type ProjectGraph } from '@nx/devkit';
/**
 * Get all transitive dependencies of a target that are non-buildable libraries.
 * This function traverses the project graph to find all dependencies of a given target,
 * @param graph Graph of the project
 * @param targetName The project name to get dependencies for
 * @param visited Set to keep track of visited nodes to prevent infinite loops in circular dependencies
 * @returns string[] - List of all transitive dependencies that are non-buildable libraries
 */
export declare function getAllTransitiveDeps(graph: ProjectGraph, targetName: string, visited?: Set<string>): string[];
//# sourceMappingURL=get-transitive-deps.d.ts.map