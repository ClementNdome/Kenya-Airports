$ $py = @'
import PIL
if not hasattr(PIL, "__version__"): PIL.__version__ = "10.0.0"
import os
from pypdf import PdfReader
r = PdfReader(r"E:\DEVELOPMENT_\DJANGOS\new-refined\Kenya-Airports\docs\CAA-AC-AGA005C CONTROL OF OBSTACLES.pdf")
for i, p in enumerate(r.pages):
    print(f"===== PAGE {i+1} =====")
    print(p.extract_text() or "")
'@; $py | .venv\Scripts\python.exe - 2>&1
...


Aviation (Aerodromes) Regulations 2013.  
 
5.2.2. Basic ILS surfaces 
 
5.2.2.1. The "basic ILS surfaces" defined in PANS -OPS Document 8168 represent the simplest form of 
protection for ILS operations. These surfaces are extensions of certain Manual of Aerodrome 
Standards surfaces, referenced to threshold level throughout and modified after threshold to 
protect the instrument missed approach.  
 
5.2.3. Obstacle assessment surfaces 
 
5.2.3.1. The obstacle assessment surfaces (OAS) establish a volume of airspace, inside which it is assumed 
the flight paths of aeroplanes making ILS approaches and subsequent missed approaches will be 
contained with sufficiently high probability. Accordingly, aerop lanes need normally only be 
protected from those obstacles that penetrate this airspace; objects that do not penetrate it usually 
present no danger to ILS operations. However, if the density of obstacles below the OAS is very 
high, these obstacles will add to the total risk and may need to be evaluated.  
 
5.2.3.2. The difference between the basic ILS surfaces and the OAS is that the dimensions of the latter are 
based upon a collection of data on aircraft ILS precision approach performance during actual 
instrument meteorological conditions, rather than existing Manual of Aerodrome Standards  
surfaces. 
 
5.2.4. ILS Collision Risk Model (CRM) 
 
5.2.4.1. The Collision Risk Model (CRM) is a  computer programme that calculates the probability of  
collision with obstacles by an aeroplane on an ILS approach and subsequent missed approach. 
5.2.4.2. The CRM may be used to assist in 
a) Aerodrome planning during evaluation of possible location of new runways in a given 
geographical and obstacle environment 
b) Deciding whether or not an existing obstacle should be removed 
c) Deciding whether or not a particular new construction will result in an increase in OCA/H  
 
5.2.5. Visual manoeuvring (circling procedure) 
 
5.2.5.1. Visual manoeuvring described in the PANS-OPS, is a visual extension of an instrument approach 
procedure. The size of the area for a visual manoeuvring varies with the speed of aircraft. It is  
permissible to eliminate from consideration a particular sector where a prominent obstacle exists 
by establishing appropriate operational procedures.  
 
5.2.5.2. In many cases, the size of the area will be considerably larger than that covered by the Manual of 
Aerodrome Standards inner horizontal surface. Therefore, circling altitudes/heights calculated 
===== PAGE 7 =====
CAA-AC-AGA005C                                             June 2024                                      Page 7 of 16 
 
according to PANS-OPS for actual operations may be higher than those based only on obstacles 
penetrating the inner horizontal surface area. 
 
Note 1:  It must be stressed that a runway protected only by the obstacle limitation surfaces of 
Manual of Aerodrome Standards will not necessarily allow the achievement of the lowest possible 
operational minima if it does not, at the same time, satisfy the provisions of the PANS-OPS.  
 
Note 2: Consideration needs to be given to objects which penetrate the PANS-OPS surfaces, 
regardless of whether or not they penetrate  the Manual of Aerodrome Standards  obstacle 
limitation surface, and such obstacles may result in an operational penalty. 
 
6. CONTROLLING OBSTACLES AT AN AERODROME 
 
6.1. Background 
 
6.1.1. When buildings encroach on the airspace needed for aircraft operations a conflict of interest arises 
between property owners and aerodrome operators. If such differences cannot be resolved, it can 
be necessary for the Authority to establish restrictions limiting operations in the interest of safety. 
Such restrictions might take the form of requiring displaced thresholds (resulting in a reduction in 
effective runway length), higher weather mi nima for operations, reductions in authorized aircraft 
masses and possibly restrictions of certain aircraft types. Any of these actions could seriously affect 
orderly and efficient air transportation to an aerodrome and adversely affect the economy of the 
communities served by the aerodrome  
 
