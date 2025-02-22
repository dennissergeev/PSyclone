! -----------------------------------------------------------------------------
! BSD 3-Clause License
!
! Copyright (c) 2017-2021, Science and Technology Facilities Council
! All rights reserved.
!
! Redistribution and use in source and binary forms, with or without
! modification, are permitted provided that the following conditions are met:
!
! * Redistributions of source code must retain the above copyright notice, this
!   list of conditions and the following disclaimer.
!
! * Redistributions in binary form must reproduce the above copyright notice,
!   this list of conditions and the following disclaimer in the documentation
!   and/or other materials provided with the distribution.
!
! * Neither the name of the copyright holder nor the names of its
!   contributors may be used to endorse or promote products derived from
!   this software without specific prior written permission.
!
! THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
! "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
! LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
! FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
! COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
! INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
! BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
! LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
! CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
! LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
! ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
! POSSIBILITY OF SUCH DAMAGE.
! -----------------------------------------------------------------------------
! Authors: R. W. Ford and A. R. Porter, STFC Daresbury Lab
! Modified: I. Kavcic, Met Office
!
!> @brief Meta-data for the LFRic API built-in operations.
!> @details This meta-data is purely to provide PSyclone with a
!!          specification of each operation. This specification is used
!!          for correctness checking as well as to enable optimisations
!!          of invokes containing calls to built-in operations.
!!          The actual implementation of these built-ins is
!!          generated by PSyclone (hence the empty ..._code routines in
!!          this file).
module lfric_builtins_mod

use kernel_mod,    only : kernel_type
use argument_mod,  only : arg_type,            &
                          GH_FIELD, GH_SCALAR, &
                          GH_REAL, GH_INTEGER, &
                          GH_READ, GH_WRITE,   &
                          GH_READWRITE,        &
                          ANY_SPACE_1, DOF

! ******************************************************************* !
! ************** Built-ins for real-valued fields ******************* !
! ******************************************************************* !

! ------------------------------------------------------------------- !
! ============== Adding (scaled) real fields ======================== !
! ------------------------------------------------------------------- !

  !> field3 = field1 + field2
  type, public, extends(kernel_type) :: X_plus_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_WRITE, ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_plus_Y_code
  end type X_plus_Y

  !> field1 = field1 + field2
  type, public, extends(kernel_type) :: inc_X_plus_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_READWRITE, ANY_SPACE_1),     &
          arg_type(GH_FIELD, GH_REAL, GH_READ,      ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_plus_Y_code
  end type inc_X_plus_Y

  !> field2 = scalar + field1
  type, public, extends(kernel_type) :: a_plus_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: a_plus_X_code
  end type a_plus_X

  !> field = scalar + field
  type, public, extends(kernel_type) :: inc_a_plus_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_a_plus_X_code
  end type inc_a_plus_X

  !> field3 = scalar*field1 + field2
  type, public, extends(kernel_type) :: aX_plus_Y
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: aX_plus_Y_code
  end type aX_plus_Y

  !> field1 = scalar*field1 + field2
  type, public, extends(kernel_type) :: inc_aX_plus_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,      ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_aX_plus_Y_code
  end type inc_aX_plus_Y

  !> field1 = field1 + scalar*field2
  type, public, extends(kernel_type) :: inc_X_plus_bY
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1),    &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,      ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_plus_bY_code
  end type inc_X_plus_bY

  !> field3 = scalar1*field1 + scalar2*field2
  type, public, extends(kernel_type) :: aX_plus_bY
     private
     type(arg_type) :: meta_args(5) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: aX_plus_bY_code
  end type aX_plus_bY

  !> field1 = scalar1*field1 + scalar2*field2
  type, public, extends(kernel_type) :: inc_aX_plus_bY
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1),    &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,      ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_aX_plus_bY_code
  end type inc_aX_plus_bY

  !> field3 = scalar*(field1 + field2)
  type, public, extends(kernel_type) :: aX_plus_aY
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: aX_plus_aY_code
  end type aX_plus_aY

