Polygonner!
A simple pygame game where the player avoids larger polygons
to stay alive and eats smaller polygons to grow.

Gabriel Mukobi - 2019/04/18


### Requirements ###
1) Python 3.7+ - https://www.python.org/
2) pygame - install in the command line with 'py -m pip install pygame'


### How to Run ###
1) Open a command line (e.g. Terminal, Powershell, cmd)
2) Install previous Requirements
3) Navigate to 'Polygonner' folder
3) Run 'py game.py'


### How to Run ###
Eat the smaller polygons to grow larger.
Avoid the larger ones, or you'll be a gonner.
Arrow keys to move, Enter to start, Esc to quit.


### Features ###
Enemies and player rotate
Enemies are colored based on relative size to player
Accurate collision based on reading color codes in enemy fill colors
Enemies and players have a variety of number of sides
Enemy sizes scale with player size
Score keeping system
Title screen with instructions
Game over screen
Music and sound effects
Enemy spawn rate increases with score
Code refactored/renamed for scalability and PEP8 conformity
Code documented with docstrings, comments