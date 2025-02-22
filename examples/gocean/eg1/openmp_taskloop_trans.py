# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2017-2021, Science and Technology Facilities Council.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
# Authors: R. W. Ford, A. R. Porter and S. Siso, STFC Daresbury Lab
#          A. B. G. Chalk, STFC Daresbury Lab

'''A simple test script showing the introduction of OpenMP tasking with
PSyclone.

'''

from __future__ import print_function
from psyclone.parse.algorithm import parse
from psyclone.psyGen import PSyFactory, TransInfo
from psyclone.psyir.backend.fortran import FortranWriter
from psyclone.psyir.nodes import Loop
from psyclone.transformations import OMPParallelTrans, OMPSingleTrans
from psyclone.transformations import OMPTaskloopTrans
from psyclone.psyir.transformations import OMPTaskwaitTrans


def trans(psy):
    '''
    Transformation routine for use with PSyclone. Applies the OpenMP
    taskloop and taskwait transformations to the PSy layer.

    :param psy: the PSy object which this script will transform.
    :type psy: :py:class:`psyclone.psyGen.PSy`
    :returns: the transformed PSy object.
    :rtype: :py:class:`psyclone.psyGen.PSy`

    '''

    singletrans = OMPSingleTrans()
    paralleltrans = OMPParallelTrans()
    tasklooptrans = OMPTaskloopTrans(nogroup=False)
    taskwaittrans = OMPTaskwaitTrans()
    for invoke in psy.invokes.invoke_list:
        print("Adding OpenMP tasking to invoke: " + invoke.name)
        schedule = invoke.schedule
        for child in schedule.children:
            if isinstance(child, Loop):
                tasklooptrans.apply(child)
        singletrans.apply(schedule)
        paralleltrans.apply(schedule)
        taskwaittrans.apply(schedule[0])

    return psy
