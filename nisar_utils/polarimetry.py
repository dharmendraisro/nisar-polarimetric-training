# SPDX-License-Identifier: Apache-2.0
"""Subset-safe polarimetric utilities for NISAR L2 GCOV.

The module keeps the large source HDF5 product on disk and operates on a
participant-selected AOI/window.  Complex off-diagonal covariance terms are
never converted to magnitude-only values before matrix reconstruction.
"""
from __future__ import annotations
import numpy as np


def safe_complex(a):
    return np.asarray(a, dtype=np.complex64)


def estimate_polarimetric_ram(shape, n_complex_terms=6, dtype=np.complex64, safety_factor=1.5):
    """Approximate working RAM in bytes for selected complex terms plus products."""
    n = int(np.prod(shape))
    item = np.dtype(dtype).itemsize
    raw = n * n_complex_terms * item
    # Matrix reconstruction/eigen/decomposition intermediates are conservatively budgeted.
    return int(raw * safety_factor)


def polarimetric_memory_guard(shape, n_complex_terms=6, ram_gb=16.0, reserve_gb=4.0,
                              science_fraction=0.45):
    """Return a participant-facing AOI guard for a 16-GB laptop workflow."""
    estimate = estimate_polarimetric_ram(shape, n_complex_terms)
    budget = max((ram_gb - reserve_gb) * science_fraction, 0.5) * 1024**3
    ok = estimate <= budget
    return {"shape": tuple(shape), "estimated_bytes": estimate,
            "estimated_gb": estimate/1024**3, "budget_gb": budget/1024**3,
            "safe": bool(ok), "recommendation": "Proceed with this AOI" if ok else
            "Reduce AOI (try 1024x1024 or smaller) before loading polarimetric terms"}


def covariance_hermitian_from_terms(terms, mode="full3"):
    """Build the raw 3x3 [HH,HV,VV] covariance from NISAR GCOV terms."""
    t = {k: safe_complex(v) for k, v in terms.items()}
    req = ["HHHH", "HVHV", "VVVV"]
    missing = [k for k in req if k not in t]
    if missing:
        raise KeyError(f"Missing required full-pol diagonal terms: {missing}")
    z = np.zeros_like(t["HHHH"], dtype=np.complex64)
    C = np.empty(t["HHHH"].shape + (3, 3), dtype=np.complex64)
    C[...,0,0] = t["HHHH"].real
    C[...,1,1] = t["HVHV"].real
    C[...,2,2] = t["VVVV"].real
    c01 = t.get("HHHV", np.conj(t.get("HHVH", z)))
    c02 = t.get("HHVV", z)
    c12 = t.get("HVVV", np.conj(t.get("VHVV", z)))
    C[...,0,1], C[...,1,0] = c01, np.conj(c01)
    C[...,0,2], C[...,2,0] = c02, np.conj(c02)
    C[...,1,2], C[...,2,1] = c12, np.conj(c12)
    return C


def nisar_c3_to_standard_c3(Craw):
    """Convert raw [HH,HV,VV] covariance to the common Pauli/T3 normalization.

    The cross-pol vector element is sqrt(2)*HV, hence row/column 2 are scaled
    by sqrt(2). This makes trace(C3) = |HH|^2 + 2|HV|^2 + |VV|^2.
    """
    C = np.asarray(Craw, dtype=np.complex64).copy()
    C[..., :, 1] *= np.sqrt(2.0)
    C[..., 1, :] *= np.sqrt(2.0)
    return C


def standard_c3_to_t3(C):
    """Convert standard lexicographic C3 [HH,sqrt(2)HV,VV] to Pauli T3.

    The unitary Pauli basis is [HH+VV, HH-VV, 2HV]/sqrt(2).
    Consequently the C3 and T3 matrices have identical eigenvalues and span.
    """
    C11, C22, C33 = C[...,0,0].real, C[...,1,1].real, C[...,2,2].real
    C12, C13, C23 = C[...,0,1], C[...,0,2], C[...,1,2]
    T = np.empty_like(C)
    T[...,0,0] = 0.5*(C11 + C33 + 2*np.real(C13))
    T[...,1,1] = 0.5*(C11 + C33 - 2*np.real(C13))
    T[...,2,2] = C22
    T[...,0,1] = 0.5*(C11-C33 - 2j*np.imag(C13)); T[...,1,0] = np.conj(T[...,0,1])
    # C is Hermitian, so the Pauli transform uses C32 = conj(C23)
    # in the terms coupling the Pauli co- and cross-pol components.
    # Keeping C23 without conjugation is only accidentally correct when
    # that off-diagonal term is purely real; real NISAR full-pol GCOV
    # contains genuinely complex covariance terms.
    C32 = np.conj(C23)
    T[...,0,2] = (C12 + C32)/np.sqrt(2); T[...,2,0] = np.conj(T[...,0,2])
    T[...,1,2] = (C12 - C32)/np.sqrt(2); T[...,2,1] = np.conj(T[...,1,2])
    return T


