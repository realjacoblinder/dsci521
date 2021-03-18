## DSCI 521 - Chess Helper
The core to this is the Dash server, which needs to have Dash and Plotly installed, both of which are available using pip. 

The dash server can be run in your terminal by running index.py in python. After an initial load time involving some data preprocessing, the console should print out the local address the server is running on. 

New chess data can easily be added by putting a new PGN file in the data folder and updating the code in pieces.py and players.py to read from the new filename. 