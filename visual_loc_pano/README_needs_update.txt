INSTRUCTIONS:

With the term "calibration" we refer to the registration of 3 different GPS-tagged points to the stella internal frame of reference.
This means finding the local coordinates of the 3 known GPS points.

The calibration can be done in 3 ways. Once you have started the tool, move as close as possible to one of the reference points (e.g "point1").
To signal the tool that its current local position is also the point1-GPS in the global frame, you can either:
* look at the QR code which encodes the number "1" (just print 3 QR codes with a free online tool that write "1", "2" and "3" accordingly);
* use the CERTH android app and push the "1" button on the UI;
* (easiest) push the button "1" on the laptop keyboard.
Repeat the same process for all 3 points accordingly.

You can immediately see in the tool cmd that the message changes from "calibrating" to "calibrated".
Note that for the calibration to be successfull, the 3 points should have different local coordinates.
So, in case stella loses tracking for a few seconds (there are no colorfull dots on the pangolin window), the local coordinates do not change,
so the calibration point taken will be invalid. You can still move and repeat the process on the lost point, when it finds tracking again
until all points are found and are different. The tool starts sending to the broker, only after the calibration is successful. 

There are 4 modes of opperation for the tool. Each one is accessed by initiating the tool using one of 4 .sh scripts:
* 2_run_one_shot.sh
* 4_run_map_area.sh
* 5_run_use_map.sh
* 6_run_use_map_calibrated.sh
Do not forget to allways terminate the tool using the script * 3_kill_docker.sh

NOTE THAT: Scripts 2,5,6 need the GPS info of the 3 reference points. Their lat, lon and alt. So, edit them accordingly.
Scripts 5,6 need a folder on the host pc to be visible by the docker container to allow loading the model (both 5 and 6) and the calibration data (6 only).
It is recommended that you use the folder that contains all the .sh scripts.
To use another one, you should edit the -v argument of the scripts 5 and 6 to point to a different folder changing it from
/home/rescuer/Documents/GitHub/Localization/visual_loc_pano:/home/rescuer/Desktop/visual_loc_pano TO <another_one>:/home/rescuer/Desktop/visual_loc_pano

Bellow, there some details for each one of the modes of operation:

* ONE SHOT means the operation without having the stella-created area model. It is the basic, naive operation. It makes the model as you move.

* MAP AREA is used to create and save the model of the area to be used later with the rest of the modes. To map the area, start the tool and take
a long walk inside it. Be carefull that stella does not lose tracking often
(you should constantly see colorfull dots in the pangolin window and the map allways moving and growing, not staying still for more than a second).
When you are done, press "Terminate" on the pangolin window and then use 3_kill_docker.sh to automatically download the model.
 
* USE MAP is the mode where you have the area model and you only need to calibrate.
 After you conduct calibration, the local coordinates of the 3 reference points are saved in a "local_points.txt" file so that you can use the last mode.

* USE MAP CALIBRATED is the mode where you have both the model of the area and the "local_points.txt" with the calibration data.
 This means the tool starts pre-calibrated and is ready to be used immediatelly without the need for calibration.

 <3<3<3
