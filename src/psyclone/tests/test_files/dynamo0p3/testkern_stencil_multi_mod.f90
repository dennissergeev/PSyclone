! -----------------------------------------------------------------------------
! BSD 3-Clause License
!
! Copyright (c) 2017-2020, Science and Technology Facilities Council
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
! Author R. W. Ford, STFC Daresbury Lab
! Modified I. Kavcic, Met Office

module testkern_stencil_multi_mod

  use argument_mod
  use fs_continuity_mod
  use kernel_mod
  use constants_mod

  implicit none

  type, extends(kernel_type) :: testkern_stencil_multi_type
     type(arg_type), dimension(4) :: meta_args =               &
          (/ arg_type(gh_field, gh_inc,  w1),                  &
             arg_type(gh_field, gh_read, w2, stencil(cross)),  &
             arg_type(gh_field, gh_read, w2, stencil(xory1d)), &
             arg_type(gh_field, gh_read, w3, stencil(x1d))     &
           /)
     integer :: operates_on = cell_column
   contains
     procedure, nopass :: code => testkern_stencil_multi_code
  end type testkern_stencil_multi_type

contains

  subroutine testkern_stencil_multi_code(nlayers, fld1,                  &
                                         fld2, fld2_st_size,             &
                                         fld2_st_dofmap,                 &
                                         fld3, fld3_st_size,             &
                                         fld3_direction, fld3_st_dofmap, &
                                         fld4, fld4_st_size,             &
                                         fld4_st_dofmap,                 &
                                         ndf_w1, undf_w1, map_w1,        &
                                         ndf_w2, undf_w2, map_w2,        &
                                         ndf_w3, undf_w3, map_w3)

    implicit none

    integer(kind=i_def), intent(in) :: nlayers
    integer(kind=i_def), intent(in) :: ndf_w1
    integer(kind=i_def), intent(in) :: ndf_w2
    integer(kind=i_def), intent(in) :: ndf_w3
    integer(kind=i_def), intent(in) :: undf_w1, undf_w2, undf_w3
    integer(kind=i_def), intent(in) :: fld2_st_size, fld3_st_size, fld4_st_size
    integer(kind=i_def), intent(in) :: fld3_direction
    integer(kind=i_def), intent(in), dimension(ndf_w1) :: map_w1
    integer(kind=i_def), intent(in), dimension(ndf_w2) :: map_w2
    integer(kind=i_def), intent(in), dimension(ndf_w3) :: map_w3
    integer(kind=i_def), intent(in), dimension(ndf_w2,fld2_st_size) :: fld2_st_dofmap
    integer(kind=i_def), intent(in), dimension(ndf_w2,fld3_st_size) :: fld3_st_dofmap
    integer(kind=i_def), intent(in), dimension(ndf_w3,fld4_st_size) :: fld4_st_dofmap
    real(kind=r_def), intent(inout), dimension(undf_w1) :: fld1
    real(kind=r_def), intent(in), dimension(undf_w2)    :: fld2
    real(kind=r_def), intent(in), dimension(undf_w2)    :: fld3
    real(kind=r_def), intent(in), dimension(undf_w3)    :: fld4

  end subroutine testkern_stencil_multi_code

end module testkern_stencil_multi_mod