6.1.2. Control of obstacles in the vicinity of aerodromes is, therefore, a matter of interest and concern to 
Authority, aerodrome operators, local governments and communities and property owners. There 
are severe legal, economic, social and political limitations to what can be achieved by any of these 
interests with respect to an existing aerodrome where obstacles already exist. Every effort should 
be exerted by all interested parties to prevent erecting of future obstacles and to remove or lower 
existing obstacles.  
 
6.2. Legal authority and responsibility 
 
6.2.1. Pursuant to the Civil Aviation (Aerodromes Design and Operations) Regulations 2018 , the 
Authority may impose prohibitions or restrictions on the use of any area of land or water in the 
vicinity of aerodromes as may be necessary to ensure safe and efficient aircraft operations.  
 
6.2.2. The ultimate responsibility for limitation and control of obstacles must, rest with the aerodrome 
operator. This includes the responsibility for controlling obstacles on aerodrome property and for 
arranging the removal or lowering of existing obstacles outside the aerodrome boundaries. The 
latter obligation can be met by negotiations leading to purchase or condemnation where authorized.  
 
6.2.3. The aerodrome operators , local governments, planning agencies and construction licensing 
authorities should develop height zoning  regulations based on appropriate obstacle li mitation 
===== PAGE 8 =====
CAA-AC-AGA005C                                             June 2024                                      Page 8 of 16 
 
surfaces, and limit future developments accordingly. The  aerodrome operators shall require 
property owners or developers to give formal notice of any proposed structure which may penetrate 
an obstacle limitation surface. Local bodies should co-operate closely with aerodrome operators to 
ensure that the measures taken provide the greatest possible degree of safety and efficiency for 
aircraft operations, the maximum economic benefits to neighboring communities and the least 
possible interference with the rights of property owners  
 
6.2.4. Each aerodrome operator shall designate a member of his staff to be responsible for monitoring the 
growth of obstacles at and in the vicinity of aerodromes  and coordinate with local authorities 
prevent unauthorized growth of obstacles.  
 
6.3. In order to fulfill   these obligations, the aerodrome operator should establish a programme of 
regular and frequent visual inspections of all areas around the aerodrome in order to be sure that 
any construction activity or natural growth (i.e. trees) likely to infringe any of the obstacle 
limitation surfaces is discovered before it may become a problem.  
 
6.4. Methods of control 
 
6.4.1. Height zoning 
  
6.4.2. The objective of height zoning is to protect the aerodrome obstacle limitation surfaces from 
intrusion by man-made objects and natural growth such as trees. Height zoning may provide for a 
minimum allowable height for land use in the vicinity of the aerodrome. Land use zoning is also a 
means of preventing erection of new obstacles.  
 
6.4.3. Obstacle Removal 
 
6.4.3.1. When obstacles have been identified, the aerodrome operator should make every effort to have 
them removed, or reduced in height so that they are no longer obstacles.  If the obstacle is a single 
object it may be possible to reach agreement with the owner of the property to reduce the height 
to acceptable limits without adverse effect.   
 
6.4.3.2. In the case of trees, which are trimmed, agreement should be reached in writing with the property 
owner to ensure that future growth will not create new obstacles.  Property owners can give such 
assurance by agreeing to trim the trees when necessary, or by  permitting access to the premises 
to have the trimming done by the aerodrome operator�s representative.   
 
6.4.3.3. Some aids to navigation both electronic, such as ILS components, and visual, such as approach 
and runway lights, constitute obstacles which cannot be removed.  Such objects should be 
frangibly designed and constructed, and mounted on frangible couplings so that they will fail on 
impact without significant damage to and aircraft. Where necessary, such objects should be 
marked and/or lighted. 
 
6.4.4. Purchase of Easements and Property Rights 
===== PAGE 9 =====
CAA-AC-AGA005C                                             June 2024                                      Page 9 of 16 
 
 
6.4.4.1. In those areas where zoning is inadequate the aerodrome operator may take steps to protect the 
obstacle limitation surfaces by other means.  Examples of other means might be such as gaining 
easements or property rights.  They should include removal or reduction in height of ex isting 
obstacles and measures to ensure that no new obstacles are allowed to be erected in future. 
 
