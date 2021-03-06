 #include "ros/ros.h" //note this must come before including 
#include <string>
#include <sstream> //stringstream, for turning all PID controller params into a string for ROS
#include <stdlib.h>    //for absolute value
#include <ctype.h> //for isspace

 #include <fstream>
#include <sstream>
 #include <vector>
 #include <algorithm>    // std::transform
#include<cstring> //std::strlen
 #include "std_msgs/String.h" //for publishing to ROS
 bool pidPublisherInitialized = false; 
 ros::Publisher PID_PARAM_PUBLISHER; //for debugging and general info

 void initializePidPublisher()
 {
   int argc = 0;
   char *argv[1]; *argv = NULL; //change later if you wish to add arguments

  ros::init(argc, argv, "pidParamInfo");
  ros::NodeHandle n;
  PID_PARAM_PUBLISHER = (n).advertise<std_msgs::String>("/dji_sdk/pidParams", 2); // queue size of 2 seems reasonable
  pidPublisherInitialized = true; 
 }
 
 
//if it receives a command like "go to angle 181 degrees", when it reaches 180.1,
//it will change the sensor measure from 180.1 to -179.9
//and the PID will try to spin another 360.9 degrees! It will continue until the gimbal can't physically turn any more
//stop it by limiting it to +- 180 degrees
//this function will be used both when calculating the error and when recieving the commands from the subscriber
double limitAngleToPi_DjiUnits(double angle_djiUnits)
  {
    while(angle_djiUnits < -1800.0)
        {angle_djiUnits += 3600.0;}
    while(angle_djiUnits > 1800.0)
        {angle_djiUnits -= 3600.0;}
    return angle_djiUnits;
   }



//another option that might be better at preventing mechanical stoppage is to
// only allow it to swing within +- 175 degrees, and eliminate "shortcutting"
//So if You went from -175 to +175 you'd swing the full positive 350, not -10
//that would eliminate a lot of the mechanical stoppage problems
double limitAngleTo175Degs_DjiUnits(double angle_djiUnits)
  {
    angle_djiUnits = limitAngleToPi_DjiUnits( angle_djiUnits);
    if (angle_djiUnits > 1750.0)
            {angle_djiUnits = 1750.0;}
    else if (angle_djiUnits < -1750.0)
             {angle_djiUnits = -1750.0;}   

    return angle_djiUnits;
   }
 

//need following behavior patterns:
//All angles will be between +-180 degrees (can be handled with other fucntions)
// Angles should use shortcuts (ie, going from 175 to -175 should use a +10 degree swing, not -350
// Will avoid mechanical lockup by using a full swing, instead of shortcutting, when the resulting angle would send it beyond 270 degrees of total travel.
//This can be tracked as follows:
    // If you've been traveling in a positive direction from 0, then sign of angle changes, and then the desired angle is between 90 and -90, you need to "unwind" (note that some of this would happen anyway, and I'm not sure what the sign of the movement would need to be)
     // If you've been traveling in a negative direction from 0, then sign of angle changes, and then the desired angle is between 90 and -90, you need to "unwind" (note that some of this would happen anyway, and I'm not sure what the sign of the movement would need to be)
  //NOTE: I assume that the desired and current angles are already between +- 180
bool needToUniwndGimbal (double desiredAngle_DjiUnits ,double currentAngle_DjiUnits ,int startingSign/*make positive if you started traveling in positive direction, negative in negative direction, 0 if not outside of a small range from start*/ ,double tolerance_DjiUnits, bool verbose) //tolerance is how close to the 180 -180 dividing line you want to get. So a tolerance of 50 (50 DjiUnits, 5 degrees) would consider that zone to be between 175 and -175 (as in 175 to 180 then -180 to -175, only a 10 degree zone)
    {   

      if(verbose)
            {std::cout <<"desired angle (tenths of degree" << desiredAngle_DjiUnits <<" bool1 :" << (bool)(startingSign >=1) << " bool2A :" <<  (bool)(abs(currentAngle_DjiUnits) > 1800 - tolerance_DjiUnits) << " bool2B :" << (bool)(currentAngle_DjiUnits < -1.0*(900-tolerance_DjiUnits)) << " bool3 :" << (bool)( -900 <= desiredAngle_DjiUnits && desiredAngle_DjiUnits <=900) << "\n";  }

//note: based on testing in python, a negative speed in yaw is always counterclockwise (from the drone's perspective)
      if (startingSign >=1 && (  (abs(currentAngle_DjiUnits) > 1800 - tolerance_DjiUnits) || currentAngle_DjiUnits < -1.0*(900-tolerance_DjiUnits) )&& ( -900 <= desiredAngle_DjiUnits && desiredAngle_DjiUnits <=900)  )
        {return true;}
      else if (startingSign <= -1 && (  (abs(currentAngle_DjiUnits) > 1800 - tolerance_DjiUnits) || currentAngle_DjiUnits > (900-tolerance_DjiUnits) )&& ( -900 <= desiredAngle_DjiUnits && desiredAngle_DjiUnits <=900)  )
        {return true;}        
      else
        {return false;}
    }



