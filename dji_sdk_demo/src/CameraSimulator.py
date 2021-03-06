#!/usr/bin/env python

#simulated target UTM coordinates
global TARGET_EAST
global TARGET_NORTH 
global TARGET_ZONE_NUMBER 
global TARGET_ZONE_LETTER 


#you can change them here
TARGET_EAST = 803814.947243 
TARGET_NORTH = 2495268.762723
TARGET_ZONE_NUMBER = 49
TARGET_ZONE_LETTER = 'Q'
#If you want to use latitude and longitude, you could place code like the following in main():
##simulatedTargetLatitude = 22.537018
##simulatedTargetLongitude = 113.953640
##TARGET_EAST, TARGET_NORTH, TARGET_ZONE_NUMBER, TARGET_ZONE_LETTER = from_latlon(simulatedTargetLatitude, simulatedTargetLongitude)









import math

def degsToRads(degrees):
    return math.pi*degrees/180.0

def radsToDegs(radians):
    return 180.0*radians/math.pi


def getCameraPlane(altitude, FOV_deg= 94.0 ):
    FOV_deg = 120.0 #it's 94.0 but the simulator is too strict so we need to compensate
    thetaDeg = FOV_deg/2.0
    theta = degsToRads(thetaDeg) #this is the angle that defines the "cone" of the camera
    #the camera x and y boundaries can each be defined using a cone, and then the image itself is a rectangle defined by those bounds
             # (theta)
            # /|
           # / |
          # /  |
         # /   | object distance
        # /    |  
       # /     | 
      # /      |
     # /       |
    # /-----------
    # field of vision (1 side, actual field is twice this much)

    # so the boundary on this is objectDistance*tan(theta), and the boundary is from -objectDistance*tan(theta) to objectDistance*tan(theta)

   #Since trig can take either sign, but the magnitude will be the same on each side, use the abs to be safe
    yBoundsCamera = [-1.0*abs(altitude*math.tan(theta)),abs(altitude*math.tan(theta)) ] 
    xBoundsCamera = [-1.0*abs(altitude*math.tan(theta)),abs(altitude*math.tan(theta)) ]

    return[xBoundsCamera , yBoundsCamera, "1st element = x bounds, 2nd = y bounds, meters"]
    

