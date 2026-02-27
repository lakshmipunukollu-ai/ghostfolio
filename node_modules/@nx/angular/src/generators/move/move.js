"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.angularMoveGenerator = angularMoveGenerator;
const move_1 = require("@nx/workspace/src/generators/move/move");
/**
 * @deprecated Use the `@nx/workspace:move` generator instead. It will be removed in Nx v22.
 */
async function angularMoveGenerator(tree, schema) {
    process.env.NX_ANGULAR_MOVE_INVOKED = 'true';
    await (0, move_1.moveGenerator)(tree, schema);
}
