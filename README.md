Short program clips doing something useful in my digital life:

# imagine

This script defines a function or method decorator that
allows the user to redefine the function or method for
one or more points in its domain, arbitrarily, bypassing
any calculation. The override extends to the end of a 
"with" context, and is visible in the global code base.
The paradigm here is one to inject imagined functional
values globally but temporarily.

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

# game_bulls_and_cows_codebreaker

This script plays the codebreaker in a game of Bulls & Cows.
It uses a naive strategy that only looks ahead one move.
The aim was to write a very short script that works on
the phone (in Pythonista 3). I used it to impress my kids
when playing the modern version of the game, Mastermind,
with them.