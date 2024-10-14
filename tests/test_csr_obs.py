"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This test checks if the observable
  ports are functioning as intended.
"""

import set_parameters
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer
import pytest

from util import setup_and_run, check_result, clock_and_time


# Clear inputs first
def clear_inputs_no_clock(dut):
    dut.csr_req_data_i.value = 0
    dut.csr_req_addr_i.value = 0
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 0
    return


# Writing to csr registers
async def write_csr(dut, data, addr):
    clear_inputs_no_clock(dut)
    dut.csr_req_data_i.value = data
    dut.csr_req_addr_i.value = addr
    dut.csr_req_write_i.value = 1
    dut.csr_req_valid_i.value = 1
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return


# Reading from csr
# But simulate how to read combinationally
async def read_csr(dut, addr):
    clear_inputs_no_clock(dut)
    dut.csr_req_addr_i.value = addr
    dut.csr_req_write_i.value = 0
    dut.csr_req_valid_i.value = 1
    # Propagate time to get combinationally
    await Timer(1, units="ps")
    csr_val = dut.csr_rsp_data_o.value.integer
    # Propagate time to finish task
    await clock_and_time(dut.clk_i)
    clear_inputs_no_clock(dut)
    return csr_val


# Some parameters for use
MAX_REG_VAL = (2**set_parameters.REG_FILE_WIDTH) - 1
MAX_8B_VAL = (2**8) - 1


@cocotb.test()
async def csr_obs_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("                  CSR Set                   ")
    cocotb.log.info(" ------------------------------------------ ")

    # Initialize input values
    clear_inputs_no_clock(dut)
    dut.rst_ni.value = 0

    # Initialize other signals
    # Put these to 1 for value checking
    dut.csr_busy_i.value = 1
    dut.csr_am_pred_i.value = 0
    dut.csr_am_pred_valid_i.value = 0
    dut.csr_inst_pc_i.value = 0
    dut.csr_inst_at_addr_i.value = 0

    # Assume that host side is always ready
    dut.csr_rsp_ready_i.value = 1

    # Initialize clock always
    clock = Clock(dut.clk_i, 10, units="ns")
    cocotb.start_soon(clock.start(start_high=False))

    # Wait one cycle for reset
    await clock_and_time(dut.clk_i)

    dut.rst_ni.value = 1

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Check Core Setting              ")
    cocotb.log.info(" ------------------------------------------ ")

    # First check default state of observable pins
    obs_signal = dut.csr_obs_logic_o.value
    check_result(obs_signal, 0b0000)
    print(f"Observable signal: {obs_signal}")

    # Write unto the lower 2 bits and check if it's correct
    await write_csr(dut, 0b11, set_parameters.OBSERVABLE_REG_DATA)
    obs_signal = dut.csr_obs_logic_o.value
    check_result(obs_signal, 0b0011)
    print(f"Observable signal: {obs_signal}")

    # Do a start sequence to see if 2 MSB changed
    await write_csr(dut, 0b1, set_parameters.CORE_SET_REG_ADDR)
    obs_signal = dut.csr_obs_logic_o.value
    check_result(obs_signal, 0b0111)
    print(f"Observable signal: {obs_signal}")

    # Trigger a busy signal
    dut.csr_busy_i.value = 0
    await clock_and_time(dut.clk_i)
    obs_signal = dut.csr_obs_logic_o.value
    check_result(obs_signal, 0b1111)
    print(f"Observable signal: {obs_signal}")

    # Do a clear and reset all to 0
    await write_csr(dut, 0b1000000, set_parameters.CORE_SET_REG_ADDR)
    obs_signal = dut.csr_obs_logic_o.value
    check_result(obs_signal, 0b0011)
    print(f"Observable signal: {obs_signal}")

    # Write instruction mode and see if observable signal changes
    await write_csr(dut, 0b10, set_parameters.INST_CTRL_REG_ADDR)
    await clock_and_time(dut.clk_i)
    obs_signal = dut.csr_obs_logic_o.value
    check_result(obs_signal, 0b1011)
    print(f"Observable signal: {obs_signal}")

    # This is for waveform checking later
    for i in range(set_parameters.TEST_RUNS):
        # Propagate time for logic
        await clock_and_time(dut.clk_i)


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "NumTotIm": str(set_parameters.NUM_TOT_IM),
            "NumPerImBank": str(set_parameters.NUM_PER_IM_BANK),
            "CsrDataWidth": str(set_parameters.REG_FILE_WIDTH),
            "CsrAddrWidth": str(set_parameters.REG_FILE_WIDTH),
            "InstMemDepth": str(set_parameters.INST_MEM_DEPTH),
        }
    ],
)
def test_csr_obs(simulator, parameters, waves):
    verilog_sources = [
        # Level 0
        "/rtl/csr/csr_addr_pkg.sv",
        # Level 1
        "/rtl/csr/csr.sv",
    ]

    toplevel = "csr"

    module = "test_csr_obs"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
