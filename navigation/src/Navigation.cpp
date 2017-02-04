#include "Navigation/Navigation.h"
#include "ros/ros.h"
#include "std_msgs/String.h"
#include <geometry_msgs/PointStamped.h>
#include <dji_sdk/dji_drone.h>
#include <signal.h>
#include <sstream>
#include <iostream>



using namespace std;
// public methods

geometry_msgs::PointStamped desiredGimbalPoseDeg;

extern geometry_msgs::Point _droneUtmPosition;
extern geometry_msgs::Point _targetGpsPosition;
extern geometry_msgs::Point _targetUtmPosition;

extern ros::Publisher gimbal_pose_pub1;

extern int targetLocked;

Navigation::Navigation()
{     
    ros::NodeHandle nh;
    m_ptrDrone = new DJIDrone(nh);

}

Navigation::Navigation(ros::NodeHandle& nh)
{    
    m_ptrDrone = new DJIDrone(nh);
}


Navigation::~Navigation()
{    

}

void Navigation::RunNavigation(void)
{
    int inputValue;
    
    DJIDrone& drone = *m_ptrDrone;
    
    bool bIsInputValid = false;
    bool bIsExitRequested = false;
    
    
    
    while(1)
    {
        ros::spinOnce();
        
        if (bIsExitRequested)
        {
            break;
        }

        DisplayMainMenu();
                    
        if (!bIsInputValid)
        {
            bIsInputValid = true;
        }
        
        std::cout << "Enter Input Value: ";
        std::cin >> inputValue;
         
        switch (inputValue)
        {
            case 1: // request control 
                drone.request_sdk_permission_control();
                break;
                
            case 2: // release control 
                drone.release_sdk_permission_control();
                break;
                	
            case 3: // arm 
				drone.drone_arm();
                break;

			case 4: // disarm
				drone.drone_disarm();
                break;
                
            case 5: // take off 
                drone.takeoff();
                break;
                
            case 6: // landing
                drone.landing();
                break;
                                
            case 7: // go home
                drone.gohome();
                break;
                
            case 8: // draw circle sample
                DrawCircleExample();
                break;
                      
            case 9: // search for target
                SearchForTarget();
                break;

			case 10: // Navigation test
                NavigationTest();
                break;
				
			case 22: // Waypoint Mission Upload
				Waypoint_mission_upload();
				break;
                     
			case 25: // Mission Start
				drone.mission_start();
				break;
				
			case 26: //mission pause
				drone.mission_pause();
				break;
				
			case 27: //mission resume
				drone.mission_resume();
				break;
				
			case 28: //mission cancel
				drone.mission_cancel();
				break;
				
            case 99: // Exit the program 
                bIsExitRequested = true;
                std::cout << "Press Ctrl-C to quit.\n";
                break;
                
            default: // It will take care of invalid inputs 
                std::cout << "Undefined input value.";
                bIsInputValid = false;
                break;
        }
        
    }
}



// private
void Navigation::DisplayMainMenu(void)
{
    printf("\r\n");
    printf("+-------------------------- < Main menu > -------------------------+\n");
	printf("| [1]  Request Control          | [21] Set Msg Frequency Test      |\n");	
	printf("| [2]  Release Control          | [22] Waypoint Mission Upload     |\n");	
	printf("| [3]  Arm the Drone            | [23]                             |\n");	
	printf("| [4]  Disarm the Drone         | [24] Followme Mission Upload     |\n");	
	printf("| [5]  Takeoff                  | [25] Mission Start               |\n");	
	printf("| [6]  Landing                  | [26] Mission Pause               |\n");	
	printf("| [7]  Go Home                  | [27] Mission Resume              |\n");	
	printf("| [8]  Draw Circle Sample       | [28] Mission Cancel              |\n");	
	printf("| [9]  Search for Target        | [29] Mission Waypoint Download   |\n");	
	printf("| [10] Local Navigation Test    | [30] Mission Waypoint Set Speed  |\n");	
	printf("| [11] Global Navigation Test   | [31] Mission Waypoint Get Speed  |\n");	 
	printf("| [12] Waypoint Navigation Test | [32] Mission Followme Set Target |\n");	
    printf("|                                    \n");
    printf("| [54] Geolocalization/Gimbal tests and AprilTag recognition)   |\n");
    printf("|                                    \n");
    printf("| [99] Exit                           \n");
    printf("+-----------------------------------------------------------------+\n");
    printf("input a number then press enter key\r\n");
    printf("use `rostopic echo` to query drone status\r\n");
    printf("----------------------------------------\r\n");
}