def pauli_powers(Craw_or_standard, standard=False):
    """Return Pauli scattering powers P1,P2,P3 and total span."""
    C = np.asarray(Craw_or_standard)
    if not standard:
        C = nisar_c3_to_standard_c3(C)
    T = standard_c3_to_t3(C)
    p1 = np.maximum(T[...,0,0].real, 0)
    p2 = np.maximum(T[...,1,1].real, 0)
    p3 = np.maximum(T[...,2,2].real, 0)
    return {"pauli_1":p1, "pauli_2":p2, "pauli_3":p3, "span":p1+p2+p3}


def hermitian_error(C):
    return np.abs(C-np.swapaxes(np.conj(C),-1,-2))


def hermitian_relative_error(C, eps=1e-12):
    num=np.linalg.norm(C-np.swapaxes(np.conj(C),-1,-2),axis=(-2,-1))
    den=np.linalg.norm(C,axis=(-2,-1))+eps
    return num/den


def eigen_analysis(C, clip_negative=False):
    """Eigen analysis for a Hermitian 3x3 polarimetric matrix.

    For Cloude-Pottier processing, pass the Pauli coherency matrix T3, not the
    unnormalised raw NISAR lexicographic covariance.

    Pixels with any NaN entry (MASK == 0 pixels are NaN by the time this is
    called) are handled explicitly. np.linalg.eigh operates on the whole
    batch of 3x3 matrices in one call, and on some LAPACK backends a
    single NaN-containing matrix anywhere in that batch makes the *entire*
    call raise LinAlgError("Eigenvalues did not converge") instead of just
    returning NaN for the affected pixel -- which would otherwise crash
    this function (and Modules 15/16, which call it directly) on any real
    product with even one transmit-gap pixel in the AOI. Invalid matrices
    are substituted with the identity (guaranteed to converge) before the
    batched eigh call, and every output is explicitly restored to NaN for
    those pixels afterward -- the `where=` guards below produce 0, not
    NaN, for a span of NaN, which would otherwise misreport an invalid
    pixel as having exactly zero entropy/anisotropy.
    """
    H=0.5*(C+np.swapaxes(np.conj(C),-1,-2))
    invalid = ~np.all(np.isfinite(H), axis=(-2,-1))
    if np.any(invalid):
        H = np.where(invalid[...,None,None], np.eye(H.shape[-1], dtype=H.dtype), H)
    w,v=np.linalg.eigh(H); w=w[...,::-1]; v=v[..., :, ::-1]
    if np.any(invalid):
        w = np.where(invalid[...,None], np.nan, w)
        v = np.where(invalid[...,None,None], np.nan, v)
    if clip_negative: w=np.maximum(w,0)
    with np.errstate(divide="ignore", invalid="ignore"):
        span=np.sum(w,axis=-1)
        p=np.divide(w,span[...,None],out=np.zeros_like(w),where=span[...,None]>0)
        Hent=-np.sum(np.where(p>0,p*np.log(p)/np.log(3),0),axis=-1)
        A=np.divide(w[...,1]-w[...,2],w[...,1]+w[...,2],out=np.zeros_like(span),where=(w[...,1]+w[...,2])>0)
    if np.any(invalid):
        span = np.where(invalid, np.nan, span)
        p = np.where(invalid[...,None], np.nan, p)
        Hent = np.where(invalid, np.nan, Hent)
        A = np.where(invalid, np.nan, A)
    return {"eigenvalues":w,"eigenvectors":v,"span":span,"probabilities":p,"entropy":Hent,"anisotropy":A}


def cloude_pottier_alpha(eigenvectors):
    """Return the three Cloude-Pottier alpha_i angles from Pauli-basis T3 eigenvectors."""
    return np.arccos(np.clip(np.abs(eigenvectors[...,0,:]),0,1))


def cloude_pottier_mean_alpha(eigenvectors, probabilities):
    """Return the entropy-weighted mean alpha angle, in radians.

    The standard Cloude-Pottier definition is a weighted SUM,
    alpha_mean = sum_i(p_i * alpha_i), since the p_i (from eigen_analysis)
    already sum to 1 and serve directly as the weights -- no further
    averaging is needed. Using np.mean/np.nanmean here instead of a sum
    silently divides the correct answer by 3 (the number of eigenvalues),
    which is exactly the bug this function replaces: two notebook cells
    (Modules 16 and 19) had it inline as `nanmean(alpha_i * p_i)`, each
    computing 15 degrees for a case where the correct answer is 45.

    A masked pixel (NaN eigenvectors/probabilities from eigen_analysis)
    has all three alpha_i*p_i terms as NaN together, so a plain np.sum
    already propagates NaN correctly for that pixel without needing
    nansum or emitting numpy's "Mean of empty slice" warning.
    """
    return np.sum(cloude_pottier_alpha(eigenvectors) * probabilities, axis=-1)


