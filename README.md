# GridMap3D for Blender
GridMap3D addon for Blender, inspired by Godot 4.x GridMap3D node.

My biggest issue with Godot's GridMap3D is the inability to assign different materials to different parts without having to make a billion copies of each piece. Blender's material management is far superior, in my opinion, but I like the quick versatility of blocking out a map with Godot's GridMap3D. So I made

## Installation
Drag & drop the .zip into Blender and it should work automatically. Confirmed working with Blender 5.3.

## Setup
In OBJECT MODE, there is a GridMap N-panel. Select the collection of meshes you want to turn into a mesh library, and click generate gridmap.
A new GridMap object and collection will populate in edit mode.

In EDIT MODE, the GridMap N-panel allows you to switch between placement/deletion, choose meshes from the library, change levels (Z axis), and clean up the final mesh by removing double vertices at intersections.

LMB to place/delete. ESC or CTRL+RMB to cancel.

## TODOS
Future features:
* Click and drag to place meshes in cells.
* Rotate pieces with WASD before placement.
* Assign materials to cell slots.

## DISCLAIMER
Parts of the code were written by AI, but every line has been READ and REVIEWED by a HUMAN.
