from scipy.stats import gaussian_kde
from scipy.stats import skew

def get_norm_kde(s, bins):
    kernel = gaussian_kde(s)
    kde = kernel(bins)
    return list(kde / kde.sum())

def get_kde(s, bins):
    kernel = gaussian_kde(s)
    kde = kernel(bins)
    return list(kde)
