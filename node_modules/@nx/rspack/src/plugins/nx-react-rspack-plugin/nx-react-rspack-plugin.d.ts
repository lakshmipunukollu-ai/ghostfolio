import type { Compiler } from '@rspack/core';
export declare class NxReactRspackPlugin {
    private options;
    constructor(options?: {
        /**
         * @deprecated SVGR support is deprecated and will be removed in Nx 23.
         * TODO(v23): Remove SVGR support
         */
        svgr?: boolean;
    });
    apply(compiler: Compiler): void;
}
//# sourceMappingURL=nx-react-rspack-plugin.d.ts.map