using namespace std;
  
  

class PIDController {
 public: //declare everything public right now for convenience
   
      vector<std::string> listOfParams = {"kp", "kd", "ki", "deadzone_djiunits"} ;

     static constexpr double min_Kp = 0.125 ; //can't assign a value lower than this in order to rpevent user errors. Use 0.125 since it can be represented precivesly using floats
	std::string pidId = "NO ID ASSIGNED"; //assign this on creation for debugging on ROS
 
	double Kp = 3.0; //initial guess of 0.5 was somewhat slow, try 0.8 was whippy, 2 works well, try 4 for more speed
	double Kd = 0.0; //initial guess
	double Ki = 0.0; //initial guess was 0.0
	
	double deadZone_DjiUnits = 10.0 ;//anything less than 1 degrees, we don't care
	
	double accumulatedError = 0.0; //need to start out at 0-element
	
    double calculateDesiredVelocity(double error, double timeSinceLastStep) {
													if (abs(error) < deadZone_DjiUnits) 
														{return 0.0;} //ie don't move at all
								
													double derivative = 0.0;
													if ( abs(timeSinceLastStep) > 0.001 ) //prevent divide by 0-element
													     { derivative = (error - accumulatedError)/timeSinceLastStep ;}
													accumulatedError += error*timeSinceLastStep;//preform discrete integral 
													if ( ((error > 0 )&&(accumulatedError < 0)) || ( (error < 0 )&&( accumulatedError > 0)) )
															{accumulatedError = 0.0; } //prevent windup
													return (Ki*accumulatedError + Kd*derivative + Kp*error);
													}

	void publishAllParamValues()
			{
			 if(pidPublisherInitialized == true)
				{			
					std::stringstream ss;
					ss << "PID controller params " << "ID: " << pidId << " Kp: " << Kp << " Kd: " << Kd << " Ki " << Ki << " deadzone " << deadZone_DjiUnits << " \n ";
					std::string messageString = ss.str();
                    std_msgs::String msg;
                    msg.data = messageString;
					PID_PARAM_PUBLISHER.publish(msg);
				}
			}
													
};
double getRequiredVelocityPID(double desiredAngle_djiUnits, double currentAngle_djiUnits ,double latest_dt ,PIDController * pidInstance)
	{
		double currentError = desiredAngle_djiUnits - currentAngle_djiUnits;

		return (*pidInstance).calculateDesiredVelocity(currentError, latest_dt);
	
	}

