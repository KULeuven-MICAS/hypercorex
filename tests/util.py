'''
    Copyright 2024 KU Leuven
    Ryan Antonio <ryan.antonio@esat.kuleuven.be>

    Description:
    This contains useful functions for managing
    the tests, script,s and generations
'''

# Importing useful tools
import subprocess
import random
from cocotb_test.simulator import run

'''
    Set of functions for test setups
'''


# For getting the root of the repository
def get_git_root():
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


# Setup and run functions
# Extracts necessary definitions and filelists
# Then invokes the run simulator
def setup_and_run(verilog_sources=None,
                  defines=None,
                  includes=None,
                  toplevel="",
                  module="",
                  simulator="verilator",
                  parameters=None):

    # Extract global main root
    git_repo_root = get_git_root()

    # Set tests path, we use this by default
    tests_path = git_repo_root + "/tests"

    # Set the simulation build within test directory
    sim_build = tests_path + "/sim_build/{}/".format(toplevel)

    # Append git repo root for all items
    for i in range(len(verilog_sources)):
        verilog_sources[i] = git_repo_root + verilog_sources[i]

    # Setting of compilation arguments
    # and timescale depending on simulator
    if simulator == "verilator":
        compile_args = [
            "-Wno-WIDTH",
            "--timing",
            "--trace-structs"
        ]
        timescale = None
    else:
        compile_args = None
        timescale = "1ns/1ps"

    run(
        verilog_sources=verilog_sources,
        includes=includes,
        toplevel=toplevel,
        defines=defines,
        module=module,
        simulator=simulator,
        sim_build=sim_build,
        compile_args=compile_args,
        timescale=timescale,
        waves=True,
        parameters=parameters,
    )


'''
    Set of functions for data generation
'''


# For generating random bits
def gen_rand_bits(dimension):
    return random.getrandbits(dimension)
