# SPDX-License-Identifier: Apache-2.0
import numpy as np

def robust_limits(a,low=2,high=98):
    z=np.asarray(a); z=z[np.isfinite(z)]
    return (float(np.percentile(z,low)),float(np.percentile(z,high))) if z.size else (np.nan,np.nan)

def summary(a):
    z=np.asarray(a); z=z[np.isfinite(z)]
    return {'count':int(z.size),'min':float(z.min()),'max':float(z.max()),'mean':float(z.mean()),'std':float(z.std())} if z.size else {}
