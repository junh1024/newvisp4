My part4 CSE project.

It's Messy python code because it's halfway between optimized and organized (having performance issues), and it's not particularly well-commented.


[Source direct link](https://code.google.com/p/newvisp4/source/browse/trunk/GUI.py)

[W32 binary Download page](https://code.google.com/p/newvisp4/issues/detail?id=11)

Unique features not found in any other FFT to my knowledge:
  * Frequency-dependant ballistics
  * Continually variable scale
  * Phase displayed ON the FTT, not below or to the side

**Install**:===

Extract the 7z with [7-zip](http://7-zip.org/) or Winzip.


**Quickstart**:===

The main executable is called gui.exe. Open that, and drag n drop a music file (mp3, aac, ogg, wav, flac should be supported) on the black area and press 'c' to play.

![https://newvisp4.googlecode.com/svn/trunk/Manual.png](https://newvisp4.googlecode.com/svn/trunk/Manual.png)

**Ballistics**:===
  * “1-way variable decay” raises the speed of fall for higher frequencies, which allows better visualization of transients at higher frequencies. (default, good for general purpose)
  * “1-way fixed decay” limits the rate of fall (decay) of spectrum points to a fixed coefficient, but the rate of rise is not limited so transients are not missed. This is a good tradeoff between readability and responsiveness within the restriction of storing only one previous reading.
  * “2-way average” limits the rate of rise and fall by averaging the current FFT points with the previous set of FFT points.
  * “Infinite maximum” takes the maximum of the current and previous FFT points, and
  * “none” delivers data to the display with no ballistics or postprocessing (useful for ultraparanoid lossy analysis)

**Scale slider**:=== Note that different scales place different emphasis on different frequency ranges, so analyzing and detecting problems across a broad range of frequencies is easier

**Phase colours**:=== detailed (default), magnified average, and none (best performance, enable this for fullscreen use).

**SFR** = Stereo field rotation DSP

Bugs and missing features do exist. Please see https://code.google.com/p/newvisp4/issues/list