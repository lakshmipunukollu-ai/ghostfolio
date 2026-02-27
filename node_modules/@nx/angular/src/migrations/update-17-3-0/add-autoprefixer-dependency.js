"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = default_1;
const devkit_1 = require("@nx/devkit");
async function default_1(tree) {
    const autprefixerVersion = (0, devkit_1.getDependencyVersionFromPackageJson)(tree, 'autoprefixer');
    if (autprefixerVersion) {
        return;
    }
    const projects = (0, devkit_1.getProjects)(tree);
    for (const project of projects.values()) {
        if (project.projectType !== 'library') {
            continue;
        }
        for (const target of Object.values(project.targets ?? {})) {
            if (target.executor !== '@nx/angular:ng-packagr-lite' &&
                target.executor !== '@nx/angular:package') {
                continue;
            }
            (0, devkit_1.addDependenciesToPackageJson)(tree, {}, { autoprefixer: '^10.4.0' });
            await (0, devkit_1.formatFiles)(tree);
            return;
        }
    }
}