double getRequiredVelocityPID_yaw(double desiredAngle_djiUnits, double currentAngle_djiUnits, int signOfMovement/*make positive if you started traveling in positive direction, negative otherwise*/ ,bool& isUnwinding, double tolerance_DjiUnits ,double latest_dt ,PIDController * pidInstance)
	{
//bool testt =false;
//note: based on testing in python, a negative speed in yaw is always counterclockwise (from the drone's perspective)
		double currentError = desiredAngle_djiUnits - currentAngle_djiUnits;
        bool needToUnwind = needToUniwndGimbal (desiredAngle_djiUnits ,currentAngle_djiUnits, signOfMovement, tolerance_DjiUnits, false);
        if (needToUnwind == false && isUnwinding == false)
            {currentError = limitAngleToPi_DjiUnits(currentError);} //uncomment this if you aren't limiting the angles to avoid rotations of more than 180 degrees

        else if(needToUnwind == true || isUnwinding == true) //the isUnwinding prevents it from ceasing to unwind partway through, which causes oscillations 
            {    //testt = true;
                if(isUnwinding == false)
                    {isUnwinding = true;}


                if (signOfMovement >= 1 && needToUnwind == true)
                        {while(currentError >= 0.0) 
                            {currentError -= 3600;}
                        //testt=true;
                        }
               else if (signOfMovement <= -1)
                        {while(currentError <= 0.0) 
                            {currentError += 3600;}
                        }             
              //if it's gone too far. Too far and sign = 1 means it's gone too far clockwise, too far and sign = -1 means it's gone too far counterclockwise. So if the starting sign was 1, we want to always return a negative value if it's gone too far. If the starting sign was -1, we want to always return a positive value if it's gone too far.  With the current set up, sign of the error is the sign of velocity, so we'd always want a negative error if starting sign was 1. 
            }

		double requiredVelocity =  (*pidInstance).calculateDesiredVelocity(currentError, latest_dt);
        //if(testt){requiredVelocity = -1.0*abs(requiredVelocity);}
        return requiredVelocity;
	
	}

	
void setParamFromString(PIDController* pidInstance, std::string param, double paramVal)
{
  std::transform(param.begin(), param.end(), param.begin(), ::tolower); //converts to lowercase for ease of analysis
  if(param.compare("kp")	 == 0 ) //the std::string::compare method returns 0 if the strings are equal
	{ 
	  if(paramVal >= (PIDController::min_Kp)) //this shouldn't be 0, and we want some gaurantee of that
		{(*pidInstance).Kp = paramVal;}
	  
	}
  else if(param.compare("kd")	 == 0 )
	{
	  (*pidInstance).Kd = paramVal;
	  
	}
  else if(param.compare("ki")	 == 0 )
	{
	  (*pidInstance).Ki = paramVal;
	  
	}
	else if(param.compare("deadzone")	 == 0 )
	{
	  (*pidInstance).deadZone_DjiUnits = paramVal;
	  
	}
	else if(param.compare("deadzone_djiunits")	 == 0 )
	{
	  (*pidInstance).deadZone_DjiUnits = paramVal;
	  
	}
	else if(param.compare("placeholder")	 == 0 ) //change this to add future parameters
	{
	  ;
	  
	}
}
//Intended to read parameters from a text file in a format like the following:
//(beginning of file here)
// Kp: 3.0*\
// Kd: 1.50
// Deadzone: 10.350
// (end of file here)
//http://stackoverflow.com/questions/7868936/read-file-line-by-line

void setParamsFromFile(PIDController* pidInstance, std::string fileName, std::vector<std::string> listOfParams)
        {
		char charsToRemove[] = ":;,"; //formatting characters that could occur that you wish to remove	
        std::ifstream infile(fileName);

        std::string line;
        while (std::getline(infile, line))
            {

				std::transform(line.begin(), line.end(), line.begin(), ::tolower); //converts to lowercase for ease of analysis

				for (unsigned int i=0; i<listOfParams.size(); i++)
					{		
						int paramPositionInString = line.find(listOfParams.at(i));
						if( paramPositionInString != std::string::npos)
						{
							std::string valString = line.substr( paramPositionInString+(listOfParams.at(i)).length() ); // so in a string like  "Kp: 5" this would result in ": 5".
							//To remove the colon and the whitespace, use the methods found here: http://stackoverflow.com/questions/5891610/how-to-remove-characters-from-a-string
							//and here: http://stackoverflow.com/questions/83439/remove-spaces-from-stdstring-in-c
                        //I had an error resolving std::isspace, the solution is shown here: http://stackoverflow.com/questions/21578544/stdremove-if-and-stdisspace-compile-time-error
auto myIsspace = [](unsigned char const c) { return std::isspace(c); };
std::remove_if(valString.begin(), valString.end(), myIsspace); 
							 valString.erase(std::remove_if(valString.begin(), valString.end(), myIsspace), valString.end()); //removes whitespace
							 std::string noSpaces =  valString ; //now that whitespaces are removed, put this as a new variable for easier debugging
							  for ( int i = 0; i < std::strlen(charsToRemove); ++i)
							    {noSpaces.erase (std::remove(noSpaces.begin(), noSpaces.end(), charsToRemove[i]), noSpaces.end());} //removes the colon and comma and some other symbols if present
							try
								  {
									double paramVal = stod(noSpaces);// parses string for valid double, but may return 0.0 if it's invalid
									setParamFromString(pidInstance, listOfParams.at(i), paramVal);
								    }
							catch(...) //catch(...) means it will catch any exception
									{
										
									 std::cout<<"unable to read double in paramater " << 	listOfParams.at(i) <<"\n";
									}
							break;//end the for loop
						}
					}
                //process the string
                //It should do the following:
                // Check each line for a param name
                //if the param name is in our list, strip the parameter name from the string, read the remaining value, and then set that parameter for the PID controller
                ;
            }
        }
		
