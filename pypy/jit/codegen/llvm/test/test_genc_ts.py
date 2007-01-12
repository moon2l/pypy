import py
from pypy.jit.codegen.i386.test.test_genc_ts import I386TimeshiftingTestMixin
from pypy.jit.timeshifter.test import test_timeshift
from pypy.jit.codegen.llvm.rgenop import RLLVMGenOp
from pypy.jit.codegen.llvm.llvmjit import llvm_version, MINIMAL_VERSION


class LLVMTimeshiftingTestMixin(I386TimeshiftingTestMixin):
    RGenOp = RLLVMGenOp


class TestTimeshiftLLVM(LLVMTimeshiftingTestMixin,
                        test_timeshift.TestTimeshift):

    # for the individual tests see
    # ====> ../../../timeshifter/test/test_timeshift.py

    def skip(self):
        py.test.skip("WIP")

    def skip_too_minimal(self):
        py.test.skip('found llvm %.1f, requires at least llvm %.1f(cvs)' % (
            llvm_version(), MINIMAL_VERSION))

    if llvm_version() < 2.0:
        test_loop_merging = skip_too_minimal #segfault
        test_two_loops_merging = skip_too_minimal #segfault
        test_green_char_at_merge = skip #segfault
        test_residual_red_call_with_exc = skip
    else: #needs fixing for >= 2.0
        test_red_array = skip
        test_red_struct_array = skip
        test_red_varsized_struct = skip
        test_array_of_voids = skip
        test_merge_structures = skip
        test_green_char_at_merge = skip
