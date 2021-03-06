#!/usr/bin/env python

from dji_sdk.dji_drone import DJIDrone
import dji_sdk.msg 
import time
import sys
import math

import ros
#import ros.geometry_msgs
#from geomemsg.Point
from geometry_msgs.msg import Point
from geometry_msgs.msg import PointStamped
import rospy
import std_msgs
import  std_msgs.msg

h = std_msgs.msg.Header()#std_msgs.msg.
p = Point()#geometry_msgs.

#drone = DJIDrone()#rospy.init_node('sampleAnglePublisher')
h.stamp = rospy.Time.now() # Note you need to call rospy.init_node() before this will work
p.x=0
p.y=0
p.z=150 

ps =PointStamped(h,p)  #geometry_msgs.msg.PointStamped(h,p)





pub = rospy.Publisher('/dji_sdk/desired_angle', PointStamped, queue_size=1)
pub.publish(ps)

#put on very few lines for ease of pasting
def makepoint(roll, pitch, yaw):
        h = std_msgs.msg.Header();p = Point();h.stamp = rospy.Time.now(); # Note you need to call rospy.init_node() before this will work
        p.x=roll;p.y=pitch;p.z=yaw;ps = PointStamped(h,p);
        return ps;


def main():
    pub = rospy.Publisher('/dji_sdk/desired_angle', PointStamped, queue_size=2)
    rospy.init_node('anglePublisher', anonymous=True)
    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        mes = makepoint(10,10,20);
        pub.publish(mes);
        rate.sleep()

main()
#to make it work in console, paste in the following: (uncomment first):
##from dji_sdk.dji_drone import DJIDrone
##import dji_sdk.msg 
##import time
##import sys
##import math
##
##import ros
###import ros.geometry_msgs
###from geomemsg.Point
##from geometry_msgs.msg import Point
##from geometry_msgs.msg import PointStamped
##import rospy
##import std_msgs
##import  std_msgs.msg
###put on very few lines for ease of pasting
##def makepoint(roll, pitch, yaw):
##        h = std_msgs.msg.Header();p = Point();h.stamp = rospy.Time.now(); # Note you need to call rospy.init_node() before this will work
##        p.x=roll;p.y=pitch;p.z=yaw;ps = PointStamped(h,p);
##        return ps;
##
##pub = rospy.Publisher('/dji_sdk/desired_angle', PointStamped, queue_size=1)
##rospy.init_node('anglePublisher', anonymous=True)
##mes = makepoint(10,10,20);
##pub.publish(mes);