//string reading verified with the following code on http://cpp.sh
/*
// Example program
#include <iostream>
#include <string>
#include <algorithm>    // std::transform

#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <stdio.h>
#include<cstring>
std::vector<std::string> listOfParams;


void setParamsFromFile( std::string line, std::vector<std::string> listOfParams)
        {


		char charsToRemove[] = ":;,"; //formatting characters that could occur that you wish to remove	
        //std::ifstream infile(fileName);
        //std::string line;
        //while (std::getline(infile, line))
        //    {
				std::transform(line.begin(), line.end(), line.begin(), ::tolower); //converts to lowercase for ease of analysis

				for (unsigned int i=0; i<listOfParams.size(); i++)
					{		
						int paramPositionInString = line.find(listOfParams.at(i));
						if( paramPositionInString != std::string::npos)
						{
						    std::cout <<"unprocessed string " <<line <<" \n";
							std::string valString = line.substr( paramPositionInString+(listOfParams.at(i)).length() ); // so in a string like  "Kp: 5" this would result in ": 5".
							//To remove the colon and the whitespace, use the methods found here: http://stackoverflow.com/questions/5891610/how-to-remove-characters-from-a-string
							//and here: http://stackoverflow.com/questions/83439/remove-spaces-from-stdstring-in-c
							  valString.erase(remove_if(valString.begin(), valString.end(), isspace), valString.end()); //removes whitespace
							std::string noSpaces =valString;
							std::cout <<"without whitespace " << noSpaces <<" \\ " << valString << "\n";
							  for ( int i = 0; i < std::strlen(charsToRemove); ++i)
							    {noSpaces.erase (std::remove(noSpaces.begin(), noSpaces.end(), charsToRemove[i]), noSpaces.end());} 
							std::cout <<"processed string " << noSpaces <<" \n";
							try
								  {
									double paramVal = stod(noSpaces);// parses string for valid double, but may return 0.0 if it's invalid
								std::cout <<"parameteR "<<listOfParams.at(i) << " should be : " << paramVal <<"\n";
								    }
							catch(...) //catch(...) means it will catch any exception
									{
										
									 std::cout<<"unable to read double in paramater " << 	listOfParams.at(i) <<"\n";
									}
							break;//end the for loop
						}
					}
                //process the string
                //It should do the following:
                // Check each line for a param name
                //if the param name is in our list, strip the parameter name from the string, read the remaining value, and then set that parameter for the PID controller
                ;
            //}
        }


int main()
{   
listOfParams.push_back("kp");
listOfParams.push_back("deadzone");
std::string str1 = "DeadZoNe: 5"; //test alternate capitalizations
std::string str2 = "kp : 7 "; //test extra whitespaces
std::string str3 = "kp, :72.884  "; //test if comma is typed instead of colon, and also if it's a decimal
std::string str4 = "notAParameter : 0.44"; // test if nonexistant parameter is entered 
std::string str5 = "kp : 0.0"; // test if it's 0

setParamsFromFile(str1 ,listOfParams);
setParamsFromFile(str2 ,listOfParams);
setParamsFromFile(str3 ,listOfParams);
setParamsFromFile(str4 ,listOfParams);
setParamsFromFile(str5 ,listOfParams);

std::string q = " 0.44 , ";
std::cout << "stod " << stod(q) << "\n"; //demonstrates the stod function
  
}

*/
		