def getCameraBoundsInertial(roll_rads, pitch_rads, yaw_rads, quadNorth, quadEast, altitude):
     roll=roll_rads
     pitch=pitch_rads
     yaw=yaw_rads
     #print("roll %f pitch %f yaw %f",roll,pitch,yaw)     
     #so now we need to convert the camera FOV to boundaries in an inertial plane.
     #To do so, we'll need to know the current camera position and rotation, and the transform matrix of the camera
     transformMatrix =  [ [0,0,1], [1,0,0], [0,-1,0] ]
     #print("transform matrix");print(transformMatrix)
     #now, assuming roll is 0:
     # The camera boundaries will change depending on the camera pitch and yaw
     # Example: If camera is pointing straight ahead (pitch 0, yaw 0), y boundaries on camera are z boundaries  on inertial frame, x bounds are y bounds on inertial frame
     # If camera is pointing straight down (pitch -90, yaw 0) then y boundaries on camera are x boundaries on inertial frame, x bounds are y bounds on inertial frame
     # If camera is pointing to the right (pitch 0, yaw 90)  then y boundaries are z boundaries on inertial frame, x bounds are x bounds on inertial frame
     # Note that if camera is pointing straight down, yaw still matters
     # Ex: if pitch is -90 and yaw is 90, then y boundaries are y boundaries on inertial frame, x boundaries are x on inertial frame
     # So it appears we can use the rotation matrix again

     cameraRotationMatrix = [
            [   math.cos(yaw)*math.cos(pitch),
                 math.cos(yaw)*math.sin(pitch)*math.sin(roll)-math.sin(yaw)*math.cos(roll), 
                math.cos(yaw)*math.sin(pitch)*math.cos(roll) + math.sin(yaw)*math.sin(roll)
            ],
            [  
                math.sin(yaw)*math.cos(pitch),
                math.sin(yaw)*math.sin(pitch)*math.sin(roll) + math.cos(yaw)*math.cos(roll),
                math.sin(yaw)*math.sin(pitch)*math.cos(roll) - math.cos(yaw)*math.sin(roll) 
            ],
            [
             -1.0*math.sin(pitch),
            math.cos(pitch)*math.sin(roll),
            math.cos(pitch)*math.cos(roll)
            ],
        ];
     #print("rotation matrix") ;print(cameraRotationMatrix)
     boundsCameraFrame = getCameraPlane(altitude)
     xBoundsCameraFrame = boundsCameraFrame[0]
     yBoundsCameraFrame = boundsCameraFrame[1]
     
     #There's not a z boundary yet but there may be when converting, so need to create a field for that
     lowerBoundsXYZ = [[xBoundsCameraFrame[0]], [yBoundsCameraFrame[0]], [0]]
     upperBoundsXYZ = [[xBoundsCameraFrame[1]], [yBoundsCameraFrame[1]], [0]]
     #print("lower bounds");print(lowerBoundsXYZ); print("upper bounds"); print(upperBoundsXYZ)
     lowerBoundsXYZinertial = [[0],[0],[0]]
     upperBoundsXYZinertial = [[0],[0],[0]]
     testMat = [[11],[7],[13]]
     testMatrix=[[0],[0],[0]]

     lowerBoundsXYZinertialTemp = [[0],[0],[0]]
     upperBoundsXYZinertialTemp = [[0],[0],[0]]
     testMatrixTemp=[[0],[0],[0]]

     for row in range(0, 3):
        sumLower = 0.0;
        sumUpper = 0.0
        testSum=0;
        for  column in range(0 ,3):
            sumLower += transformMatrix[row][column] * lowerBoundsXYZ [column][0]; 
            sumUpper += transformMatrix[row][column] * upperBoundsXYZ [column][0]; 
            #testSum += transformMatrix[row][column] * testMat [column][0]; 
         #   print("row %d column %d testSum is %d" %(row,column,testSum) )
            
           
        lowerBoundsXYZinertialTemp[row][0] = sumLower;
        upperBoundsXYZinertialTemp[row][0] = sumUpper
        #testMatrixTemp[row][0]=testSum
        #print("lower bounds inertial");print(lowerBoundsXYZinertialTemp);print("upperBounds inertial");print(upperBoundsXYZinertialTemp);
        #print("testMatrix");print(testMatrixTemp)


     for row in range(0, 3):
        sumLower = 0.0;
        sumUpper = 0.0
        testSum=0;
        for  column in range(0 ,3):
            sumLower += cameraRotationMatrix[row][column] * lowerBoundsXYZinertialTemp [column][0]; 
            sumUpper += cameraRotationMatrix[row][column] * upperBoundsXYZinertialTemp [column][0]; 
            #testSum += cameraRotationMatrix[row][column] * testMatrixTemp [column][0]; 
      #      print("row %d column %d testSum is %d" %(row,column,testSum) )
            
           
        lowerBoundsXYZinertial[row][0] = sumLower;
        upperBoundsXYZinertial[row][0] = sumUpper
        #testMatrix[row][0]=testSum
        #print("lower bounds inertial");print(lowerBoundsXYZinertial);print("upperBounds inertial");print(upperBoundsXYZinertial);
        #print("testMatrix");print(testMatrix)
     #If we have a negative bounds, and a positive bounds, and apply the rotation matrix to it, that will convert the offset to inertial frame
     #But we also need to know where the center of the bounds is in inertial frame (ie, what point does 0,0 on the camera correspond to on inertial frame?)
     #Assuming target is roughly ground level, that can be solved with simple trig
     # 
     #  Copter: x_______________
      #         |\ (pitch)
    #           | \
    #           |  \
    #   Altitude|   \
    #           |    \
    #           |     \
    #           |      \
    #           |       \
     #          __________
      #          targetDistance ( = displacement2D)
    #  Ok, so displacement2D = altitude*tan(theta), where theta=90-pitch 
    #  And then from that, 
     
    #              _____ Y
    #             |   /
    #           X |  / displacement2D
    #             | /  
    #             |/_____________________(90 - yaw)
    #     Copter: x 
    #  clearly, deltaX = displacement2D * cos(yaw), deltaY = displacement2D*sin(yaw)
    
    #prevent getting an infinity in here
     if ( (degsToRads(-0.1) < pitch) & (pitch < degsToRads(0.1))  ):
        if(pitch > 0):
            pitch = degsToRads(0.1)
        else:
            pitch = degsToRads(-0.1)

     displacement2D = math.tan(-1.0 * degsToRads(90)-pitch) * altitude
    
     deltaX = displacement2D * math.cos(yaw)
     deltaY = displacement2D * math.sin(yaw)
     centerX = quadNorth + deltaX
     centerY = quadEast + deltaY

     #at this point, there's still some risk that the sign could be messed up, due to the trigonometric transform, so make sure we use the positive and negative appropriately
     
     yPositiveOffset = max(lowerBoundsXYZinertial[1][0], upperBoundsXYZinertial[1][0])
     yNegativeOffset = min(lowerBoundsXYZinertial[1][0], upperBoundsXYZinertial[1][0])
     xPositiveOffset = max(lowerBoundsXYZinertial[0][0], upperBoundsXYZinertial[0][0])
     xNegativeOffset = min(lowerBoundsXYZinertial[0][0], upperBoundsXYZinertial[0][0])
