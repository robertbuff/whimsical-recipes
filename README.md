Short program clips doing something useful in my digital life:

# gopro_merge_dual_hero3

This script takes the left and right HD videos taken with the 
Dual Hero system. This system houses two synchronized GoPro Hero3+
cameras. The script uses ffmpeg to produce a side-by-side 
merged 4k video. It can correct for vertical displacement 
of the two cameras in the housing (mine is 16 pixels.) The
script can also correct the inputs for distortion.

My workflow used to be to import the individual videos and
combine them in Final Cut Pro X and a Dashwood plugin. The
plugin isn't maintained any longer. Now I can run the
script in the background and then simply import the merged
side-by-side videos.

# gopro_sbs_to_other_formats

This script takes a side-by-side movie and converts it into
two additional stereo formats: red/cyan/gray anaglyph and
sterescopic. The movie may come out of a movie editor (I'm
using Final Cut Pro X to combine the merged Dual Hero clips
into a movie.)