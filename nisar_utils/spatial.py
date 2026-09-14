# SPDX-License-Identifier: Apache-2.0
import numpy as np

def coordinate_to_index(x,y,xmin,xmax,ymin,ymax):
    c0=int(np.searchsorted(x,xmin,'left')); c1=int(np.searchsorted(x,xmax,'right'))
    # y is often descending
    if y[0]>y[-1]:
        r0=int(np.searchsorted(-y,-ymax,'left')); r1=int(np.searchsorted(-y,-ymin,'right'))
    else:
        r0=int(np.searchsorted(y,ymin,'left')); r1=int(np.searchsorted(y,ymax,'right'))
    return max(0,r0),min(len(y),r1),max(0,c0),min(len(x),c1)

def get_window_extent(x,y,r0,r1,c0,c1):
    return (float(x[c0]),float(x[c1-1]),float(y[r1-1]),float(y[r0]))

def pixel_centers_to_extent(x,y):
    return (float(x.min()-abs(np.diff(x).mean())/2),float(x.max()+abs(np.diff(x).mean())/2),float(y.min()-abs(np.diff(y).mean())/2),float(y.max()+abs(np.diff(y).mean())/2))