! ------------------------------------------------------------------- !
! ============== Subtracting (scaled) real fields =================== !
! ------------------------------------------------------------------- !

  !> field3 = field1 - field2
  type, public, extends(kernel_type) :: X_minus_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_WRITE, ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_minus_Y_code
  end type X_minus_Y

  !> field1 = field1 - field2
  type, public, extends(kernel_type) :: inc_X_minus_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_READWRITE, ANY_SPACE_1),     &
          arg_type(GH_FIELD, GH_REAL, GH_READ,      ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_minus_Y_code
  end type inc_X_minus_Y

  !> field2 = scalar - field1
  type, public, extends(kernel_type) :: a_minus_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: a_minus_X_code
  end type a_minus_X

  !> field = scalar - field
  type, public, extends(kernel_type) :: inc_a_minus_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_a_minus_X_code
  end type inc_a_minus_X


  !> field3 = scalar*field1 - field2
  type, public, extends(kernel_type) :: aX_minus_Y
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: aX_minus_Y_code
  end type aX_minus_Y

  !> field3 = field1 - scalar*field2
  type, public, extends(kernel_type) :: X_minus_bY
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_minus_bY_code
  end type X_minus_bY

  !> field1 = field1 - scalar*field2
  type, public, extends(kernel_type) :: inc_X_minus_bY
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1),    &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,      ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_minus_bY_code
  end type inc_X_minus_bY

  !> field3 = scalar1*field1 - scalar2*field2
  type, public, extends(kernel_type) :: aX_minus_bY
     private
     type(arg_type) :: meta_args(5) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: aX_minus_bY_code
  end type aX_minus_bY

! ------------------------------------------------------------------- !
! ============== Multiplying (scaled) real fields =================== !
! ------------------------------------------------------------------- !

  !> field3 = field1*field2
  type, public, extends(kernel_type) :: X_times_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_WRITE, ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_times_Y_code
  end type X_times_Y

  !> field1 = field1*field2
  type, public, extends(kernel_type) :: inc_X_times_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_READWRITE, ANY_SPACE_1),     &
          arg_type(GH_FIELD, GH_REAL, GH_READ,      ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_times_Y_code
  end type inc_X_times_Y

  !> field1 = scalar*field1*field2
  type, public, extends(kernel_type) :: inc_aX_times_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,      ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_aX_times_Y_code
  end type inc_aX_times_Y

! ------------------------------------------------------------------- !
! ============== Scaling real fields ================================ !
! ------------------------------------------------------------------- !

  !> field2 = scalar*field1
  type, public, extends(kernel_type) :: a_times_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: a_times_X_code
  end type a_times_X

  !> field = scalar*field
  type, public, extends(kernel_type) :: inc_a_times_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_a_times_X_code
  end type inc_a_times_X

! ------------------------------------------------------------------- !
! ============== Dividing real fields =============================== !
! ------------------------------------------------------------------- !

  !> field3 = field1/field2
  type, public, extends(kernel_type) :: X_divideby_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_WRITE, ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_divideby_Y_code
  end type X_divideby_Y

  !> field1 = field1/field2
  type, public, extends(kernel_type) :: inc_X_divideby_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_READWRITE, ANY_SPACE_1),     &
          arg_type(GH_FIELD, GH_REAL, GH_READ,      ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_divideby_Y_code
  end type inc_X_divideby_Y

! ------------------------------------------------------------------- !
! ============== Inverse scaling of real fields ===================== !
! ------------------------------------------------------------------- !

  !> field2 = scalar/field1
  type, public, extends(kernel_type) :: a_divideby_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: a_divideby_X_code
  end type a_divideby_X

  !> field = scalar/field
  type, public, extends(kernel_type) :: inc_a_divideby_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  ),    &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1)     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_a_divideby_X_code
  end type inc_a_divideby_X

! ------------------------------------------------------------------- !
! ============== Raising a real field to a scalar =================== !
! ------------------------------------------------------------------- !

  !> field =  field**rscalar (real scalar)
  type, public, extends(kernel_type) :: inc_X_powreal_a
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_READWRITE, ANY_SPACE_1),    &
          arg_type(GH_SCALAR, GH_REAL, GH_READ                  )     &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_powreal_a_code
  end type inc_X_powreal_a

  !> field =  field**iscalar (integer scalar)
  type, public, extends(kernel_type) :: inc_X_powint_n
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD,  GH_REAL,    GH_READWRITE, ANY_SPACE_1), &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ                  )  &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: inc_X_powint_n_code
  end type inc_X_powint_n