void Navigation::SearchForTarget(void)
{
    ROS_INFO("Starting to search for target-----------------------");

    int limitRadius = 10; 
    int flyingRadius = 1;
    int droneAltitude = 3;
    int Phi = 0;

    
    DJIDrone& drone = *m_ptrDrone;


    desiredGimbalPoseDeg.point.x = 0.0;  // roll
    desiredGimbalPoseDeg.point.y = -45.0;  // pitch
    desiredGimbalPoseDeg.point.z = 0.0;   // yaw 
    
    ROS_INFO("Local Position: %f, %f\n", drone.local_position.x, drone.local_position.y);
    float x_center = drone.local_position.x;
    float y_center = drone.local_position.y;
                
    float circleRadiusIncrements = 2.0;
    float gimbalYawIncrements = 1;

    while(flyingRadius < limitRadius && 0 == targetLocked)
    {
        for(int i = 0; i < 1000 && 0 == targetLocked; i ++)
        {   
            //set up drone task
            float x =  x_center + flyingRadius*cos((Phi/120));
            float y =  y_center + flyingRadius*sin((Phi/120));
            Phi = Phi+1;
            drone.local_position_control(x, y, droneAltitude, 0);
            
            //set up gimbal task
            if(desiredGimbalPoseDeg.point.z > 30.0) //if yaw is greater than or equal to 30deg. 
                gimbalYawIncrements = -1;         //gimbal swing back
            else if(desiredGimbalPoseDeg.point.z < -30.0) //if yaw is less than or equal to 30deg.
                gimbalYawIncrements = 1;          //gimbal swing back again
            desiredGimbalPoseDeg.point.z += gimbalYawIncrements;
            gimbal_pose_pub1.publish(desiredGimbalPoseDeg);
            
            
            usleep(20000);

        } 
        
        flyingRadius += circleRadiusIncrements; 
        
    }
    
    if(flyingRadius < 20)
        ROS_INFO("Target FOUND!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    else if(flyingRadius > 20)
        ROS_INFO("Didn't find anything! Try to change searching range or search again. ");


}


void Navigation::DrawCircleExample(void)
{
    std::cout << "Enter the radius of the circle in meteres (4m < x < 10m)\n";
    int desiredRadius;
    std::cin >> desiredRadius;   

    std::cout << "Enter height in meteres (Relative to take off point. 1m < x < 5m) \n";
    int desiredAltitude;
    std::cin >> desiredAltitude;  
    
    int flyingRadius = std::max(4, std::min(10, desiredRadius));
    ROS_INFO("The flying radius is %d meters\n", flyingRadius);
    
    int droneAltitude = std::max(1, std::min(5, desiredAltitude));
    ROS_INFO("The drone altitude is %d meters\n", droneAltitude);
                                    
    
    DJIDrone& drone = *m_ptrDrone;
    
    ROS_INFO("Local Position: %f, %f\n", drone.local_position.x, drone.local_position.y);

    float x_center = drone.local_position.x;
    float y_center = drone.local_position.y;
                
    float circleRadiusIncrements = 0.01;
	        
    for(int j = 0; j < 1000; j ++)
    {   
        if (circleRadiusIncrements < flyingRadius)
	    {
            float x =  x_center + circleRadiusIncrements;
            float y =  y_center;
	        circleRadiusIncrements = circleRadiusIncrements + 0.01;
            drone.local_position_control(x, y, droneAltitude, 0);
            usleep(20000);
	    }
        else
	    {
            break;
        }
    }
    
    int Phi = 0;
    
    for(int i = 0; i < 1000; i ++)
    {   
        float x =  x_center + flyingRadius*cos((Phi/120));
        float y =  y_center + flyingRadius*sin((Phi/120));
        Phi = Phi+1;
        drone.local_position_control(x, y, droneAltitude, 0);
        usleep(50000);
           
        ROS_INFO("Local Position: %f, %f\n", drone.local_position.x, drone.local_position.y);
        ROS_INFO("Global Position: lon:%f, lat:%f, alt:%f, height:%f\n", 
                    drone.global_position.longitude,
                    drone.global_position.latitude,
                    drone.global_position.altitude,
                    drone.global_position.height
                 );
                         
    } 
}

void Navigation::NavigationTest(void)
{
	DJIDrone& drone = *m_ptrDrone;

	float x_start = drone.local_position.x ;
	float y_start = drone.local_position.y ;

    float x =  x_start;
    float y =  y_start + 5.0;
	
	while(drone.local_position.z > 0 ) 
	{  
    	drone.local_position_control(x, y, -0.1, 0);
		usleep(20000);
	}

}

void Navigation::Waypoint_mission_upload(void)
{
    static float x;
    static float y;
    float z;
    float delta_x; 
    float delta_y;
    float delta_z;
    float distance;
                
    DJIDrone& drone = *m_ptrDrone;

    ROS_INFO_STREAM("Target GPS Position: X = " << _targetGpsPosition.x 
                           << " \nY = " << _targetGpsPosition.y 
                           << " \nZ = " <<  _targetGpsPosition.z);


    x = _targetGpsPosition.x;
	y = _targetGpsPosition.y;
	z = drone.global_position.height;
	distance = (x - drone.global_position.altitude)*(x - drone.global_position.altitude) + (y - drone.global_position.longitude)*(y - drone.global_position.longitude); 

    while(distance > 0.000001) 
	{ 
        drone.global_position_control(x, y, z, 0);
        usleep(20000);

		distance = (x - drone.global_position.altitude)*(x - drone.global_position.altitude) + (y - drone.global_position.longitude)*(y - drone.global_position.longitude);
    }


}





