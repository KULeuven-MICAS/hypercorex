from isolet_recog import main
import json
import sys

hv_dims = [2048, 10000]
hv_types = ["binary", "bipolar"]

quant_types = [
    None,
    "INT2_alt",
    "INT4_alt",
    "INT8_alt",
    "INT8",
    "INT4",
    "INT2",
    "FP8_E4M3",
    "FP8_E5M2",
    "FP6_E2M3",
    "FP6_E3M2",
    "FP4_E2M1",
    "FP4_E2M1_alt",
]


def worker(i, hv_dim, hv_type, quant_type):
    print(f"Task {i}_{hv_dim}_{hv_type}_{quant_type} starting")
    result = main(hv_dim=hv_dim, hv_type=hv_type, quant_type=quant_type)
    print(f"Task {i}_{hv_dim}_{hv_type}_{quant_type} done")
    return result


def outer(i):
    result_dict = {}
    tot = len(hv_dims) * len(hv_types) * len(quant_types)
    count = 0
    for hv_dim in hv_dims:
        for hv_type in hv_types:
            for quant_type in quant_types:
                result_dict[f"{hv_dim} {hv_type} {quant_type}"] = worker(
                    i, hv_dim, hv_type, quant_type
                )
                count += 1
                print(f"Tread {i}: {round(count / tot * 100, 2)}%")
    with open(f"result_isolet_{i}.json", "w") as f:
        json.dump(result_dict, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        outer(99)
    else:
        outer(sys.argv[1])