6.4.4.2. An aerodrome authority could achieve these objectives either by purchase of easements or 
property rights. Of these two alternatives, the purchase of easements would often prove to be more 
simple and economical.  In this case, the aerodrome authority secure s the consent of the owner 
(after paying suitable compensation) to lower the height of the obstacle in question.  This may be 
done by direct negotiation with the property owner.  Such an agreement should also include a 
provision to prevent erection of futu re obstacles, if height zoning limits are not in effect or are 
inadequate to protect obstacle limitation surfaces. 
 
6.4.4.3. Where agreement can be reached for the reduction in height of an obstacle, the agreement should 
include a written aviation easement limiting heights over the property to specific levels unless 
effective height zoning has been established. 
 
6.4.5. Obstacle shielding 
 
6.4.5.1. The principle of obstacle shielding is employed to permit a more logical approach to restricting 
new construction and to prescribing obstacles marking and lighting.  Shielding principles are 
employed when some object, an existing building or natural terrain, already penetrates above one 
of the aerodrome limitation surfaces.  If it is considered that the nature of an object is such that 
its presence may be described as permanent, then additional objects within a specified area around 
it may be permitted to penetrate the surface without being considered as obstacles.  The original 
obstacle is considered as dominating or shielding the surrounding area. 
 
6.4.5.2. The shielding effect of immovable obstacle laterally in approach and take-off climb areas is more 
uncertain. In certain circumstances, it may be advantageous to preserve existing unobstructed 
cross-section areas, particularly when the obstacle is close to the runway.  This would guard 
against future changes in either approach or take-off climb area specifications or the adoption of 
a turned take-off procedure. The permanency of the immovable obstacle which is to be considered 
as shielding an area should be given very careful review.  An object should be classed as 
immovable only if, when taking the longest view possible, there is no prospect of removal being 
practicable, possible or justifiable, regardless of how the pattern, type or density of air operations 
might change. 
 
6.5. Marking and lighting of obstacle 
 
6.5.1. Where it is impractical to eliminate an obstacle, it should be appropriately marked and/or lighted 
so as to be clearly visible to pilots in all weather and visibility conditions. The Manual of 
===== PAGE 10 =====
CAA-AC-AGA005C                                             June 2024                                      Page 10 of 16 
 
Aerodrome Standards contains detailed requirements concerning marking and/or lighting of 
obstacles.  
 
6.5.2. It should be noted that the marking and lighting of obstacles is intended to reduce hazards to 
aircraft by indicating the presence of the obstacles. It does not necessarily reduce operating 
limitations which may be imposed by the obstacle. The Manual of Aerodrome Standards specifies 
that obstacles be marked and, if the aerodrome is used at night, lighted, except that: 
a) Such marking and lighting may be omitted when the obstacle is shielded by another obstacle; 
and 
b) The marking may be omitted when the obstacle is lighted by high intensity obstacle lights 
by day. 
 
6.5.3. Vehicles and other mobile objects, excluding aircraft, on movement areas of aerodromes should be 
marked and lighted, unless used only on apron areas. 
6.5.4. Installation and maintenance of required marking and lighting may be done by the property owner, 
by community authorities or by the aerodrome operator. The aerodrome operator should make a 
daily visual inspection of all obstacle lights on and around the ae rodrome, and take steps to have 
inoperative lights repaired. Aerodrome operators may find it helpful to use dual light fixtures with 
an automatic switch to the second light fixture in case the first one fails. Such an arrangement 
provides greater assurance  of continued obstacle lighting and reduces the number of visits to 
replace inoperative lamps 
6.6. Notification of proposed construction 
6.6.1. One of the difficult aspects of obstacle control is the problem of anticipating new construction 
which may penetrate obstacle limitation surfaces. Aerodrome operators have no direct means of 
preventing such developments. As noted above, they should conduct frequent inspections of the 
aerodrome environs to learn of any suck projects. Although there is no legal obligation for 
aerodrome operators to report proposed constructions when they become aware of it, their own 
self-interest and the need to protect the aerodrome indicate the wisdom of bringing such matters to 
the attention of the Authority. Of course where an obstacle is to be located on aerodrome property, 
such as electronic or visual aids, the aerodrome operator is responsible for reporting such projects.  
 
6.6.2. Notification of new construction shall be made through aeronautical charts or Aeronautical 
Information Publication (AIP). 
 
7. OBSTACLE SURVEYS 
 
7.1. General 
 
