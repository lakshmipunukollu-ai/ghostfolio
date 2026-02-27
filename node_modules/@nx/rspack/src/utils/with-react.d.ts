import { Configuration } from '@rspack/core';
import { NxRspackExecutionContext } from './config';
import { WithWebOptions } from './with-web';
import { SvgrOptions } from '../plugins/utils/models';
export interface WithReactOptions extends WithWebOptions {
    /**
     * @deprecated SVGR support is deprecated and will be removed in Nx 23.
     * TODO(v23): Remove SVGR support
     */
    svgr?: boolean | SvgrOptions;
}
export declare function withReact(opts?: WithReactOptions): (config: Configuration, { options, context }: NxRspackExecutionContext) => Configuration;
//# sourceMappingURL=with-react.d.ts.map