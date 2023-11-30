#!/usr/bin/env python3
# coding: utf-8

import os
# os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import numpy as np

 
import pycuda.driver as drv
from pycuda.compiler import SourceModule

import pycuda.tools
import pycuda.autoinit

# this is from NV offfice python
# import cuda
# from cuda import cuda, nvrtc
# from cuda import cudart

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string("fn", "example/vector_add/out", "cubin file name")
flags.DEFINE_string("func", "_Z9vectorAddPfS_S_i", "func name after mingling")
flags.DEFINE_integer("thr", 5, "thread num")

# from: https://documen.tician.de/pycuda/tutorial.html
def jit():
    mod = SourceModule("""
    __global__ void multiply_them(float *dest, float *a, float *b)
    {
    const int i = threadIdx.x;
    dest[i] = a[i] * b[i];
    }
    """)

    multiply_them = mod.get_function("multiply_them")

    a = np.random.randn(400).astype(np.float32)
    b = np.random.randn(400).astype(np.float32)

    dest = np.zeros_like(a)
    multiply_them(
            drv.Out(dest), drv.In(a), drv.In(b),
            block=(400,1,1), grid=(1,1))
    
    print('JIT:')
    # print(dest)
    # print(dest-a*b)
    np.testing.assert_allclose(dest, a*b) 
    print(f'multiply_them passed')

def jit_with_args():

    # Define the CUDA kernel
    cuda_kernel_code = """
    __global__ void add_int_kernel(int *result, int value_to_add) {
        *result += value_to_add;
    }
    """

    # Compile the CUDA kernel
    mod = SourceModule(cuda_kernel_code)
    add_int_kernel = mod.get_function("add_int_kernel")

    # Create a numpy array to hold the result
    result = np.array([5], dtype=np.int32)

    # Define the integer argument
    value_to_add = np.int32(10)

    # Call the CUDA kernel and pass the integer argument
    add_int_kernel(drv.InOut(result), value_to_add, block=(1, 1, 1), grid=(1, 1))

    # Print the updated result
    print("Result after adding:", result[0])


def main(_):

    # jit()  # jit is ok
    # jit_with_args()

    mod = drv.module_from_file(f'{FLAGS.fn}.cubin')
    kernel = mod.get_function(f'{FLAGS.func}')

    # args short cut (without short cut we can do cu_memcpy explicitly)
    # TODO find a way to get args and cuda launch args from cubin automatically??
    a = np.random.randn(400).astype(np.float32)
    b = np.random.randn(400).astype(np.float32)
    dest = np.zeros_like(a)
    n = np.int32(400)

    # kernel configs
    block = (400, 1, 1)
    grid = (1, 1)

    # launch
    kernel(drv.In(a), drv.In(b), drv.Out(dest),  n, #
            block=block, grid=grid, # 
    )

    # result
    print('CUBIN:')

    # print(f'Result = {np.unique(c)[0]:#0x}')
    # print(f'Result = {dest}')

    c_ref = a+b
    np.testing.assert_allclose(dest, c_ref) 
    print(f'{FLAGS.fn} passed')

if __name__ == "__main__":
    app.run(main)