7.1.1. Aerodrome obstacle surveys are conducted in order to enable the aerodrome operators to determine 
the location and elevation of objects that may constitute infringements of both PANS OPS and the 
Manual of Aerodrome Standards obstacle control surfaces. The surveys include the approach area 
===== PAGE 11 =====
CAA-AC-AGA005C                                             June 2024                                      Page 11 of 16 
 
and surface, take-off climb area and surface, transitional, horizontal and conical surfaces at both 
proposed and existing aerodromes. In the case of a precision approach runway or a runway on 
which a precision approach aid is likely to be installed, the surv ey should cover the additional 
horizontal surface associated with this aid.   
 
7.1.2. The aerodrome obstacle survey must supply principally: 
a) the aerodrome elevation; 
b) runway profile elevations; 
c) the latitude and longitude of the aerodrome reference point (ARP); 
d) the width and length of each runway; 
e) the azimuth of each runway; 
f) the planimetry at the aerodrome; and 
g) the location and elevation of each obstacle in the area covered by the chart. 
 
7.2. Obstacle survey practices 
 
7.2.1. The complexity of each survey and the number of charts maintained will vary from State to State. 
ICAO Document 9137 gives additional guidance on obstacle survey practices.    
 
7.2.2. The methods for survey include:  
a) use of photography during the survey    
b) photogrammetric compilation processes and /or 
c) field methods 
 
7.2.3. The field survey is considered in a series of steps or processes as follows: 
7.2.3.1. Initial survey: The initial survey should produce a chart presenting a plan view of the entire 
aerodrome and its environs to the outer limit of the conical surface (and the outer horizontal 
surface where established), together with profile views of all obstacle limitation surfaces. Each 
obstacle should be identified in both plan and profile with its descript ion and height above the 
datum which should be specified in the chart. More detailed requirements are contained in chapter 
3 and 4 of Annex 4, describing aerodrome ob struction chart. Engineering field surveys may be 
supplemented by aerial photographs and photogrammetry to identify possible obstacles not 
readily visible from the aerodrome 
 
7.2.3.2. Periodic survey:  The aerodrome operator should make frequent visual observations of 
surrounding areas to determine the presence of new obstacles. Follow up surveys should be 
conducted whenever significant changes occur. A detailed survey of a specific area may be 
necessary when the ini tial survey indicates the presence of obstacles for which a removal 
programme is contemplated. Following a completion of an obstacle removal programme, the area 
should be resurveyed to provide corrected data on the presence or absence of obstacles. Similarly, 
revision surveys should be made if changes are made (or planned) in aerodrome chrematistics 
such as runway length, elevation or orientation. No firm rule can be set down for the frequency 
of periodic survey, but constant vigilance is required. Changes in obstacle data arising from such 
===== PAGE 12 =====
CAA-AC-AGA005C                                             June 2024                                      Page 12 of 16 
 
surveys should be reported to the aviation community in accordance with the provisions of Annex 
15. 
 
7.2.3.3. Revision survey - A thorough field examination of the existing obstacle chart is made  and all 
the field survey data required is supplied to update the chart to conform with the current 
requirements. The kind and volume of the field work required for revision survey will var y 
considerably depending upon the age of the chart.  
 
8. AERODROME EQUIPMENT AND INSTALLATIONS WHICH MAY CONSTITUTE 
OBSTACLES 
 
8.1. General 
 
8.1.1. All fixed and mobile objects, or parts thereof, that are located on an area intended for the surface 
movement of aircraft or that extends  above 300ft above ground level are obstacles. Certain 
aerodrome equipment and installations, because of their air navigation functions, must inevitably 
be so located and/or constructed that they constitute obstacles. Equipment or installations other than 
these should not be permitted. This section discusses the sitting and construction of aerodrome 
equipment and installations which of necessity must be located on a runway strip; a runway end 
safety area; a taxiway strip; or within the taxiway clearance distance specified in the Manual of 
Aerodromes Standards; or on a clearway, if it would endanger an aircraft in the air. 
 
8.1.2. When aerodrome equipment, such as a vehicle or plant is an obstacle, it is generally considered 
temporary obstacle. However, when aerodrome installations such as visual aids, radio aids and 
meteorological installations are obstacles, they are generally considered permanent obstacles.  
 
8.1.3. Any equipment or installation which is situated on an aerodrome and which is an obstacle should 
be of minimum practicable mass and height and be sited in such a manner as to reduce the hazard 
to aircraft to a minimum. Additionally, any such equipment or installation which is fixed at its base 
should incorporate frangible mounting. 
 