! ------------------------------------------------------------------- !
! ============== Setting real field elements to a value  ============ !
! ------------------------------------------------------------------- !

  !> field = scalar
  type, public, extends(kernel_type) :: setval_c
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              )         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: setval_c_code
  end type setval_c

  !> field2 = field1
  type, public, extends(kernel_type) :: setval_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_REAL, GH_WRITE, ANY_SPACE_1),         &
          arg_type(GH_FIELD, GH_REAL, GH_READ,  ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: setval_X_code
  end type setval_X

! ------------------------------------------------------------------- !
! ============== Inner product of real fields ======================= !
! ------------------------------------------------------------------- !

  !> innprod = innprod + field1(i,j,..)*field2(i,j,...)
  type, public, extends(kernel_type) :: X_innerproduct_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_SUM              ),         &
          arg_type(GH_FIELD,  GH_REAL, GH_READ, ANY_SPACE_1),         &
          arg_type(GH_FIELD,  GH_REAL, GH_READ, ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_innerproduct_Y_code
  end type X_innerproduct_Y

  !> innprod = innprod + field(i,j,..)*field(i,j,...)
  type, public, extends(kernel_type) :: X_innerproduct_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_SUM              ),         &
          arg_type(GH_FIELD,  GH_REAL, GH_READ, ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: X_innerproduct_X_code
  end type X_innerproduct_X

! ------------------------------------------------------------------- !
! ============== Sum real field elements ============================ !
! ------------------------------------------------------------------- !

  !> sumfld = SUM(field(:,:,...))
  type, public, extends(kernel_type) :: sum_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_REAL, GH_SUM              ),         &
          arg_type(GH_FIELD,  GH_REAL, GH_READ, ANY_SPACE_1)          &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: sum_X_code
  end type sum_X

! ------------------------------------------------------------------- !
! ============== Sign of real field elements ======================== !
! ------------------------------------------------------------------- !

  !> field2 = SIGN(scalar, field1)
  type, public, extends(kernel_type) :: sign_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_REAL, GH_WRITE, ANY_SPACE_1),        &
          arg_type(GH_SCALAR, GH_REAL, GH_READ              ),        &
          arg_type(GH_FIELD,  GH_REAL, GH_READ,  ANY_SPACE_1)         &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: sign_X_code
  end type sign_X

! ------------------------------------------------------------------- !
! ============== Converting real to integer field elements ========== !
! ------------------------------------------------------------------- !

  !> ifield2 = int(field1, i_def)
  type, public, extends(kernel_type) :: int_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_WRITE, ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_REAL,    GH_READ,  ANY_SPACE_1)       &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_X_code
  end type int_X

! ******************************************************************* !
! ************** Built-ins for integer-valued fields **************** !
! ******************************************************************* !

! ------------------------------------------------------------------- !
! ============== Adding integer fields ============================== !
! ------------------------------------------------------------------- !

  !> ifield3 = ifield1 + ifield2
  type, public, extends(kernel_type) :: int_X_plus_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_WRITE, ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1)       &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_X_plus_Y_code
  end type int_X_plus_Y

  !> ifield1 = ifield1 + ifield2
  type, public, extends(kernel_type) :: int_inc_X_plus_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_READWRITE, ANY_SPACE_1),  &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,      ANY_SPACE_1)   &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_inc_X_plus_Y_code
  end type int_inc_X_plus_Y

  !> ifield2 = iscalar + ifield1
  type, public, extends(kernel_type) :: int_a_plus_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_INTEGER, GH_WRITE, ANY_SPACE_1),     &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ              ),     &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READ,  ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_a_plus_X_code
  end type int_a_plus_X

  !> ifield = iscalar + ifield
  type, public, extends(kernel_type) :: int_inc_a_plus_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ                  ), &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READWRITE, ANY_SPACE_1)  &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_inc_a_plus_X_code
  end type int_inc_a_plus_X

! ------------------------------------------------------------------- !
! ============== Subtracting integer fields ========================= !
! ------------------------------------------------------------------- !

  !> ifield3 = ifield1 - ifield2
  type, public, extends(kernel_type) :: int_X_minus_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_WRITE, ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1)       &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_X_minus_Y_code
  end type int_X_minus_Y

  !> ifield1 = ifield1 - ifield2
  type, public, extends(kernel_type) :: int_inc_X_minus_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_READWRITE, ANY_SPACE_1),  &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,      ANY_SPACE_1)   &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_inc_X_minus_Y_code
  end type int_inc_X_minus_Y

  !> ifield2 = iscalar - ifield1
  type, public, extends(kernel_type) :: int_a_minus_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_INTEGER, GH_WRITE, ANY_SPACE_1),     &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ              ),     &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READ,  ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_a_minus_X_code
  end type int_a_minus_X

  !> ifield = iscalar - ifield
  type, public, extends(kernel_type) :: int_inc_a_minus_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ                  ), &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READWRITE, ANY_SPACE_1)  &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_inc_a_minus_X_code
  end type int_inc_a_minus_X

