**How to install it:**

This is the code for the localization simulator. The simulator can work both in Windows and Linux.

In Windows: 
- Install the VcXsrv Windows X Server (you can download it from here: https://sourceforge.net/projects/vcxsrv/). While installing, go with all the default settings, but do note to check “Disable access control”.
- Launch the x server. Try looking for xlaunch.exe at the default install location “C:\Program Files\VcXsrv\xlaunch.exe”
- Download the win_start.bat file from GitLab.
- Run the win_start.bat

In Linux:
- Install "x11-xserver-utils" Package by running this command: sudo apt-get install x11-xserver-utils.
- Download the lin_start.sh file from GitLab.
- Run lin_start.sh file. (You may need to make it executable first using the command: chmod +x lin_start.sh)

If you don't want to use Docker:

- Install all the requirements with the command: pip install -r requirements.txt
- Run the file print_path.py

**How to use it:**

_On the left side of the GUI you will see some text boxes, buttons, etc._
- In the first one you have to complete the Broker IP in which the messages will be sent to (e.g. 192.168.100.12).
- In the second one you have to complete the source id (e.g. FR001#FR).
- The "send to broker" button should be clicked whenever your scenario is ready and you want to send the messages to the Broker.
- The "save session" button should be clicked whenever your want to save a scenario and run it in the future even if you have closed the program. You can either create a new folder or use an existing folder for saving the messages.
- The "load session" button should be clicked whenever you wish to load a session that has been previously saved.
- The Tile Server is an Option Menu, where you can choose the type of the map you wish to have.
- The Appearance Mode is an Option Menu, where you can choose if you want dark or light mode.
- The 4 check boxes give you the freedom to choose which tools you wish to have in your simulator, the text boxes next to them (time diff (s)) are for you to complete the time difference (in seconds) between each message sent by each tool, the switches next to the are for enabling noise to the data. Adding random noise means that the point will be near the "real" point, but it will have a distance (random number coming from a normal distribution) from it, in a random direction (random number comming from a normal distribution in (0,360)). The mean of the normal distribution is always 0 and the standard deviation is being definded by the user in the textbox noise std.
- The last text box is the speed (in meters/second) that the FR has.
- At the bottom of the left side you can see a percentage. This is the percentage of the progress of the messages sent to the broker.

_On the right side:_
- On the top, there is a search bar to search the place that you wish easily.
- You can zoom in/out using either the +/- buttons or using the scroll wheel of your mouse.
- By right-clicking on the map you can either copy the coordinates to the clipboard or add a marker.
- By adding multiple markers you create a path from which the FR is supposed to come from (the path starts from the first marker you create and ends in the penultimate one).
- By the time you have completed the text and check boxes with the values you wish and you have created the path you wish, you are ready to send the messages to the Broker. 
- The messages will be sent and will have as start time the current date and time, as coordinates the place that the FR would be in x seconds walking 
with x speed and heading based on the next steps on the path. The last two messages will have the same heading.