def fullpol_freeman_durden(Craw, eps=1e-10, normalize=True):
    """Freeman-Durden 3-component powers on a subset.

    Uses the standard normalized C3 convention where the cross-pol element is
    sqrt(2)*HV. Negative component powers are clipped and positive components
    are rescaled to the observed span when necessary.
    """
    C = nisar_c3_to_standard_c3(Craw) if normalize else np.asarray(Craw)
    c11=np.real(C[...,0,0]); c22=np.real(C[...,1,1]); c33=np.real(C[...,2,2]); c13=C[...,0,2]
    fv=4.0*c22
    a11=np.maximum(c11-3.0*fv/8.0, eps)
    a33=np.maximum(c33-3.0*fv/8.0, eps)
    c13p=c13-fv/8.0
    mag=np.abs(c13p); lim=np.sqrt(a11*a33)
    scale=np.minimum(1.0, np.divide(lim, np.maximum(mag,eps)))
    c13p=c13p*scale
    fs=np.zeros_like(a11); fd=np.zeros_like(a11); alpha=np.zeros_like(c13p); beta=np.zeros_like(a11)
    pos=np.real(c13p) >= 0
    # Rough-surface dominant branch: alpha=-1
    beta[pos]=np.divide(a11[pos]+np.real(c13p[pos]), a33[pos]+np.real(c13p[pos]), out=np.zeros_like(a11[pos]), where=np.abs(a33[pos]+np.real(c13p[pos]))>eps)
    fs[pos]=np.maximum(0, np.real(np.divide(a33[pos]+np.real(c13p[pos]), 1+beta[pos], out=np.zeros_like(a11[pos],dtype=float), where=np.abs(1+beta[pos])>eps)))
    fd[pos]=np.maximum(0,a33[pos]-fs[pos])
    alpha[pos]=-1
    # Double-bounce dominant branch: beta=1
    neg=~pos
    beta[neg]=1
    den=np.conj(c13p[neg])-a33[neg]
    alpha[neg]=np.divide(a11[neg]-c13p[neg], den, out=np.zeros_like(c13p[neg]), where=np.abs(den)>eps)
    fd[neg]=np.maximum(0,np.real(np.divide(a33[neg]-np.real(c13p[neg]), 1-np.real(alpha[neg]), out=np.zeros_like(a33[neg]), where=np.abs(1-np.real(alpha[neg]))>eps)))
    fs[neg]=np.maximum(0,a33[neg]-fd[neg])
    Ps=fs*(1+np.abs(beta)**2); Pd=fd*(1+np.abs(alpha)**2); Pv=np.maximum(fv,0)
    span=np.maximum(np.real(C[...,0,0]+C[...,1,1]+C[...,2,2]),0)
    total=Ps+Pd+Pv
    scale2=np.divide(span,total,out=np.ones_like(span),where=total>eps)
    Ps*=scale2; Pd*=scale2; Pv*=scale2
    return {"surface":Ps,"double_bounce":Pd,"volume":Pv,"span":span,"residual":span-(Ps+Pd+Pv),"alpha":alpha,"beta":beta}


