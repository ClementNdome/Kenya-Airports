$ $env:PYTHONIOENCODING="utf-8"; $py = @'
import PIL
if not hasattr(PIL, "__version__"): PIL.__version__ = "10.0.0"
import os, sys, re
from pypdf import PdfReader
def clean(t):
    return re.sub(r"[\uf000-\uf0ff\u2000-\u206f]", "", t or "")
r = PdfReader(r"E:\DEVELOPMENT_\DJANGOS\new-refined\Kenya-Airports\docs\CAA-AC-AGA032A Lighting and Marking of Obstacles.pdf")
for i, p in enumerate(r.pages[7:], start=8):
    print(f"===== PAGE {i} =====")
    print(clean(p.extract_text()))
'@; $py | .venv\Scripts\python.exe - 2>&1
===== PAGE 8 =====
CAA-AC-AGA032A February 2026 Page 8 of 13 
 
 
 
Figure 1(b)  Marking and lighting of tall structures 
 
See 6. 3.112.
A
A
C
B
H
H
A  Rooftop pattern
A   Plain roof pattern
B  Curved surface
C  Skeleton structure
N1
N2Y
X
Light spacing (X) in accordance with Appendix 5
Number of levels of lights = N =Y (metres)
X (metres)
Note. H is less than 45 m for the examples shown above.
For greater heights intermediate lights must be added as shown below.
===== PAGE 9 =====
CAA-AC-AGA032A February 2026 Page 9 of 13 
 
Note. 1:- In  the  case  of  chimney  or  other structure  of  
like  function,  the  top  lights  should  be placed sufficiently 
below the top so as to  minimize contamination by smoke 
etc. 
Note. 2:- H  is  less t h a n  45  m     for     the examples 
shown above. For greater heights intermediate lights must 
be added as shown Figure 2 (a). 
 
 
Number of obstruction lights to be  placed on tall 
structures can be calculated by the following formula: 
 
 
 
 
Number of levels of lights = N = Y (metres) 
45 
 
 
 
Light spacing = X = Y ≤ 45m 
N 
 
 
Figure 2 (a)  Lighting of tall structures (No. and Spacing) 
 
 
 
 
Figure 2 (b)  - Lighting of buildings

===== PAGE 10 =====
CAA-AC-AGA032A February 2026 Page 10 of 13 
 
 
Figure 2 (c)  Lighting of extensive buildings 
 
5.2.  Overhead wires, cables, etc., and supporting towers Markings 
 
Aerial/Obstruction warning is primarily meant to help pilots see the lines to avoid flying into 
them. Aerial/obstruction marker balls shall be displayed on the following along the flight path 
to warn pilots during the day; 
a) High-rise Power Transmission Lines 
b) Ropeway cables 
c) Guyed Wires 
Note: The warning sphere shall conform to the specifications in the Regulations. 
 
In addition to being used for protection of airports, the red balls are used in other areas where 
aircraft frequent and to delineate power lines that cross rivers, canyons or ravines. For instance, 
some larger hospitals offer helicopter transfer of patients. Since a hospital is not set up in the 
same way that an airport is, the balls may be installed on powerlines near the hospital to help 
guide the pilot. If there are any areas where emergency medical evacuations are common, the 
balls may be used on lines in these areas as well. 
 
The support towers are obstruction painted. When painting the support towers is not practical, 
or to provide added warning, shore markers painted orange and white will be displayed. In some 
cases, older marker panels that have not been updated are of a checkerboard design. 
 
An alternative method of marking is to use strobe lights on shore-based cable support towers. 
Normally three levels of lights are installed as follows: one light unit at the top of the structures 
to provide 360° coverage; two light units on each structure at the base of the arc of the lowest 
cable; and two light units at a point midway between the top and bo ttom levels with 180° 
coverage. The beams of the middle and lower lights are adjusted so that the signal will be seen 
from the approach direction on either side of the power line. The lights flash sequentially: 
middle lights followed by the top lights and then the bottom lights in order to display a fly up 
signal to the pilot. The middle light may be removed in the case of narrow power line sags; in 

===== PAGE 11 =====
CAA-AC-AGA032A February 2026 Page 11 of 13 
 