! ------------------------------------------------------------------- !
! ============== Multiplying integer fields ========================= !
! ------------------------------------------------------------------- !

  !> ifield3 = ifield1*ifield2
  type, public, extends(kernel_type) :: int_X_times_Y
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_WRITE, ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1)       &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_X_times_Y_code
  end type int_X_times_Y

  !> ifield1 = ifield1*ifield2
  type, public, extends(kernel_type) :: int_inc_X_times_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_READWRITE, ANY_SPACE_1),  &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,      ANY_SPACE_1)   &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_inc_X_times_Y_code
  end type int_inc_X_times_Y

! ------------------------------------------------------------------- !
! ============== Scaling integer fields ============================= !
! ------------------------------------------------------------------- !

  !> ifield2 = iscalar*ifield1
  type, public, extends(kernel_type) :: int_a_times_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_INTEGER, GH_WRITE, ANY_SPACE_1),     &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ              ),     &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READ,  ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_a_times_X_code
  end type int_a_times_X

  !> ifield = iscalar*ifield
  type, public, extends(kernel_type) :: int_inc_a_times_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ                  ), &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READWRITE, ANY_SPACE_1)  &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_inc_a_times_X_code
  end type int_inc_a_times_X

! ------------------------------------------------------------------- !
! ============== Setting integer field elements to a value  ========= !
! ------------------------------------------------------------------- !

  !> ifield = iscalar
  type, public, extends(kernel_type) :: int_setval_c
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD,  GH_INTEGER, GH_WRITE, ANY_SPACE_1),     &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ              )      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_setval_c_code
  end type int_setval_c

  !> ifield2 = ifield1
  type, public, extends(kernel_type) :: int_setval_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_INTEGER, GH_WRITE, ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1)       &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_setval_X_code
  end type int_setval_X

! ------------------------------------------------------------------- !
! ============== Sign of integer field elements ===================== !
! ------------------------------------------------------------------- !

  !> ifield2 = SIGN(iscalar, ifield1)
  type, public, extends(kernel_type) :: int_sign_X
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_FIELD,  GH_INTEGER, GH_WRITE, ANY_SPACE_1),     &
          arg_type(GH_SCALAR, GH_INTEGER, GH_READ              ),     &
          arg_type(GH_FIELD,  GH_INTEGER, GH_READ,  ANY_SPACE_1)      &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: int_sign_X_code
  end type int_sign_X

! ------------------------------------------------------------------- !
! ============== Converting integer to real field elements ========== !
! ------------------------------------------------------------------- !

  !> field2 = real(ifield1, r_def)
  type, public, extends(kernel_type) :: real_X
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD, GH_REAL,    GH_WRITE, ANY_SPACE_1),      &
          arg_type(GH_FIELD, GH_INTEGER, GH_READ,  ANY_SPACE_1)       &
          /)
     integer :: operates_on = DOF
   contains
     procedure, nopass :: real_X_code
  end type real_X

