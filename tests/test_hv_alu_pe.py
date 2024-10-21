"""
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality of the
  hypervector ALU with basic operations
"""

import set_parameters
from util import setup_and_run, gen_rand_bits, gen_randint, hv_alu_out

import cocotb
from cocotb.triggers import Timer
import pytest


# Routinary test
async def gen_and_test(dut, hv_dim, shift_amt, mode):
    # Generate data
    if mode == 3 or mode == 4:
        A = gen_rand_bits(set_parameters.HV_DIM)
        B = 0
        shift_amt = gen_randint(shift_amt)
    else:
        A = gen_rand_bits(set_parameters.HV_DIM)
        B = gen_rand_bits(set_parameters.HV_DIM)
        shift_amt = 0

    gold_result = hv_alu_out(A, B, shift_amt, hv_dim, mode)

    # Feed inputs
    dut.A_i.value = A
    dut.B_i.value = B
    dut.shift_amt_i.value = shift_amt
    dut.op_i.value = mode

    # Let time pass for logic to evaluate
    await Timer(1, units="ps")

    # Log data
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info(f" Mode: { dut.op_i.value.integer}")
    cocotb.log.info(f" Input A: {dut.A_i.value.integer}")
    cocotb.log.info(f" Input B: {dut.B_i.value.integer}")
    cocotb.log.info(f" Shift Amount: {dut.shift_amt_i.value.integer}")
    cocotb.log.info(f" Golden Out: {gold_result}")
    cocotb.log.info(f" Actual Out: {dut.C_o.value.integer}")
    cocotb.log.info(" ------------------------------------------ ")

    # Check if result is correct
    assert gold_result == dut.C_o.value.integer, "Error! Output mismatch!"
    return


@cocotb.test()
async def hv_alu_pe_dut(dut):
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("            Testing ALU HV Cases            ")
    cocotb.log.info(" ------------------------------------------ ")

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing XOR Cases              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Test the XOR case
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(dut, set_parameters.HV_DIM, 0, 0)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing AND Cases              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Test the AND case
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(dut, set_parameters.HV_DIM, 0, 1)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing OR Cases               ")
    cocotb.log.info(" ------------------------------------------ ")

    # Test the OR case
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(dut, set_parameters.HV_DIM, 0, 2)

    cocotb.log.info(" ------------------------------------------------ ")
    cocotb.log.info("       Testing Circular Right Shift Cases         ")
    cocotb.log.info(" ------------------------------------------------ ")

    # Test circular shift cases
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(
            dut, set_parameters.HV_DIM, set_parameters.MAX_SHIFT_AMT - 1, 3
        )

    cocotb.log.info(" ------------------------------------------------ ")
    cocotb.log.info("        Testing Circular Left Shift Cases         ")
    cocotb.log.info(" ------------------------------------------------ ")

    # Test circular shift cases
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(
            dut, set_parameters.HV_DIM, set_parameters.MAX_SHIFT_AMT - 1, 4
        )


# Actual test run
@pytest.mark.parametrize(
    "parameters",
    [
        {
            "HVDimension": str(set_parameters.HV_DIM),
            "MaxShiftAmt": str(set_parameters.MAX_SHIFT_AMT),
        }
    ],
)
def test_hv_alu_pe(simulator, parameters, waves):
    verilog_sources = ["/rtl/encoder/hv_alu_pe.sv"]

    toplevel = "hv_alu_pe"

    module = "test_hv_alu_pe"

    setup_and_run(
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        simulator=simulator,
        parameters=parameters,
        waves=waves,
    )
