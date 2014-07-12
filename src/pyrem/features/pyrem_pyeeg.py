__author__ = 'quentin'

import numpy as np


def embed_seq(X,Tau,D):

    N =len(X)

    if D * Tau > N:
        raise ValueError("Cannot build such a matrix, because D * Tau > N")

    if Tau<1:
        raise ValueError("Tau has to be at least 1")


    Y=np.zeros((D, N - (D - 1) * Tau))

    for i in range(D):
        Y[i] = X[i *Tau : i*Tau + Y.shape[1] ]

    return Y.T

def pfd(X):
    """
    Compute Petrosian Fractal Dimension of a time series.
    Vectorised/optimised version of the eponymous function from PyEEG (https://code.google.com/p/pyeeg/).

    :param X: a one dimensional array representing a time series
    :type X: np.array
    :return: the Petrosian Fractal Dimension; a scalar
    :rtype: float

    """


    diff = np.diff(X)

    # x[i] * x[i-1] for i in t0 -> tmax
    prod = diff[1:-1] * diff[0:-2]

    #number of sign changes in derivative of the signal
    N_delta = np.sum(prod < 0)

    n = len(X)
    return np.log10(n)/(np.log10(n)+np.log10(n/n+0.4*N_delta))


def hjorth(X):

    first_deriv = np.diff(X)
    second_deriv = np.diff(X,2)

    var_zero = np.mean(X ** 2)
    var_d1 = np.mean(first_deriv ** 2)
    var_d2 = np.mean(second_deriv ** 2)


    activity = var_zero ** 2.0
    morbidity = var_d1 / var_zero
    complexity = np.abs(var_d2 / var_d1) - morbidity ** 2.0

    return activity, morbidity, complexity




def svd_entropy(X, Tau, DE):
    mat =  embed_seq(X, Tau, DE)
    W = np.linalg.svd(mat, compute_uv = False)
    W /= sum(W) # normalize singular values
    return -1*sum(W * np.log(W))


def fisher_info(X, Tau, DE):
    mat =  embed_seq(X, Tau, DE)
    W = np.linalg.svd(mat, compute_uv = False)
    W /= sum(W) # normalize singular values
    FI_v = (W[1:] - W[:-1]) **2 / W[:-1]

    return np.sum(FI_v)


def make_cmp(X, M, R, in_range_i, in_range_j):
     #Then we make Cmp
    Emp = embed_seq(X, 1, M + 1)
    inrange_cmp = np.abs(Emp[in_range_i,-1] - Emp[in_range_j,-1]) <= R
    # inrange_cmp_ij_arr = in_range_ij_arr[inrange_cmp]
    in_range_cmp_i = in_range_i[inrange_cmp]
    in_range_cmp_j = in_range_j[inrange_cmp]
    # Cmp = np.bincount(inrange_cmp_ij_arr.flatten(), minlength=N-M)
    Cmp = np.bincount(in_range_cmp_i, minlength=N-M)
    Cmp += np.bincount(in_range_cmp_j, minlength=N-M)
    return Cmp.astype(np.float)

def make_cm(X,M,R):
    N = len(X)

    # we pregenerate all indices
    i_idx,j_idx  = np.triu_indices(N - M)

    # We start by making Cm
    Em = embed_seq(X, 1, M)
    dif =  np.abs(Em[i_idx] - Em[j_idx])
    max_dist = np.max(dif, 1)
    inrange_cm = max_dist <= R


    in_range_i = i_idx[inrange_cm]
    in_range_j = j_idx[inrange_cm]

    Cm = np.bincount(in_range_i, minlength=N-M+1)
    Cm += np.bincount(in_range_j, minlength=N-M+1)

    inrange_last = np.max(np.abs(Em[:-1] - Em[-1]),1) <= R
    Cm[inrange_last] += 1
    # all matches + self match
    Cm[-1] += np.sum(inrange_last) + 1

    return Cm.astype(np.float), in_range_i, in_range_j

def ap_entropy(X, M, R):

    Cm, in_range_i, in_range_j = make_cm(X,M,R)

    Cmp = make_cmp(X, M, R, in_range_i, in_range_j)

    Cm /= float((N - M +1 ))
    Cmp /= float(N - M)
    Phi_m, Phi_mp = np.sum(np.log(Cm)),  np.sum(np.log(Cmp))
    Ap_En = (Phi_m - Phi_mp) / (N - M)
    return Ap_En







#
#
# def hfd_new(X, Kmax):
#     """ Compute Higuchi Fractal Dimension of a time series X, kmax
#      is an HFD parameter
#     """
#     L = []
#     x = []
#     N = len(X)
#     for k in range(1,Kmax):
#         Lk = []
#         for m in range(k):
#             max = int((N-m)/k)
#
#             diffs = X[m+k:len(X)-k+1:k]
#             #print np.sum(np.abs(diffs))
#             # print len(ar[m: :k])
#
#
#             print k,m,len(diffs)
#
#             Lmk = np.sum(np.abs(diffs))*(N - 1)/np.floor((N - m) / float(k)) / k
#             #print k,m, np.sum(np.abs(diffs)) / float(len(diffs))
#             Lk.append(Lmk)
#
#
#
#         L.append(np.log(np.mean(Lk)))
#         x.append([np.log(float(1) / k), 1])
#
#     # print L,x
#     (p, r1, r2, s)=np.linalg.lstsq(x, L)
#     return p[0]
#
#



def hfd(X, Kmax):
    """ Compute Higuchi Fractal Dimension of a time series X, kmax
     is an HFD parameter
    """
    L = []
    x = []
    N = len(X)
    for k in xrange(1,Kmax):
        Lk = []
        for m in xrange(0,k):
            Lmk = 0
            test = []

            for i in xrange(1,int(np.floor((N-m)/k))):
                test.append(X[m+i*k])
                Lmk += abs(X[m+i*k] - X[m+i*k-k])
            #print k,m, Lmk
            print k,m,len(test)
            # print k,m,Lmk
            Lmk = Lmk*(N - 1)/np.floor((N - m) / float(k)) / k
            Lk.append(Lmk)


        L.append(np.log(np.mean(Lk)))
        x.append([np.log(float(1) / k), 1])
    # print L,x
    (p, r1, r2, s)=np.linalg.lstsq(x, L)
    return p[0]

#
# ar = np.arange(100)
# hfd(ar, 10)
# print "==================="
# hfd_new(ar, 10)

# def hfd_exple(pow=10):
#     start = 1000
#     N = np.int64(2 **pow)
#     i=start
#     out = np.zeros((N))
#     while i < N + start:
#         out[i-start] = np.sum(np.random.normal(0,1,i))
#         i += 1
#     return out
#
# a = hfd_exple(15)


# hfd(a, 4)