contains

  ! ***** Real-valued fields ***** !
  ! Adding (scaled) real fields
  subroutine X_plus_Y_code()
  end subroutine X_plus_Y_code

  subroutine inc_X_plus_Y_code()
  end subroutine inc_X_plus_Y_code

  subroutine a_plus_X_code()
  end subroutine a_plus_X_code

  subroutine inc_a_plus_X_code()
  end subroutine inc_a_plus_X_code

  subroutine aX_plus_Y_code()
  end subroutine aX_plus_Y_code

  subroutine inc_aX_plus_Y_code()
  end subroutine inc_aX_plus_Y_code

  subroutine inc_X_plus_bY_code()
  end subroutine inc_X_plus_bY_code

  subroutine aX_plus_bY_code()
  end subroutine aX_plus_bY_code

  subroutine inc_aX_plus_bY_code()
  end subroutine inc_aX_plus_bY_code

  subroutine aX_plus_aY_code()
  end subroutine aX_plus_aY_code

  ! Subtracting (scaled) real fields
  subroutine X_minus_Y_code()
  end subroutine X_minus_Y_code

  subroutine inc_X_minus_Y_code()
  end subroutine inc_X_minus_Y_code

  subroutine a_minus_X_code()
  end subroutine a_minus_X_code

  subroutine inc_a_minus_X_code()
  end subroutine inc_a_minus_X_code

  subroutine aX_minus_Y_code()
  end subroutine aX_minus_Y_code

  subroutine X_minus_bY_code()
  end subroutine X_minus_bY_code

  subroutine inc_X_minus_bY_code()
  end subroutine inc_X_minus_bY_code

  subroutine aX_minus_bY_code()
  end subroutine aX_minus_bY_code

  ! Multiplying (scaled) real fields
  subroutine X_times_Y_code()
  end subroutine X_times_Y_code

  subroutine inc_X_times_Y_code()
  end subroutine inc_X_times_Y_code

  subroutine inc_aX_times_Y_code()
  end subroutine inc_aX_times_Y_code

  ! Multiplying real fields by a real scalar
  ! (scaling fields)
  subroutine a_times_X_code()
  end subroutine a_times_X_code

  subroutine inc_a_times_X_code()
  end subroutine inc_a_times_X_code

  ! Dividing real fields
  subroutine X_divideby_Y_code()
  end subroutine X_divideby_Y_code

  subroutine inc_X_divideby_Y_code()
  end subroutine inc_X_divideby_Y_code

  ! Dividing a real scalar by elements of a
  ! real field (inverse scaling of fields)
  subroutine a_divideby_X_code()
  end subroutine a_divideby_X_code

  subroutine inc_a_divideby_X_code()
  end subroutine inc_a_divideby_X_code

  ! Raising a real field to a scalar
  subroutine inc_X_powreal_a_code()
  end subroutine inc_X_powreal_a_code

  subroutine inc_X_powint_n_code()
  end subroutine inc_X_powint_n_code

  ! Setting real field elements to a real scalar
  ! or other real field's values
  subroutine setval_c_code()
  end subroutine setval_c_code

  subroutine setval_X_code()
  end subroutine setval_X_code

  ! Inner product of real fields
  subroutine X_innerproduct_Y_code()
  end subroutine X_innerproduct_Y_code

  subroutine X_innerproduct_X_code()
  end subroutine X_innerproduct_X_code

  ! Sum values of a real field
  subroutine sum_X_code()
  end subroutine sum_X_code

  ! Sign of real field elements
  subroutine sign_X_code()
  end subroutine sign_X_code

  ! Converting real to integer field elements
  subroutine int_X_code()
  end subroutine int_X_code

  ! ***** Integer-valued fields ***** !
  ! Adding integer fields
  subroutine int_X_plus_Y_code()
  end subroutine int_X_plus_Y_code

  subroutine int_inc_X_plus_Y_code()
  end subroutine int_inc_X_plus_Y_code

  subroutine int_a_plus_X_code()
  end subroutine int_a_plus_X_code

  subroutine int_inc_a_plus_X_code()
  end subroutine int_inc_a_plus_X_code

  ! Subtracting integer fields
  subroutine int_X_minus_Y_code()
  end subroutine int_X_minus_Y_code

  subroutine int_inc_X_minus_Y_code()
  end subroutine int_inc_X_minus_Y_code

  subroutine int_a_minus_X_code()
  end subroutine int_a_minus_X_code

  subroutine int_inc_a_minus_X_code()
  end subroutine int_inc_a_minus_X_code

  ! Multiplying integer fields
  subroutine int_X_times_Y_code()
  end subroutine int_X_times_Y_code

  subroutine int_inc_X_times_Y_code()
  end subroutine int_inc_X_times_Y_code

  ! Multiplying integer fields by an integer scalar
  ! (scaling fields)
  subroutine int_a_times_X_code()
  end subroutine int_a_times_X_code

  subroutine int_inc_a_times_X_code()
  end subroutine int_inc_a_times_X_code

  ! Setting integer field elements to an integer scalar
  ! or other integer field's values
  subroutine int_setval_c_code()
  end subroutine int_setval_c_code

  subroutine int_setval_X_code()
  end subroutine int_setval_X_code

  ! Sign of integer field elements
  subroutine int_sign_X_code()
  end subroutine int_sign_X_code

  ! Converting integer to real field elements
  subroutine real_X_code()
  end subroutine real_X_code

end module lfric_builtins_mod