# In theory, the camera is roughly symmetric, but the field of view calculated can become extraordinarily narrow at certain times in this simulator.
# account for this by using the largest difference found.

     if(abs(xNegativeOffset) > abs(yNegativeOffset)):
         yNegativeOffset = xNegativeOffset;
     else:
         xNegativeOffset = yNegativeOffset;
     if(abs(xPositiveOffset) > abs(yPositiveOffset)):
         yPositiveOffset = xPositiveOffset;
     else:
         xPositiveOffset = yPositiveOffset;

#add a slight extra constant as well to account for the field of view when it's landed
     yBoundsInertial = [centerY +yNegativeOffset -2, centerY + yPositiveOffset +2 ]
     xBoundsInertial = [centerX + xNegativeOffset - 2, centerX + xPositiveOffset +2 ]
     
     cameraBoundsInertial = [xBoundsInertial, yBoundsInertial, "1st element: x bounds, 2nd element: y bounds, both in meters on inertial frame"]
     return cameraBoundsInertial
    
#This assumes that the target is actually in the camera's field of view. You'll need to calculated whether it is or not elsehwere
def calculateAprilTagDetection(roll_rads, pitch_rads, yaw_rads, quadNorth, quadEast, altitude, targetNorth, targetEast):
        yaw = yaw_rads; roll=roll_rads; pitch=pitch_rads;
    #knowing camera rotation matrix and transform matrix, camera position, and target position, need to figure out what the displacement is in the camera frame 
    #Assuming target is roughly at ground level, Z displacement(camera frame) is just  the total camera distance to ground
        deltaNorth = targetNorth - quadNorth;
        deltaEast = targetEast - quadEast;
        displacement2D = math.sqrt( deltaEast * deltaEast  +  deltaNorth * deltaNorth)
        cameraZ = math.sqrt( altitude * altitude   +   displacement2D * displacement2D) # this serves as a sanity check on the camera Z calculation done later

    #disp = rotation*transform*cameraDisp
    #transform^-1*rotation^-1*disp = cameraDisp  
    #transform^-1 is [ [0,1,0] [0,0,-1] [1,0,0] ]
    #so let's just convert the camera plane into inertial coords, and then we can figure out the camera displacement from there
        
        a = math.cos(yaw)*math.cos(pitch)
        b = math.cos(yaw)*math.sin(pitch)*math.sin(roll)-math.sin(yaw)*math.cos(roll)
        c = math.cos(yaw)*math.sin(pitch)*math.cos(roll) + math.sin(yaw)*math.sin(roll)
        d = math.sin(yaw)*math.cos(pitch)
        e = math.sin(yaw)*math.sin(pitch)*math.sin(roll) + math.cos(yaw)*math.cos(roll)
        f = math.sin(yaw)*math.sin(pitch)*math.cos(roll) - math.cos(yaw)*math.sin(roll) 
        g = -1.0*math.sin(pitch)
        h = math.cos(pitch)*math.sin(roll)
        i = math.cos(pitch)*math.cos(roll)
        cameraRotationMatrix = [
            [   a,
                 b, 
                c
            ],
            [  
                d,
                e,
                f 
            ],
            [
             g,
            h,
            i
            ],
        ];
        
    # so if we do, in matlab:
    #  syms a b c d e f g h id
    #  m = [a,b,c; d,e,f; g,h,i]
    #  v = m^-1
    # result is 
        """
     v =
         [  (e*i - f*h)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), -(b*i - c*h)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g),  (b*f - c*e)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g)]
         [ -(d*i - f*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g),  (a*i - c*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), -(a*f - c*d)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g)]
         [  (d*h - e*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), -(a*h - b*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g),  (a*e - b*d)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g)]

        """
    #so there's our inverse 
        invRow1 = [(e*i - f*h)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), -(b*i - c*h)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), (b*f - c*e)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g)   ]
        invRow2 = [-(d*i - f*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g),(a*i - c*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), -(a*f - c*d)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g)   ]
        invRow3 = [ (d*h - e*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g), -(a*h - b*g)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g),  (a*e - b*d)/(a*e*i - a*f*h - b*d*i + b*f*g + c*d*h - c*e*g) ]
        inverseRotationMatrix = [invRow1, invRow2, invRow3] 
    
        inverseTransformMatrix =  [[0,1,0] ,[0,0,-1] ,[1,0,0]] # converts from inertial frame to camera frame, neglecting the rotation matrix
    
    
    #remember, transform^-1*rotation^-1*disp = cameraDisp
        dispInertial = [[deltaNorth], [deltaEast], [altitude] ]
        tempMatrix = [[0], [0], [0]] #handle multiplication of dispInertial with rotation^-1
        for row in range(0, 3):
            sum = 0.0
            for  column in range(0 ,3):
                sum += inverseRotationMatrix[row][column] * dispInertial [column][0]; 

        
            tempMatrix[row][0] = sum
        #print("disp inertial", dispInertial, " and after inverse rotation", tempMatrix)
    # now finish the multiplication through multiplying by inverse transform matrix
        cameraDisplacement = [[0] ,[0], [0]]
        for row in range(0, 3):
            sum = 0.0
            for  column in range(0 ,3):
                sum += inverseTransformMatrix[row][column] * tempMatrix [column][0]; 

            cameraDisplacement[row][0] = sum    
        #print("disp inerti", dispInertial, " and after both matrix multiplications ", cameraDisplacement)

    #convert back to a row vector instead of a column vector before returning, for simplicity 
        cameraDisplacementSimplified = [cameraDisplacement[0][0], cameraDisplacement[1][0],cameraDisplacement[2][0] ]
        cameraDisplacementSimplified[2] = abs(altitude); #simplify for use with the simulator by assuming altitude is same as height above ground, and target is flat on ground 
        cameraDisplacementSimplified[1]
        return cameraDisplacementSimplified 

    
