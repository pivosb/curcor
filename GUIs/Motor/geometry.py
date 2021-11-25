#######################################################################
#                                                                     #
#   The definition of the coordinate system as used here is:          #
#        (Perspective from above)                                     #
#           _____________________________________________             #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |                                             |   ^        #
#          |                                             |   |        #
#        ^ |                                             |  x_len     #
# X-AXIS | |                                             |   |        #
#        - |-->Z-AXIS             X                      |   V        #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |                                             |            #
#          |               <-- z_len -->                 |            #
#          |_____________________________________________|            #
#                                                                     #
#          - OUT OF THE PLANE: Y-AXIS   Zero defined @ LID            #
#          - The "X"-symbol marks the theoretically correct           #
#            focal spot of the telescope                              #
#            (coordinates x=0, y=0, z=z_len/2)                        #
#          - all values used here are given in mm                     #
#                                                                     #
#                                                                     #
#######################################################################

#as defined in the sketch
x_len=500
z_len=640

#offset values of the focal spot in relation to the setup (due to imprecisions in the mounting of the setup)
#these values are determined experimentally and then inserted here
offset_center_x=0
offset_center_y=0
offset_center_z=0

#calculate the position of the center according to the parameters that we inserted before
center_z=z_len/2=offset_center_z
center_y=offset_center_y
center_x=offset_center_x

#constants due to the geometry of the telescope
dish_focal_length=1500 #focal length of the dish. Is the same as the distance between the lid and a hypothetical mirror in the middle of the dish
dish_diameter=1300 # diamter of the dish

#constants of the setup
lens_focal_length= #focal length of the lens used in the optics to parralelize the light
lens_center_offset_y= #height of the lens-center above the lid
