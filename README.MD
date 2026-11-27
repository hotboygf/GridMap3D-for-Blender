# GridMap3D for Blender
GridMap3D addon for Blender, inspired by Godot 4.x GridMap3D node.

My biggest issue with Godot's GridMap3D is the inability to assign different materials to different parts without having to make a billion copies of each piece. Blender's material management is far superior, in my opinion, but I like the quick versatility of blocking out a map with Godot's GridMap3D. So I made this! It's still in alpha and there's plenty of quality of life improvements to be made, but I figured I'd upload it now in case anyone else wants to have a look at it.

## Installation
Drag & drop the .zip into Blender and it should work automatically. Confirmed working with Blender 5.3.

## Setup
In OBJECT MODE, there is a GridMap N-panel. Select the collection of meshes you want to turn into a mesh library, and click generate gridmap.
A new GridMap object and collection will populate in edit mode.

In EDIT MODE, the GridMap N-panel allows you to switch between placement/deletion, choose meshes from the library, change levels (Z axis), and clean up the final mesh by removing double vertices at intersections.

LMB to place/delete. ESC or CTRL+RMB to cancel.

## Good Practices & Easy Mistakes

Do NOT remove cells manually by clicking & deleting vertices because they will still exist in the cell dictionary. Currently, this has no effect, but in future versions that utilize materials, this will cause issues further down the road.

## TODOS
Future features:
* Click and drag to place meshes in cells.
* Rotate pieces with WASD before placement.
* Assign materials to cell slots.
* Replace cell on click / block placement if cell is full

## DISCLAIMER
Parts of the code were written by AI, but every line has been READ and REVIEWED by a HUMAN.

<img width="1920" height="1032" alt="Screenshot 2026-11-26 165823" src="https://github.com/user-attachments/assets/21378770-eae8-458e-91c7-a918bb0be528" />

<img width="1920" height="1032" alt="Screenshot 2026-11-26 165836" src="https://github.com/user-attachments/assets/aa633234-36a2-4955-a729-97945b97ed16" />

<img width="1920" height="1032" alt="Screenshot 2026-11-26 165931" src="https://github.com/user-attachments/assets/13d22ebe-1255-49dc-98f5-c2a3cb478f9e" />

<img width="1118" height="448" alt="image" src="https://github.com/user-attachments/assets/9078656d-bf3e-43ae-982e-a4475367c8d9" />