def getApriltagDetection(roll_rads, pitch_rads, yaw_rads, quadNorth, quadEast, altitude, targetNorth, targetEast):
    cameraBoundsInertial = getCameraBoundsInertial(roll_rads, pitch_rads, yaw_rads, quadNorth, quadEast, altitude)
    xBounds = cameraBoundsInertial[0]
    yBounds = cameraBoundsInertial[1]
    print("camera bounds, x ", xBounds)
    print("camera bounds, y ", yBounds)
    
    inXBounds = ( (xBounds[0] < targetNorth) & (targetNorth < xBounds[1]) )
    inYBounds = ( (yBounds[0] < targetEast) & (targetEast < yBounds[1]) )
    if( inXBounds & inYBounds ):
        #need to figure out what the x y and z coordinates should be, IN THE CAMERA FRAME
        detectionCoords = calculateAprilTagDetection(roll_rads, pitch_rads, yaw_rads, quadNorth, quadEast, altitude, targetNorth, targetEast)
        return detectionCoords 
    else:
        blankDetection = []
        return blankDetection
    
    






    







	
	
######################################UTM CODE FROM MODULE "UTM"
class OutOfRangeError(ValueError):
    pass
	
__all__ = ['to_latlon', 'from_latlon']

K0 = 0.9996

E = 0.00669438
E2 = E * E
E3 = E2 * E
E_P2 = E / (1.0 - E)

SQRT_E = math.sqrt(1 - E)
_E = (1 - SQRT_E) / (1 + SQRT_E)
_E2 = _E * _E
_E3 = _E2 * _E
_E4 = _E3 * _E
_E5 = _E4 * _E

M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)
M2 = (3 * E / 8 + 3 * E2 / 32 + 45 * E3 / 1024)
M3 = (15 * E2 / 256 + 45 * E3 / 1024)
M4 = (35 * E3 / 3072)

P2 = (3. / 2 * _E - 27. / 32 * _E3 + 269. / 512 * _E5)
P3 = (21. / 16 * _E2 - 55. / 32 * _E4)
P4 = (151. / 96 * _E3 - 417. / 128 * _E5)
P5 = (1097. / 512 * _E4)

R = 6378137

ZONE_LETTERS = "CDEFGHJKLMNPQRSTUVWXX"


