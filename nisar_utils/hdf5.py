# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
import h5py

@contextmanager
def open_h5(filename, mode="r"):
    with h5py.File(filename, mode) as f:
        yield f

open_hdf5 = open_h5

def safe_visititems(group, callback, _prefix="", _seen=None):
    """Walk an HDF5 group and call callback(name, obj) for every child, the
    same way h5py's Group.visititems does — except it doesn't use h5py's
    low-level h5o.visit() internally.

    h5o.visit() aborts the *entire* traversal with
    ``RuntimeError: Object visitation failed (unable to determine object
    type)`` the moment it hits a single object it can't resolve — most often
    a dangling soft/external link, but sometimes a committed datatype or
    region reference. Real NISAR products are large enough, and carry enough
    auxiliary metadata, that this shows up in practice. This walker resolves
    each child individually and just skips the ones that don't resolve,
    instead of failing the whole file.
    """
    if _seen is None:
        _seen = set()
    try:
        keys = list(group.keys())
    except Exception:
        return
    for key in keys:
        name = f"{_prefix}/{key}" if _prefix else key
        try:
            obj = group[key]
        except Exception:
            # Broken link or an object type h5py can't resolve — skip it
            # rather than letting it take down the whole traversal.
            continue
        obj_id = obj.id.__hash__() if hasattr(obj, "id") else id(obj)
        if obj_id in _seen:
            continue
        _seen.add(obj_id)
        callback(name, obj)
        if isinstance(obj, h5py.Group):
            safe_visititems(obj, callback, name, _seen)

def list_tree(h5, path="/", depth=None):
    if isinstance(path, int):
        depth, path = path, "/"
    path = str(path)
    if path not in h5:
        raise KeyError(f"HDF5 path does not exist: {path}")
    obj = h5[path]
    result = [(path, "GROUP" if isinstance(obj, h5py.Group) else "DATASET")]
    if not isinstance(obj, h5py.Group):
        return result
    base = path.strip("/").count("/") if path != "/" else 0
    def visit(name, child):
        full = "/" + name
        d = full.strip("/").count("/")
        if depth is None or d - base <= depth:
            result.append((full, "GROUP" if isinstance(child, h5py.Group) else "DATASET"))
    safe_visititems(obj, visit)
    seen=set()
    return [(p,k) for p,k in result if not (p in seen or seen.add(p))]

def inspect_dataset(h5, dataset_path):
    d=h5[dataset_path]
    attrs={}
    for k,v in d.attrs.items():
        try: attrs[k]=v.tolist()
        except AttributeError: attrs[k]=v
    info={
        "path": dataset_path,
        "shape": tuple(d.shape),
        "dtype": str(d.dtype),
        "chunks": d.chunks,
        "compression": d.compression,
        "compression_options": d.compression_opts,
        "attributes": attrs,
    }
    print("="*70)
    print("Dataset:",dataset_path)
    print("Shape:",d.shape)
    print("Datatype:",d.dtype)
    print("Chunks:",d.chunks)
    print("Compression:",d.compression)
    if d.compression: print("Compression options:",d.compression_opts)
    print("\nAttributes:")
    for k,v in d.attrs.items(): print(f"  {k}: {v}")
    return info
