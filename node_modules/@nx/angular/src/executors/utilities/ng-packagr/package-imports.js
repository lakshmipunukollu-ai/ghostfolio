"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.importNgPackagrPath = importNgPackagrPath;
function importNgPackagrPath(path, ngPackagrMajorVersion) {
    let finalPath = path;
    if (ngPackagrMajorVersion < 20 && path.startsWith('ng-packagr/src/')) {
        finalPath = path.replace(/^ng-packagr\/src\//, 'ng-packagr/');
    }
    return require(finalPath);
}