def to_latlon(easting, northing, zone_number, zone_letter=None, northern=None):

    if not zone_letter and northern is None:
        raise ValueError('either zone_letter or northern needs to be set')

    elif zone_letter and northern is not None:
        raise ValueError('set either zone_letter or northern, but not both')

    if not 100000 <= easting < 1000000:
        raise OutOfRangeError('easting out of range (must be between 100.000 m and 999.999 m)')
    if not 0 <= northing <= 10000000:
        raise OutOfRangeError('northing out of range (must be between 0 m and 10.000.000 m)')
    if not 1 <= zone_number <= 60:
        raise OutOfRangeError('zone number out of range (must be between 1 and 60)')

    if zone_letter:
        zone_letter = zone_letter.upper()

        if not 'C' <= zone_letter <= 'X' or zone_letter in ['I', 'O']:
            raise OutOfRangeError('zone letter out of range (must be between C and X)')

        northern = (zone_letter >= 'N')

    x = easting - 500000
    y = northing

    if not northern:
        y -= 10000000

    m = y / K0
    mu = m / (R * M1)

    p_rad = (mu +
             P2 * math.sin(2 * mu) +
             P3 * math.sin(4 * mu) +
             P4 * math.sin(6 * mu) +
             P5 * math.sin(8 * mu))

    p_sin = math.sin(p_rad)
    p_sin2 = p_sin * p_sin

    p_cos = math.cos(p_rad)

    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2

    ep_sin = 1 - E * p_sin2
    ep_sin_sqrt = math.sqrt(1 - E * p_sin2)

    n = R / ep_sin_sqrt
    r = (1 - E) / ep_sin

    c = _E * p_cos**2
    c2 = c * c

    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d

    latitude = (p_rad - (p_tan / r) *
                (d2 / 2 -
                 d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * E_P2)) +
                 d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * E_P2 - 3 * c2))

    longitude = (d -
                 d3 / 6 * (1 + 2 * p_tan2 + c) +
                 d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * E_P2 + 24 * p_tan4)) / p_cos

    return (math.degrees(latitude),
            math.degrees(longitude) + zone_number_to_central_longitude(zone_number))


def from_latlon(latitude, longitude, force_zone_number=None):
    if not -80.0 <= latitude <= 84.0:
        raise OutOfRangeError('latitude out of range (must be between 80 deg S and 84 deg N)')
    if not -180.0 <= longitude <= 180.0:
        raise OutOfRangeError('longitude out of range (must be between 180 deg W and 180 deg E)')

    lat_rad = math.radians(latitude)
    lat_sin = math.sin(lat_rad)
    lat_cos = math.cos(lat_rad)

    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    if force_zone_number is None:
        zone_number = latlon_to_zone_number(latitude, longitude)
    else:
        zone_number = force_zone_number

    zone_letter = latitude_to_zone_letter(latitude)

    lon_rad = math.radians(longitude)
    central_lon = zone_number_to_central_longitude(zone_number)
    central_lon_rad = math.radians(central_lon)

    n = R / math.sqrt(1 - E * lat_sin**2)
    c = E_P2 * lat_cos**2

    a = lat_cos * (lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = R * (M1 * lat_rad -
             M2 * math.sin(2 * lat_rad) +
             M3 * math.sin(4 * lat_rad) -
             M4 * math.sin(6 * lat_rad))

    easting = K0 * n * (a +
                        a3 / 6 * (1 - lat_tan2 + c) +
                        a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * E_P2)) + 500000

    northing = K0 * (m + n * lat_tan * (a2 / 2 +
                                        a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c**2) +
                                        a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * E_P2)))

    if latitude < 0:
        northing += 10000000

    return easting, northing, zone_number, zone_letter


def latitude_to_zone_letter(latitude):
    if -80 <= latitude <= 84:
        return ZONE_LETTERS[int(latitude + 80) >> 3]
    else:
        return None


def latlon_to_zone_number(latitude, longitude):
    if 56 <= latitude < 64 and 3 <= longitude < 12:
        return 32

    if 72 <= latitude <= 84 and longitude >= 0:
        if longitude <= 9:
            return 31
        elif longitude <= 21:
            return 33
        elif longitude <= 33:
            return 35
        elif longitude <= 42:
            return 37

    return int((longitude + 180) / 6) + 1


def zone_number_to_central_longitude(zone_number):
    return (zone_number - 1) * 6 - 180 + 3

#######################################END UTM CODE
            
			
			



import ros

from dji_sdk.dji_drone import DJIDrone
import dji_sdk.msg 

#Following 4 lines import the apriltags message format. 
import roslib
roslib.load_manifest("apriltags_ros")
from apriltags_ros.msg import AprilTagDetection
from apriltags_ros.msg import AprilTagDetectionArray