def fullpol_yamaguchi4(Craw, volume_model="auto", eps=1e-10):
    """Educational Yamaguchi-4 component implementation.

    The algorithm explicitly extracts helix power from T3, selects one of the
    standard oriented volume covariance models, subtracts those terms, then
    applies the Freeman surface/double-bounce partition to the residual.
    It returns a reconstruction residual so the participant can reject pixels
    where the model assumptions are poor.
    """
    C=nisar_c3_to_standard_c3(Craw); T=standard_c3_to_t3(C)
    # Helix power in the common T3 convention.
    pc=2*np.abs(np.imag(T[...,1,2])); helix=np.zeros_like(T)
    # Helix normalized matrix has unit trace; sign is carried by Im(T23).
    sign=np.sign(np.imag(T[...,1,2])); sign=np.where(sign==0,1,sign)
    helix[...,1,1]=pc/2; helix[...,2,2]=pc/2
    helix[...,1,2]=1j*sign*pc/2; helix[...,2,1]=-1j*sign*pc/2
    Tres=T-helix
    # Work in C3 for the residual Freeman branch.
    Cres=np.empty_like(C)
    # inverse of standard C3 -> T3
    # vectorize via formulas using matrix transform U
    U=np.array([[1,0,1],[1,0,-1],[0,np.sqrt(2),0]],complex)/np.sqrt(2)
    # T = U C U^H => C = U^H T U
    Cres=np.einsum('ab,...bc,cd->...ad',np.conj(U).T,Tres,U)
    # volume model selection based on original co-pol ratio
    c11=np.real(C[...,0,0]); c33=np.real(C[...,2,2]); ratio=10*np.log10(np.maximum(c33,eps)/np.maximum(c11,eps))
    model=np.where(ratio>2.0,'vv_dominant',np.where(ratio<-2.0,'hh_dominant','symmetric')) if volume_model=='auto' else np.full(c11.shape,volume_model)
    # Models are normalized to unit trace and positive semidefinite.
    Vsym=np.array([[3,0,1],[0,2,0],[1,0,3]],float)/8
    Vhh=np.array([[8,0,2],[0,4,0],[2,0,3]],float)/15
    Vvv=np.array([[3,0,2],[0,4,0],[2,0,8]],float)/15
    V=np.zeros(Cres.shape, dtype=np.float64)
    for mask,Vm in [(model=='symmetric',Vsym),(model=='hh_dominant',Vhh),(model=='vv_dominant',Vvv)]:
        V[mask]=Vm
    pv=np.maximum(np.real(Tres[...,0,0]*0+np.trace(Tres,axis1=-2,axis2=-1)),0) # initial available power
    # Estimate volume from T22 using model's middle element, then subtract.
    v22=V[...,1,1]
    pv=np.maximum(np.divide(np.real(Tres[...,1,1]),np.maximum(v22,eps)),0)
    Tv=V*pv[...,None,None]
    Trem=Tres-Tv
    Crem=np.einsum('ab,...bc,cd->...ad',np.conj(U).T,Trem,U)
    # Freeman on residual; pass as standard C3 and disable normalization.
    fd=fullpol_freeman_durden(Crem,normalize=False)
    ps,pd=fd['surface'],fd['double_bounce']; residual_span=np.maximum(np.real(np.trace(Trem,axis1=-2,axis2=-1)),0)
    total=np.maximum(np.real(ps+pd+pv+pc),eps)
    observed=np.maximum(np.real(np.trace(T,axis1=-2,axis2=-1)),0)
    sc=np.real(np.divide(observed,total,out=np.ones_like(total),where=total>eps))
    ps*=sc; pd*=sc; pv*=sc; pc*=sc
    return {"surface":ps,"double_bounce":pd,"volume":pv,"helix":pc,"span":observed,
            "residual":observed-(ps+pd+pv+pc),"volume_model":model}


def stokes_from_compact_terms(rhrh,rhrv,rvrv):
    rr=np.real(rhrh); vv=np.real(rvrv); rv=safe_complex(rhrv)
    g0=rr+vv; g1=rr-vv; g2=2*np.real(rv); g3=2*np.imag(rv)
    return g0,g1,g2,g3


def compact_child_parameters(g0,g1,g2,g3,eps=1e-12, chirality_sign=-1):
    den=np.maximum(g0,eps)
    m=np.sqrt(np.maximum(g1*g1+g2*g2+g3*g3,0))/den; m=np.clip(m,0,1)
    s=chirality_sign*g3/np.maximum(m*g0,eps)
    chi2=np.arcsin(np.clip(s,-1,1))
    delta=np.arctan2(g3,g2)
    alpha=0.5*np.arctan2(np.sqrt(np.maximum(g1*g1+g2*g2,0)), chirality_sign*g3)
    return {"m":m,"chi2":chi2,"delta":delta,"alpha_s":alpha}


def m_chi_decomposition(g0,m,chi2):
    vol=np.maximum(g0*(1-m),0); dbl=np.maximum(0.5*g0*m*(1-np.sin(chi2)),0); surf=np.maximum(0.5*g0*m*(1+np.sin(chi2)),0)
    return {"double_bounce":dbl,"volume":vol,"surface":surf}

def m_delta_decomposition(g0,m,delta):
    vol=np.maximum(g0*(1-m),0); dbl=np.maximum(0.5*g0*m*(1-np.sin(delta)),0); surf=np.maximum(0.5*g0*m*(1+np.sin(delta)),0)
    return {"double_bounce":dbl,"volume":vol,"surface":surf}

def m_alpha_decomposition(g0,m,alpha_s):
    vol=np.maximum(g0*(1-m),0); dbl=np.maximum(0.5*g0*m*(1-np.cos(2*alpha_s)),0); surf=np.maximum(0.5*g0*m*(1+np.cos(2*alpha_s)),0)
    return {"double_bounce":dbl,"volume":vol,"surface":surf}

def decomposition_residual(g0,parts):
    return g0-sum(parts.values())