8.1.4. The degree to which equipment and installations can be made to conform to the desired construction 
characteristics is often dependent on the performance requirements of the equipment or installation 
concerned.  
 
8.1.5. Many factors must be considered in the selection of aid fixtures and their mounting devices to 
ensure that the reliability of the aids is maintained and that the hazard to aircraft in flight or 
manoeuvring on the ground is minimal. It is therefore importan t that the appropriate structural 
characteristics of all aids which may be obstacles be specified and published. Some guidance 
material on the frangibility requirements of aerodrome equipment and installations are contained 
in Section 25 of this AC. 
 
8.2. Types of aerodrome equipment and installations which may constitute obstacles 
 
===== PAGE 13 =====
CAA-AC-AGA005C                                             June 2024                                      Page 13 of 16 
 
8.2.1. There are many types of aerodrome equipment and installations which, because of their particular 
air navigation functions, must be so located that they constitute obstacles. Such aerodrome 
equipment and installations include: 
a) ILS glide path antennas; 
b) ILS inner marker beacons; 
c) ILS localizer antennas; 
d) Wind direction indicators; 
e) Landing direction indicators; 
f) Anemometers; 
g) Ceilometers; 
h) Transmissometers;  
i) Elevated runway edge, threshold, end and stopway lights; 
j) Elevated taxiway edge lights; 
k) Approach lights; 
l) Visual approach slope indicator systems/precision approach slope indicator systems; 
m) Signs and markers; 
n) Components of the microwave landing system (MLS); 
o) Certain radar and other electronic installations and other devices; 
p) VOR or VOR/DME when located on aerodrome; 
q) Precision approach radar system or elements; 
r) VHF direction finders; and 
s) Aerodrome maintenance equipment, e.g. tracks, tractors. 
 
There is wide variation in the structural characteristics of these aids currently in use. Some guidance 
is provided below on appropriate structural characteristics of these aids for guidance of designers.  
 
8.2.2. ILS Glide Path Antennas 
 
8.2.2.1. The ILS glide path antenna masts may consist of thin walled large-diameter tubes which are slightly 
cone-shaped and made from fibre -glass material with short glass fibres. These masts can resist 
considerable wind loadings but they will break with the appli cation of a load such as would be 
imposed in the event of impact by an aircraft. 
 
8.2.3. ILS Localizer antennas 
 
8.2.3.1. ILS localizer antenna supports may consist of thin -walled tubes made from fibre glass material 
with short glass fibres. The maximum height of the installation may be about 3 m. The reflectors 
of the localizer antennas may be rods approximately 2.5m long, h eld by springs only. When 
exposed to loads in excess of the design load, they jump out of their supports and thus minimize 
the hazard to an aircraft overrunning the runway. Alternatively, the localizer antenna could 
comprise aluminium-clad balsa wood spars supported by aluminium tubing where the supporting 
structure incorporates shear pins at critical points to allow the structure to collapse under impact. 
 
 
===== PAGE 14 =====
CAA-AC-AGA005C                                             June 2024                                      Page 14 of 16 
 
8.2.4. Transmissometers 
 
8.2.4.1. The structure on which the transmissometer is placed may be constructed of hollow aluminium 
tubes that, although sufficiently strong by themselves, bend or break easily should an aircraft 
collide with them. The structure is attached to sunken concrete foundation by means of breakable 
bolts.  
 
8.2.5. Elevated runway edge, threshold, end, stopway and taxiway edge lighting 
 
8.2.5.1. The height of these lights should be sufficiently low to ensure propeller and engine pod clearance. 
Wing flex and strut compression under dynamic loads can bring the engine pods of some aircraft 
to near ground level. Only a small height can be tolerated, and a maximum height of 36 cm is 
advocated. 
 
8.2.5.2. These aids should be mounted on frangible mounting devices. The impact load required to cause 
failure at the break point should not exceed 5kg.m and a static load required to cause failure 
should not exceed 230 kg applied horizontally 30 cm above the break  point of the mounting 
device. The desirable maximum height of light units and frangible coupling is 36 cm above 
ground. Units exceeding this height limitation may require higher breaking characteristics for the 
frangible mounting device, but the frangibil ity should be such that, should a unit be hit by an 
aircraft, the impact would result in minimum damage to aircraft. 
 
