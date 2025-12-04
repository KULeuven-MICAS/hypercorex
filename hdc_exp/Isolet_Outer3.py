from isolet_recog import main
import json
import sys

hv_dims = [2048, 10000]
hv_types = ["binary", "bipolar"]
# quant_types = [None, 'INT8', 'INT4', 'INT2', 'FP8_E4M3', 'FP8_E5M2', 'FP6_E2M3', 'FP6_E3M2', 'FP4_E2M1']
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

# hv_dims = [500]
# hv_types = ['bipolar', 'binary']
# quant_types = [None]


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
                print(f"Tread {i}: {round(count/tot*100,2)}%")
    with open(f"result_isolet_{i}.json", "w") as f:
        json.dump(result_dict, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        outer(99)
    else:
        outer(sys.argv[1])


# def run_experiment(i):
#     result_dict = {}
#     futures = {}

#     # inner parallelism via multiprocessing
#     with ProcessPoolExecutor(max_workers=4) as inner_pool:
#         for hv_dim in hv_dims:
#             for hv_type in hv_types:
#                 for quant_type in quant_types:
#                     f = inner_pool.submit(worker, i, hv_dim, hv_type, quant_type)
#                     futures[f] = (hv_dim, hv_type, quant_type)

#         for f in as_completed(futures):
#             hv_dim, hv_type, quant_type = futures[f]
#             key = f"{hv_dim} {hv_type} {quant_type}"
#             result_dict[key] = f.result()

#     # save each experiment to its own file
#     print(i)
#     with open(f"result_lang_{i}.json", "w") as f:
#         json.dump(result_dict, f, indent=2)

#     return i


# # === Outer parallelism (also multiprocessing) ===
# if __name__ == "__main__":   # REQUIRED for multiprocessing on Windows/macOS
#     start = time.time()
#     with ProcessPoolExecutor(max_workers=1) as outer_pool:
#         futures = [outer_pool.submit(run_experiment, i) for i in range(repeats)]

#         for f in as_completed(futures):
#             print(f"Experiment {f.result()} finished")
#     end = time.time()
#     print(f'\nThis took: {end-start:.2f} seconds')


# from lang_recog import main
# import matplotlib.pyplot as plt
# import json
# from concurrent.futures import ThreadPoolExecutor, as_completed

# # hv_dims = [2048, 8192]
# # hv_types = ['binary', 'bipolar']
# # quant_types = [None, 'INT8', 'INT4', 'INT2', 'FP8_E4M3', 'FP8_E5M2', 'FP6_E2M3', 'FP6_E3M2', 'FP4_E2M1']
# repeats = 2

# hv_dims = [64]
# hv_types = ['binary', 'bipolar']
# quant_types = [None, 'INT8']

# def worker(i, hv_dim, hv_type, quant_type):
#     print(f"Task {i}_{hv_dim}_{hv_type}_{quant_type} starting")
#     result = main(hv_dim=hv_dim, hv_type=hv_type, quant_type=quant_type)
#     print(f"Task {i}_{hv_dim}_{hv_type}_{quant_type} done")
#     return result


# def run_experiment(i):
#     result_dict = {}
#     futures = {}

#     # inner parallelism
#     with ThreadPoolExecutor(max_workers=10) as inner_pool:
#         for hv_dim in hv_dims:
#             for hv_type in hv_types:
#                 for quant_type in quant_types:
#                     f = inner_pool.submit(worker, i, hv_dim, hv_type, quant_type)
#                     futures[f] = (hv_dim, hv_type, quant_type)

#         for f in as_completed(futures):
#             hv_dim, hv_type, quant_type = futures[f]
#             key = f"{hv_dim} {hv_type} {quant_type}"
#             result_dict[key] = f.result()

#     # save each experiment to its own file
#     with open(f"hdc_exp/result_lang_{i}.json", "w") as f:
#         json.dump(result_dict, f, indent=2)

#     return i


# # === Outer parallelism over i ===
# with ThreadPoolExecutor(max_workers=3) as outer_pool:
#     futures = [outer_pool.submit(run_experiment, i) for i in range(repeats)]

#     for f in as_completed(futures):
#         print(f"Experiment {f.result()} finished")


# for i in range(0, 10):
#     tot_count = len(hv_dims)*len(hv_types)*len(quant_types)
#     k = 0

#     result_dict = {}
#     for hv_dim in hv_dims:
#         for hv_type in hv_types:
#             for quant_type in quant_types:
#                 result_dict[str(hv_dim)+' '+str(hv_type)+' '+str(quant_type)] = main(hv_dim=hv_dim, hv_type=hv_type, quant_type=quant_type)
#                 k+=1
#                 print(str(round(k/tot_count*100,2))+"%")


#     print(result_dict)
#     # Save to a file
#     with open(f"hdc_exp/result_lang_{i}.json", "w") as f:
#         json.dump(result_dict, f)
