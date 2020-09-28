! -----------------------------------------------------------------------------
! BSD 3-Clause License
!
! Copyright (c) 2017-2020, Science and Technology Facilities Council
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
! Authors R. W. Ford and A. R. Porter, STFC Daresbury Lab
! Modified I. Kavcic, Met Office

module testkern_w3_mod

  use constants_mod
  use argument_mod
  use fs_continuity_mod
  use kernel_mod

  implicit none

  ! Description: discontinuous field (read)writer (w3)
  type, extends(kernel_type) :: testkern_w3_type
     type(arg_type), dimension(5) :: meta_args = (/       &
          arg_type(gh_scalar, gh_real, gh_read),          &
          arg_type(gh_field,           gh_read,      w0), &
          arg_type(gh_field,           gh_read,      w1), &
          arg_type(gh_field,           gh_read,      w2), &
          arg_type(gh_field,           gh_readwrite, w3)  &
          /)
     integer :: operates_on = cell_column
   contains
     procedure, nopass :: code => testkern_w3_code
  end type testkern_w3_type

contains

  subroutine testkern_w3_code(nlayers, ascalar,        &
                              fld1, fld2, fld3, fld4,  &
                              ndf_w0, undf_w0, map_w0, &
                              ndf_w1, undf_w1, map_w1, &
                              ndf_w2, undf_w2, map_w2, &
                              ndf_w3, undf_w3, map_w3)

    implicit none

    integer(kind=i_def), intent(in)  :: nlayers
    integer(kind=i_def), intent(in)  :: ndf_w0, undf_w0, &
                                        ndf_w1, undf_w1, &
                                        ndf_w2, undf_w2, &
                                        ndf_w3, undf_w3
    integer(kind=i_def), dimension(ndf_w1), intent(in) :: map_w0
    integer(kind=i_def), dimension(ndf_w1), intent(in) :: map_w1
    integer(kind=i_def), dimension(ndf_w2), intent(in) :: map_w2
    integer(kind=i_def), dimension(ndf_w3), intent(in) :: map_w3
    real(kind=r_def), intent(in) :: ascalar
    real(kind=r_def), dimension(undf_w1), intent(in)    :: fld1
    real(kind=r_def), dimension(undf_w2), intent(in)    :: fld2
    real(kind=r_def), dimension(undf_w2), intent(in)    :: fld3
    real(kind=r_def), dimension(undf_w3), intent(inout) :: fld4

  end subroutine testkern_w3_code

end module testkern_w3_mod
