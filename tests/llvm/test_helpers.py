#!/usr/bin/python3

import copy
import functools
import numpy as np
import pytest

from psyneulink.core import llvm as pnlvm
from llvmlite import ir


DIM_X=1000
TST_MIN=1.0
TST_MAX=3.0

vector = np.random.rand(DIM_X)

@pytest.mark.llvm
@pytest.mark.parametrize('mode', ['CPU',
                                  pytest.param('PTX', marks=pytest.mark.cuda)])
def test_helper_fclamp(mode):

    with pnlvm.LLVMBuilderContext() as ctx:
        local_vec = copy.deepcopy(vector)
        double_ptr_ty = ctx.float_ty.as_pointer()
        func_ty = ir.FunctionType(ir.VoidType(), (double_ptr_ty, ctx.int32_ty,
                                                  double_ptr_ty))

        # Create clamp function
        custom_name = ctx.get_unique_name("clamp")
        function = ir.Function(ctx.module, func_ty, name=custom_name)
        vec, count, bounds = function.args
        block = function.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        tst_min = builder.load(builder.gep(bounds, [ctx.int32_ty(0)]))
        tst_max = builder.load(builder.gep(bounds, [ctx.int32_ty(1)]))

        index = None
        with pnlvm.helpers.for_loop_zero_inc(builder, count, "linear") as (builder, index):
            val_ptr = builder.gep(vec, [index])
            val = builder.load(val_ptr)
            val = pnlvm.helpers.fclamp(builder, val, tst_min, tst_max)
            builder.store(val, val_ptr)

        builder.ret_void()

    ref = np.clip(vector, TST_MIN, TST_MAX)
    bounds = np.asfarray([TST_MIN, TST_MAX])
    bin_f = pnlvm.LLVMBinaryFunction.get(custom_name)
    if mode == 'CPU':
        ct_ty = pnlvm._convert_llvm_ir_to_ctype(double_ptr_ty)
        ct_vec = local_vec.ctypes.data_as(ct_ty)
        ct_bounds = bounds.ctypes.data_as(ct_ty)

        bin_f(ct_vec, DIM_X, ct_bounds)
    else:
        bin_f.cuda_wrap_call(local_vec, np.int32(DIM_X), bounds)

    assert np.array_equal(local_vec, ref)


@pytest.mark.llvm
@pytest.mark.parametrize('mode', ['CPU',
                                  pytest.param('PTX', marks=pytest.mark.cuda)])
def test_helper_fclamp_const(mode):

    with pnlvm.LLVMBuilderContext() as ctx:
        local_vec = copy.deepcopy(vector)
        double_ptr_ty = ctx.float_ty.as_pointer()
        func_ty = ir.FunctionType(ir.VoidType(), (double_ptr_ty, ctx.int32_ty))

        # Create clamp function
        custom_name = ctx.get_unique_name("clamp")
        function = ir.Function(ctx.module, func_ty, name=custom_name)
        vec, count = function.args
        block = function.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        index = None
        with pnlvm.helpers.for_loop_zero_inc(builder, count, "linear") as (builder, index):
            val_ptr = builder.gep(vec, [index])
            val = builder.load(val_ptr)
            val = pnlvm.helpers.fclamp(builder, val, TST_MIN, TST_MAX)
            builder.store(val, val_ptr)

        builder.ret_void()

    ref = np.clip(vector, TST_MIN, TST_MAX)
    bin_f = pnlvm.LLVMBinaryFunction.get(custom_name)
    if mode == 'CPU':
        ct_ty = pnlvm._convert_llvm_ir_to_ctype(double_ptr_ty)
        ct_vec = local_vec.ctypes.data_as(ct_ty)

        bin_f(ct_vec, DIM_X)
    else:
        bin_f.cuda_wrap_call(local_vec, np.int32(DIM_X))

    assert np.array_equal(local_vec, ref)


@pytest.mark.llvm
@pytest.mark.parametrize('mode', ['CPU',
                                  pytest.param('PTX', marks=pytest.mark.cuda)])
def test_helper_is_close(mode):

    with pnlvm.LLVMBuilderContext() as ctx:
        double_ptr_ty = ctx.float_ty.as_pointer()
        func_ty = ir.FunctionType(ir.VoidType(), [double_ptr_ty, double_ptr_ty,
                                                  double_ptr_ty, ctx.int32_ty])

        # Create clamp function
        custom_name = ctx.get_unique_name("all_close")
        function = ir.Function(ctx.module, func_ty, name=custom_name)
        in1, in2, out, count = function.args
        block = function.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        index = None
        with pnlvm.helpers.for_loop_zero_inc(builder, count, "compare") as (builder, index):
            val1_ptr = builder.gep(in1, [index])
            val2_ptr = builder.gep(in2, [index])
            val1 = builder.load(val1_ptr)
            val2 = builder.load(val2_ptr)
            close = pnlvm.helpers.is_close(builder, val1, val2)
            out_ptr = builder.gep(out, [index])
            out_val = builder.select(close, ctx.float_ty(1), ctx.float_ty(0))
            builder.store(out_val, out_ptr)

        builder.ret_void()
        
    vec1 = copy.deepcopy(vector)
    tmp = np.random.rand(DIM_X)
    tmp[0::2] = vec1[0::2]
    vec2 = np.asfarray(tmp)
    assert len(vec1) == len(vec2)
    res = np.empty_like(vec2)

    ref = np.isclose(vec1, vec2)
    bin_f = pnlvm.LLVMBinaryFunction.get(custom_name)
    if mode == 'CPU':
        ct_ty = pnlvm._convert_llvm_ir_to_ctype(double_ptr_ty)
        ct_vec1 = vec1.ctypes.data_as(ct_ty)
        ct_vec2 = vec2.ctypes.data_as(ct_ty)
        ct_res = res.ctypes.data_as(ct_ty)

        bin_f(ct_vec1, ct_vec2, ct_res, DIM_X)
    else:
        bin_f.cuda_wrap_call(vec1, vec2, res, np.int32(DIM_X))

    assert np.array_equal(res, ref)
