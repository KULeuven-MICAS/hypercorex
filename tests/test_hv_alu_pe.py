'''
  Copyright 2024 KU Leuven
  Ryan Antonio <ryan.antonio@esat.kuleuven.be>

  Description:
  This tests the basic functionality of the
  hypervector ALU with basic operations
'''

import set_parameters
from util import setup_and_run, gen_rand_bits

import cocotb
from cocotb.triggers import Timer
import pytest


# ALU PE model
def hv_alu_pe_golden_out(A, B, mode):
    if (mode == 1):
        result = A & B
    elif (mode == 2):
        result = A | B
    else:
        result = A ^ B
    return result


# Routinary test
async def gen_and_test(dut, mode):

    # Generate data
    A = gen_rand_bits(set_parameters.HV_DIM)
    B = gen_rand_bits(set_parameters.HV_DIM)
    gold_result = hv_alu_pe_golden_out(A, B, mode)

    # Feed inputs
    dut.A_i.value = A
    dut.B_i.value = B
    dut.op_i.value = mode

    # Let time pass for logic to evaluate
    await Timer(1, units="ps")

    # Log data
    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info(f" Mode: { dut.op_i.value.integer}")
    cocotb.log.info(f" Input A: {dut.A_i.value.integer}")
    cocotb.log.info(f" Input B: {dut.B_i.value.integer}")
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

    # Test the default XOR case
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(dut, 0)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing AND Cases              ")
    cocotb.log.info(" ------------------------------------------ ")

    # Test the default AND case
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(dut, 1)

    cocotb.log.info(" ------------------------------------------ ")
    cocotb.log.info("             Testing OR Cases               ")
    cocotb.log.info(" ------------------------------------------ ")

    # Test the default OR case
    for i in range(set_parameters.TEST_RUNS):
        await gen_and_test(dut, 2)


# Actual test run
@pytest.mark.parametrize(
    "parameters", [{"HVDimension": str(set_parameters.HV_DIM)}]
)
def test_hv_alu_pe(simulator, parameters):

    verilog_sources = ["/rtl/hv_alu_pe.sv"]

    toplevel = "hv_alu_pe"

    module = "test_hv_alu_pe"

    setup_and_run(verilog_sources=verilog_sources,
                  toplevel=toplevel,
                  module=module,
                  simulator=simulator,
                  parameters=parameters)