8.2.5.3. In addition, all elevated light installed on runways of code letters A and B should be capable of 
withstanding a jet engine exhaust velocity of 300 kt, and lights on runways of code letters C, D, 
and E, a lower velocity of 200kt. Elevated taxiway edge lights should be able to withstand an 
exhaust velocity of 200 kt. 
 
8.2.6. Approach lighting system 
 
8.2.6.1. To minimize the hazard to aircraft that may strike them, approach lights should have a frangible 
device, or their supports be of a frangible design. 
 
8.2.6.2. Where the terrain requires light fittings and their supporting structure to be taller than 
approximately 1.8 m and they constitute the critical hazard, it is considered that it is not 
practicable to require that the frangible mounting devise be at the base  of the structure. The 
frangible portion may be limited to the top 1.8 m of the structure, except if the structure itself is 
frangible. Though there is some question of the need to provide frangibility for approach lights 
installed beyond 300 m before the threshold (as these light are required to be below the approach 
surface), it is recognized that protection needs to be provided for aircraft that might descend 
below the approach or take -off surfaces. A frangible top portion of 1.8 m is considered to be a 
minimum specification, and a longer frangible top potion should be provided where possible. 
  
===== PAGE 15 =====
CAA-AC-AGA005C                                             June 2024                                      Page 15 of 16 
 
8.2.6.3. In all cases the unit and supports of the approach lighting system should fail when an impact load 
of not more than 5kg.m and a static load of not less than 230 kg is applied horizontally at 30 cm 
above the break point of the structure. 
 
8.2.6.4. Where it is necessary for approach lights to be installed in stopways, the light should be inset in 
the surface when the stopway is paved. When the stopway is not paved, they should either be 
inset or, if elevated, meet the criteria for frangibility agreed for lights installed beyond the runway 
end. 
 
8.2.7. Other aids (e.g. VASIS, signs and markers) 
 
8.2.7.1. These aids should be located as far as practicable from the edges of runways, taxiways and aprons 
as is compatible with their function. Every effort should be made to ensure that the aids will retain 
their structural integrity when subjected to the most severe environmental conditions. However, 
when subjected to aircraft impact in excess of the foregoing conditions, the aids will break or 
distort in a manner which will cause minimum or no damage to aircraft. 
 
8.2.7.2. Caution should be taken when installing visual aids in the movement area to ensure that the light 
support base does not protrude above ground, but rather terminates below ground as required by 
environmental conditions so as to cause minimum or no damage to the aircraft overrunning them. 
However, the frangible coupling should always be above ground level. 
 
9. OBSTACLE CONTROL PROCEDURES IN THE AERODROME MANUAL 
 
9.1. Details of the procedures for inspection of the aerodrome movement area, obstacle limitation 
surface and for obstacle control at an aerodrome should be presented in the Aerodrome Manual. 
 
9.2. Particulars in the aerodrome manual of the procedures for the inspection of the aerodrome 
movement area and obstacle limitation surface must include details of the following: 
 
a) Arrangements for carrying out inspections, including runway friction and water depth 
measurement on runways and taxiways during and outside normal hours of aerodrome 
operations; 
b) Arrangements and means of communicating with ATC during an inspection; 
c) Arrangements for keeping an inspection logbook and the location of the logbook; 
d) Details of inspection intervals and times; 
e) Inspection checklist; 
f) Arrangements for reporting the results of inspections and for taking prompt follow-up actions 
to ensure correction of unsafe conditions; and 
g) The names and roles of persons responsible for carrying out inspections and their contact 
numbers during and after working hours. 
 
9.3. Particulars in the aerodrome manual for obstacle control must contain details setting out the 
procedures for � 
===== PAGE 16 =====
CAA-AC-AGA005C                                             June 2024                                      Page 16 of 16 
 
 
a) Monitoring the obstacle limitation surfaces and Type A chart for obstacle in the take -off 
surface; 
b) Controlling obstacles within the authority of the aerodrome operator; 
c) Monitoring the height of buildings or structures within the boundaries of the obstacle 
limitation surfaces; 
d) Controlling new developments in the vicinity of the aerodrome; 
e) Notifying the Authority of the nature and location of obstacles and any subsequent addition 
or removal of obstacles for action as necessary, including amendment of AIS publications. 
 
 
 
 
__________________ 
Civil Aviation Authority