this case the bottom lights will flash first then the top lights will flash in order to display a fly 
up signal to the pilot. When determined appropriate by an aeronautical study, medium-intensity 
white flashing omnidirectional lighting systems may be used on supporting structures of 
suspended cable spans lower than 150 m (500 ft) AGL. 
 
5.4. Specifications for aerial/obstruction marker balls 
Obstruction markings on aerial cables (i.e., marker balls) that define aeronautical hazards are 
generally placed on the highest line for crossings where there is more than one cable. In this case, 
the marker balls are placed on the lowest power line and are displayed to water craft as a warning 
of low clearance between the water and an overhead cable. See figure 3 for illustration. 
 
In accordance with the foregoing, pilots operating at low levels may expect to find power line 
crossings marked as either an aeronautical hazard. They may be unmarked if it has bee n 
determined by the CAA that it is not an aeronautical hazard. Pilots operating at low altitudes 
must be aware of the hazards and exercise extreme caution. 
Each ball shall be of a single solid colour. When installed, white and red, or white and orange 
markers should be displayed alternately. The color selected should contrast with the background 
against which it will be seen. 
Each ball shall not have a diameter less than 60 cm.  
The spacing between two consecutive markers or between a marker and a supporting tower should 
be appropriate to the diameter of the marker, but in no case should the spacing exceed: 
a) 30 m where the marker diameter is 60 cm progressively increasing with the diameter of the 
marker to  
b) 35 m where the marker diameter is 80 cm and further progressively increasing to a maximum of 
c) 40 m where the marker diameter is of at least 130 cm. 
Where multiple wires, cables, etc., are involved, a marker should be located not lower than the level 
of the highest wire at the point marked. 
===== PAGE 12 =====
CAA-AC-AGA032A February 2026 Page 12 of 13 
 
 
Figure 3  Marking of aerial cables 
 
5.5  Wind turbines 
A wind turbine shall be marked and/or lighted if it is determined to be an obstacle. 
Note 1:-Additional lighting or markings may be provided where in the opinion of the State such 
lighting or markings are deemed necessary. 
The rotor blades, nacelle and upper 2/3 of the supporting mast of wind turbines should be painted 
white, unless otherwise indicated by an aeronautical study. 
When lighting is deemed necessary, in the case of a wind farm, i.e. a group of two or more wind 
turbines, the wind farm should be regarded as an extensive object and the lights should be 
installed: 
a) to identify the perimeter of the wind farm; 

===== PAGE 13 =====
CAA-AC-AGA032A February 2026 Page 13 of 13 
 
b) respecting the maximum spacing, between the lights along the perimeter, unless a dedicated 
assessment shows that a greater spacing can be used; 
c) so that, where flashing lights are used, they flash simultaneously throughout the wind farm; 
d) so that, within a wind farm, any wind turbines of significantly higher elevation are also 
identified wherever they are located; and 
e) at locations prescribed in a), b) and d), respecting the following criteria: 
i). for wind turbines of less than 150 m in overall height (hub height plus vertical blade 
height), medium-intensity lighting on the nacelle should be provided; 
ii). for wind turbines from 150 m to 315 m in overall height, in addition to the medium -
intensity light installed on the nacelle, a second light serving as an alternate should be 
provided in case of failure of the operating light. The lights should be installed to assure 
that the output of either light is not blocked by the other; and 
iii). in addition, for wind turbines from 150 m to 315 m in overall height, an intermediate 
level at half the nacelle height of at least three low-intensity Type E lights, as specified 
in 5.5 e) should be provided. If an aeronautical study shows that low-intensity Type E 
lights are not suitable, low-intensity Type A or B lights may be used. 
Note: -The above 5.5 (e) does not address wind turbines of more than 315 m of overall height. 
For such wind turbines, additional marking and lighting may be required as determined by 
an aeronautical study. 
 
The obstacle lights should be installed on the nacelle in such a manner as to provide an 
unobstructed view for aircraft approaching from any direction. 
Where lighting is deemed necessary for a single wind turbine or short line of wind turbines, the 
installation should be in accordance with section 5.5 (e) or as determined by an aeronautical study. 
 
 
 
___________________ 
Civil Aviation Authority