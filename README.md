# Python Basic 3D Engine

This is a **Python-based minimal 3D engine and scene editor** using:
- **PyOpenGL** for 3D rendering
- **Pygame** for windowing and input handling
- **Tkinter** for scene save/load dialogs

It provides:
- Rendering of simple 3D scenes
- Basic physics and AABB collision detection
- Object placement, scaling, rotation
- Save/load scene files (`.json`)
- A simple in-engine editor with mouse and keyboard controls

> This is a bare-bones first pass and is unlicensed.

---

## 🎮 Current Features

### 🏃 Camera Controller
- Move with `WASD`
- Look around with the mouse
- Jump with `SPACE`
- No eternal void to fall into

### 🧱 Object Editing
- `C` to create a new cube in front of the camera
  - **Left click:** confirm placement
  - **Right click:** cancel
- Select cubes by hovering the cursor and left-clicking
- Use `UP`/`DOWN` arrows to cycle edit modes:
  - Move
  - Rotate
  - Scale
- Adjust selected object with `WASD` and `E/Q`
- Toggle gravity with `G`

### 💾 Scene Management
- `P` to save the scene (with overwrite protection)
- `L` to load a saved scene, selected from your previously saved scenes sorted by date

### 📦 Collision
- Axis-aligned bounding box (AABB) collision resolution

### 🕹️ Grid and Cursor
- Fade-out grid to help with orientation
- Simple 2D crosshair cursor

---

## ⚙️ Installation

Make sure you have **Python 3.9+** and install the dependencies:

```bash
pip install numpy PyOpenGL pygame
```

🚀 Running the Project
You can either:

Use the Python API:

```python

from engine.core.app import game_loop

if __name__ == "__main__":
    game_loop()
```

Or run your main script (CustomEngine.py) directly:

```bash
python CustomEngine.py
```

🎮 Controls
Key	Action
WASD	Move camera or selected object
Mouse Move	Look around
SPACE	Jump
C	Create cube (Left click confirm, Right click cancel)
Left Click	Select object
Right Click	Deselect object
UP / DOWN	Cycle edit mode (move / rotate / scale)
E / Q	Move or scale along vertical axis
G	Toggle gravity on selected object
P	Save scene
L	Load scene
ESC	Quit

🗂️ Project Structure
```pgsql
master
│   CustomEngine.py
│   CustomEngine.pyproj
│   CustomEngine.sln
│
├───engine
│   │   main.py
│   │   scene_editor.py
│   │
│   ├───core
│   │   │   app.py
│   │   │   camera.py
│   │   │   renderer.py
│   │
│   ├───geometry
│   │   │   primitives.py
│   │   │
│   │   └───objects
│   │       │   cube.obj
│   │
│   ├───scene
│   │   │   scene.py
│   │   │
│   │   └───saved_scenes
│   │       │   basic.json
│   │       │   basic2.json
│   │
│   ├───shaders
│   │       basic.frag
│   │       basic.vert
│   │       cube.frag
│   │       cube.vert
│   │       outline.frag
│
└───game_assets
        Don't Put That in the Microwave.mp4
        notlooking.png
```
When you press L, a Tkinter window will display all available .json scenes sorted by date.

License:

This project is unlicensed.
Feel free to use, modify, share, or do whatever you like.

Acknowledgements:

PyOpenGL

Pygame

NumPy