#import ros.geometry_msgs
#from geomemsg.Point
from geometry_msgs.msg import Point
from geometry_msgs.msg import PointStamped
from geometry_msgs.msg import Pose

from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Quaternion

import rospy

import std_msgs
import  std_msgs.msg




def maketag(xIn ,yIn ,zIn ): #to use, do something like tagCoords = getAprilTagDetection(arguments here); myTag = maketag(tagCoords[0], tagCoords[1], tagCoords[2])
            h = std_msgs.msg.Header()#std_msgs.msg.
            h.stamp = rospy.Time.now() # Note you need to call rospy.init_node() before this will work
            p = Point()#geometry_msgs.

            p.x=xIn
            p.y=yIn
            p.z=zIn   
            q = Quaternion()
            q.x=0 ;q.y=0; q.z=0; q.w=0;         
            
            poseU = Pose(p,q)
            poseS = PoseStamped(h, poseU)

            tag = AprilTagDetection()
            tag.size = 0.163513 #default from the launch file
            tag.id = 1 #the tad number I believe
            tag.pose = poseS 
            atda = AprilTagDetectionArray()
            atda.detections = [tag] 
            
            return atda;

			

def maketagSpecifyHeader(x, y, z, h):

            p = Point()#geometry_msgs.

            p.x=xIn
            p.y=yIn
            p.z=zIn   
            q = Quaternion()
            q.x=0 ;q.y=0; q.z=0; q.w=0;         
            
            poseU = Pose(p,q)
            poseS = PoseStamped(h, poseU)

            tag = AprilTagDetection()
            tag.size = 0.163513 #default from the launch file
            tad.id = 1 #the tad number I believe
            tag.pose = poseS 
            atda = AprilTagDetectionArray()
            atda.detections = [tag] 
            
            return atda;
		
			
			
			
			
def apriltagCallback(data):
	#basically, whenever I detect an Apriltags message, I want to simulate a detection (or not) based on where the camera is and our simulated tag is
	#Waiting for a physical apriltags message ensures the simulator has the same timing as the camera
    gimbal = GLOBAL_DRONE.gimbal 
    position = GLOBAL_DRONE.global_position
    quadEasting, quadNorthing, zoneNumber, zoneLetter = from_latlon(position.latitude, position.longitude)
    print("quad east %f, quad north %f " %(quadEasting, quadNorthing)) 
    print("target location east %f north %f " %(TARGET_EAST, TARGET_NORTH))
    detectionCoords = getApriltagDetection(gimbal.roll,gimbal.pitch, gimbal.yaw, quadNorthing, quadEasting, position.altitude, TARGET_NORTH, TARGET_EAST)
    mes = AprilTagDetectionArray() #initialize as empty to avoid errors
    if( (len(data.detections)>0) & (len(detectionCoords)>=3) ):	
        mes = maketagSpecifyHeader(detectionCoords[0], detectionCoords[1], detectionCoords[2], data.detections.pose.header);
    elif(len(detectionCoords)>=3):
	mes=maketag(detectionCoords[0], detectionCoords[1], detectionCoords[2]);
    if(detectionCoords == []):
        mes = AprilTagDetectionArray() #make it blank if the apriltag was out of view of the camera
    print("message to publish: ", mes); 
    GLOBAL_PUBLISHER.publish(mes);
	
def listener( topic="dji_sdk/tag_detections_for_simulator"):

    # In ROS, nodes are uniquely named. If two nodes with the same
    # node are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
	#I think since we have a node initialized elsewhere, we don't need to initialize here
    #rospy.init_node('listener', anonymous=True)

    rospy.Subscriber(topic, AprilTagDetectionArray, apriltagCallback)
   

   # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()			
			
            
def main():
    print("\n\nREMEMBER, NEED TO FEED THE APRILTAGS TOPIC TO THE SIMULATOR, AND HAVE THE SIMULATOR PUBLISH TO dji_sdk/tag_detections !!!! \n\n")
    global GLOBAL_PUBLISHER
    GLOBAL_PUBLISHER = rospy.Publisher('/dji_sdk/tag_detections', AprilTagDetectionArray, queue_size=1)
    #rospy.init_node('tagPublisher', anonymous=True)

    drone = DJIDrone() #this calls a rospy.init_node() function
    rate = rospy.Rate(10)
    global GLOBAL_DRONE 
    GLOBAL_DRONE = drone

	
    listener("dji_sdk/tag_detections_for_simulator")
	#while not rospy.is_shutdown():
    #    rate.sleep()

main()
