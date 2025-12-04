import numpy as np


def fp864_quantize(x, mode="E4M3", overflow="SAT"):
    x = np.asarray(x, dtype=np.float32)
    sign_bit = (x < 0).astype(np.uint8)
    abs_x = np.abs(x)

    # ---- format parameters (from OCP spec) ----
    if mode == "E4M3":
        exp_bits, man_bits, bias = 4, 3, 7
        max_norm, min_norm, min_sub = 448.0, 2**-6, 2**-9
        nan_code = 0b01111111
    elif mode == "E5M2":
        exp_bits, man_bits, bias = 5, 2, 15
        max_norm, min_norm, min_sub = 57344.0, 2**-14, 2**-16
        nan_code = 0b01111101
    elif mode == "E2M3":
        exp_bits, man_bits, bias = 2, 3, 1
        max_norm, min_norm, min_sub = 7.5, 1.0, 0.125
        nan_code = None
    elif mode == "E3M2":
        exp_bits, man_bits, bias = 3, 2, 1
        max_norm, min_norm, min_sub = 28.0, 0.25, 0.0625
        nan_code = None
    elif mode == "E2M1":
        exp_bits, man_bits, bias = 2, 1, 1
        max_norm, min_norm, min_sub = 6.0, 1.0, 0.5
        nan_code = None
    else:
        raise ValueError("mode must be 'E4M3' or 'E5M2'")

    # Initialize
    q = np.zeros_like(abs_x, dtype=np.float32)
    encoded = np.zeros_like(abs_x, dtype=np.uint8)

    # Masks
    isnan = np.isnan(x)
    isinf = np.isinf(x)
    finite = ~(isnan | isinf)

    # Handle NaNs
    if mode != "E2M1" and mode != "E2M3" and mode != "E3M2":
        encoded[isnan] = nan_code
        q[isnan] = np.nan

    # Handle Infs
    if overflow.upper() == "SAT":
        q[isinf] = np.sign(x[isinf]) * max_norm
    else:  # OVF
        q[isinf] = np.nan
        encoded[isinf] = nan_code

    # Finite values
    finite_x = abs_x[finite]
    finite_sign = sign_bit[finite]

    # Clip to representable range
    finite_x = np.clip(finite_x, 0, max_norm)

    # Subnormal region
    sub_mask = (finite_x < min_norm) & (finite_x >= min_sub)
    norm_mask = finite_x >= min_norm
    zero_mask = finite_x < min_sub

    E = np.zeros_like(finite_x, dtype=np.uint8)
    M = np.zeros_like(finite_x, dtype=np.uint8)
    q_f = np.zeros_like(finite_x, dtype=np.float32)

    # ---- Normal numbers ----
    if np.any(norm_mask):
        xn = finite_x[norm_mask]
        exp = np.floor(np.log2(xn))
        mant = xn / (2**exp) - 1.0
        mant_q = np.round(mant * (2**man_bits)) / (2**man_bits)
        q_norm = (1.0 + mant_q) * (2.0**exp)
        q_norm = np.clip(q_norm, 0, max_norm)

        E[norm_mask] = np.uint8(exp + bias)
        M[norm_mask] = np.uint8(np.round(mant_q * (2**man_bits)))
        q_f[norm_mask] = q_norm

    # ---- Subnormals ----
    if np.any(sub_mask):
        xs = finite_x[sub_mask]
        M[sub_mask] = np.uint8(np.round(xs / min_norm * (2**man_bits)))
        q_f[sub_mask] = (M[sub_mask].astype(np.float32) / (2**man_bits)) * min_norm

    # ---- Zeros ----
    q_f[zero_mask] = 0.0
    E[zero_mask] = 0
    M[zero_mask] = 0

    # ---- Encode bitfields ----
    encoded_finite = (finite_sign << (exp_bits + man_bits)) | (E << man_bits) | M
    encoded[finite] = encoded_finite

    q[finite] = q_f * np.where(finite_sign == 1, -1.0, 1.0)

    # Saturate out-of-range finite values
    over_mask = (abs_x > max_norm) & finite
    if np.any(over_mask):
        if overflow.upper() == "SAT":
            q[over_mask] = np.sign(x[over_mask]) * max_norm
        else:
            q[over_mask] = np.nan
            encoded[over_mask] = nan_code

    return q.astype(np.float32)  # , encoded
