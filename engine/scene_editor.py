import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
from typing import List, Tuple
import math
import json
import os
from datetime import datetime
import engine.geometry.objects
import engine.scene.saved_scenes
class Vector3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

class AABB:
    def __init__(self, min_point: Vector3, max_point: Vector3):
        self.min = min_point
        self.max = max_point
    
    def intersects(self, other: 'AABB') -> bool:
        return (self.min.x <= other.max.x and self.max.x >= other.min.x and
                self.min.y <= other.max.y and self.max.y >= other.min.y and
                self.min.z <= other.max.z and self.max.z >= other.min.z)

class MeshCollider:
    def __init__(self, obj_file_path: str):
        self.vertices: List[Vector3] = []
        self.faces: List[Tuple[int, int, int]] = []
        self.aabb = None
        self.sphere_radius = 0  # Added for sphere collision
        self.load_obj(obj_file_path)
        
    def load_obj(self, file_path: str):
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('v '):
                    parts = line.split()
                    vertex = Vector3(float(parts[1]), float(parts[2]), float(parts[3]))
                    self.vertices.append(vertex)
                elif line.startswith('f '):
                    parts = line.split()
                    face = (int(parts[1].split('/')[0]) - 1,
                           int(parts[2].split('/')[0]) - 1,
                           int(parts[3].split('/')[0]) - 1)
                    self.faces.append(face)
        self.update_aabb()
        self.calculate_sphere_radius()

    def calculate_sphere_radius(self):
        if not self.vertices:
            return
        # Find maximum distance between any pair of vertices
        max_dist = 0
        for i, v1 in enumerate(self.vertices):
            for v2 in self.vertices[i+1:]:
                dist = math.sqrt((v2.x-v1.x)**2 + (v2.y-v1.y)**2 + (v2.z-v1.z)**2)
                max_dist = max(max_dist, dist)
        self.sphere_radius = max_dist / 2

    def update_aabb(self):
        if not self.vertices:
            return
        min_x = min(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        min_z = min(v.z for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        max_y = max(v.y for v in self.vertices)
        max_z = max(v.z for v in self.vertices)
        self.aabb = AABB(Vector3(min_x, min_y, min_z), Vector3(max_x, max_y, max_z))

class Camera:
    def __init__(self):
        self.position = Vector3(0, 5, 10)
        self.yaw = -90.0
        self.pitch = 0.0
        self.move_speed = 5.0
        self.mouse_sensitivity = 0.1
        self.direction = Vector3(0, 0, -1)
        self.velocity = Vector3(0, 0, 0)
        self.size = Vector3(1, 2, 1)  # Camera's collision box size (width, height, depth)
        self.rb = RigidBody()
        obj_dir = os.path.dirname(engine.geometry.objects.__file__)
        cube_obj_path = os.path.join(obj_dir, "cube.obj")
        self.rb.set_mesh(cube_obj_path)
        self.rb.scale = self.size  # Scale it to match camera size
        self.ghost = True
        self.rb.is_visible = False
        self.rb.is_selectable = False
        self.rb.is_camera = True

    def get_aabb(self) -> AABB:
        half_size = Vector3(self.size.x/2, self.size.y/2, self.size.z/2)
        return AABB(
            Vector3(self.position.x - half_size.x, 
                   self.position.y - half_size.y, 
                   self.position.z - half_size.z),
            Vector3(self.position.x + half_size.x, 
                   self.position.y + half_size.y, 
                   self.position.z + half_size.z)
        )

    def update(self, delta_time: float, can_move: bool):
        if not can_move:
            return

        keys = pygame.key.get_pressed()
        forward = self.get_forward_vector()
        right = self.get_right_vector()

        move_dir = Vector3(0, 0, 0)
        if keys[pygame.K_w]:
            move_dir.x += forward.x
            move_dir.z += forward.z
        if keys[pygame.K_s]:
            move_dir.x -= forward.x
            move_dir.z -= forward.z
        if keys[pygame.K_a]:
            move_dir.x -= right.x
            move_dir.z -= right.z
        if keys[pygame.K_d]:
            move_dir.x += right.x
            move_dir.z += right.z

        if move_dir.x != 0 or move_dir.z != 0:
            length = math.sqrt(move_dir.x**2 + move_dir.z**2)
            move_dir.x /= length
            move_dir.z /= length

        # Jumping
        if keys[pygame.K_SPACE]:
            # Only jump when grounded
            if self.rb.is_grounded:
                self.rb.velocity.y = 8.0

        # Apply movement directly to the velocity
        self.rb.velocity.x = move_dir.x * self.move_speed
        self.rb.velocity.z = move_dir.z * self.move_speed
 
        

    def handle_mouse(self, dx: float, dy: float):
        self.yaw += dx * self.mouse_sensitivity
        self.pitch -= dy * self.mouse_sensitivity
        self.pitch = max(-89.0, min(89.0, self.pitch))

        direction_x = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        direction_y = math.sin(math.radians(self.pitch))
        direction_z = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        self.direction = Vector3(direction_x, direction_y, direction_z)

    def get_forward_vector(self) -> Vector3:
        length = math.sqrt(self.direction.x**2 + self.direction.y**2 + self.direction.z**2)
        return Vector3(self.direction.x/length, self.direction.y/length, self.direction.z/length)

    def get_right_vector(self) -> Vector3:
        forward = self.get_forward_vector()
        up = Vector3(0, 1, 0)
        right_x = forward.y * up.z - forward.z * up.y
        right_y = forward.z * up.x - forward.x * up.z
        right_z = forward.x * up.y - forward.y * up.x
        length = math.sqrt(right_x**2 + right_y**2 + right_z**2)
        return Vector3(right_x/length, right_y/length, right_z/length)

    def apply(self):
        forward = self.get_forward_vector()
        look_at = Vector3(
            self.position.x + forward.x,
            self.position.y + forward.y,
            self.position.z + forward.z
        )
        gluLookAt(
            self.position.x, self.position.y, self.position.z,
            look_at.x, look_at.y, look_at.z,
            0, 1, 0
        )
    def to_dict(self):
        return {
            'position': [self.position.x, self.position.y, self.position.z],
            'yaw': self.yaw,
            'pitch': self.pitch,
            'rb_position': [self.rb.position.x, self.rb.position.y, self.rb.position.z]
        }

    @classmethod
    def from_dict(cls, data):
        cam = cls()
        cam.position = Vector3(*data['position'])
        cam.yaw = data['yaw']
        cam.pitch = data['pitch']
        cam.handle_mouse(0, 0)  # Update direction vector
        if 'rb_position' in data:
            cam.rb.position = Vector3(*data['rb_position'])
        return cam

    

class RigidBody:
    def __init__(self):
        self.position = Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.mass = 1.0
        self.mesh_collider = None
        self.size = Vector3(1, 1, 1)
        self.gravity_enabled = True
        self.scale = Vector3(1, 1, 1)
        self.rotation = Vector3(0, 0, 0)  # Added for rotation
        self.is_selected = False
        self.is_preview = False
        self.is_visible = True
        self.is_selectable = True
        self.is_grounded = False
        self.is_camera = False

    def set_mesh(self, obj_file_path: str):
        self.mesh_collider = MeshCollider(obj_file_path)

    def get_sphere_center(self):
        return self.position
    
    def integrate(self, delta_time: float):
        # Gravity
        self.is_grounded = False
    
     
        if self.gravity_enabled:
            self.velocity.y -= 9.8 * delta_time

        # Integrate position
        self.position = self.position + (self.velocity * delta_time)

        # Clamp to ground
        if self.position.y < 0:
            self.position.y = 0
            self.velocity.y = 0
            self.is_grounded = True

        # Damping
        damping = 0.95
        self.velocity.x *= damping
        self.velocity.z *= damping
    
    def check_aabb_collision_and_resolve(self, other: 'RigidBody'):
        aabb1 = self.get_aabb()
        aabb2 = other.get_aabb()

        if not aabb1.intersects(aabb2):
            return False

        # Compute penetration depths
        pen_x = min(aabb1.max.x - aabb2.min.x, aabb2.max.x - aabb1.min.x)
        pen_y = min(aabb1.max.y - aabb2.min.y, aabb2.max.y - aabb1.min.y)
        pen_z = min(aabb1.max.z - aabb2.min.z, aabb2.max.z - aabb1.min.z)

        # Find minimum penetration
        min_penetration = min(pen_x, pen_y, pen_z)

        # Compute centers
        center1 = Vector3(
            (aabb1.min.x + aabb1.max.x) * 0.5,
            (aabb1.min.y + aabb1.max.y) * 0.5,
            (aabb1.min.z + aabb1.max.z) * 0.5
        )
        center2 = Vector3(
            (aabb2.min.x + aabb2.max.x) * 0.5,
            (aabb2.min.y + aabb2.max.y) * 0.5,
            (aabb2.min.z + aabb2.max.z) * 0.5
        )

        # Determine correction vector
        if min_penetration == pen_x:
            if center1.x < center2.x:
                correction = Vector3(-pen_x * 0.5, 0, 0)
            else:
                correction = Vector3(pen_x * 0.5, 0, 0)
            self.velocity.x = 0
            other.velocity.x = 0
        elif min_penetration == pen_y:
            if center1.y < center2.y:
                correction = Vector3(0, -pen_y * 0.5, 0)
            else:
                correction = Vector3(0, pen_y * 0.5, 0)
            self.velocity.y = 0
            other.velocity.y = 0
            
            # If we were corrected upward, we're standing on something
            
            
        else:
            if center1.z < center2.z:
                correction = Vector3(0, 0, -pen_z * 0.5)
            else:
                correction = Vector3(0, 0, pen_z * 0.5)
            self.velocity.z = 0
            other.velocity.z = 0

        # Apply correction
        
        self.position = self.position + correction
        other.position = other.position - correction
        
        if correction.y > 0 or self.position.y <= 0:
            self.is_grounded = True
        else:
            self.is_grounded = False
            
            
        if correction.y < 0 or other.position.y <= 0:
            other.is_grounded = True
        else:
            other.is_grounded = False

        return True
    def get_aabb(self) -> AABB:
        scaled_min = Vector3(
            self.mesh_collider.aabb.min.x * self.scale.x,
            self.mesh_collider.aabb.min.y * self.scale.y,
            self.mesh_collider.aabb.min.z * self.scale.z
        )
        scaled_max = Vector3(
            self.mesh_collider.aabb.max.x * self.scale.x,
            self.mesh_collider.aabb.max.y * self.scale.y,
            self.mesh_collider.aabb.max.z * self.scale.z
        )
        return AABB(
            Vector3(
                self.position.x + scaled_min.x,
                self.position.y + scaled_min.y,
                self.position.z + scaled_min.z
            ),
            Vector3(
                self.position.x + scaled_max.x,
                self.position.y + scaled_max.y,
                self.position.z + scaled_max.z
            )
        )

    def apply_force(self, force: Vector3):
        acceleration = Vector3(force.x/self.mass, force.y/self.mass, force.z/self.mass)
        self.velocity = self.velocity + acceleration

    def update(self, delta_time: float):
        if self.gravity_enabled:
            self.velocity.y -= 9.8 * delta_time

        self.position = self.position + (self.velocity * delta_time)

        if self.position.y < 0:
            self.position.y = 0
            self.velocity.y = 0

    def get_sphere_radius(self):
        # Scale the radius based on the largest scale factor
        max_scale = max(self.scale.x, self.scale.y, self.scale.z)
        return self.mesh_collider.sphere_radius * max_scale

    def check_sphere_collision(self, other: 'RigidBody'):
        center1 = self.get_sphere_center()
        center2 = other.get_sphere_center()
        radius1 = self.get_sphere_radius()
        radius2 = other.get_sphere_radius()
        
        distance = math.sqrt(
            (center2.x - center1.x)**2 +
            (center2.y - center1.y)**2 +
            (center2.z - center1.z)**2
        )
        return distance < (radius1 + radius2), distance - (radius1 + radius2)

    def render(self):
 
        if not self.mesh_collider or not self.is_visible:
            return

        glPushMatrix()
        glTranslatef(self.position.x, self.position.y, self.position.z)
        glRotatef(self.rotation.y, 0, 1, 0)  # Yaw
        glRotatef(self.rotation.x, 1, 0, 0)  # Pitch
        glRotatef(self.rotation.z, 0, 0, 1)  # Roll
        glScalef(self.scale.x, self.scale.y, self.scale.z)
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        if self.is_preview:
            glColor4f(0.5, 0.5, 0.5, 0.5)
        elif self.is_selected:
            glColor3f(0.8, 0.8, 0.8)
        else:
            glColor3f(0.7, 0.7, 0.7)
        
        glBegin(GL_TRIANGLES)
        for face in self.mesh_collider.faces:
            for vertex_idx in face:
                vertex = self.mesh_collider.vertices[vertex_idx]
                glVertex3f(vertex.x, vertex.y, vertex.z)
        glEnd()

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2.0)
        glBegin(GL_TRIANGLES)
        for face in self.mesh_collider.faces:
            for vertex_idx in face:
                vertex = self.mesh_collider.vertices[vertex_idx]
                glVertex3f(vertex.x, vertex.y, vertex.z)
        glEnd()
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glPopMatrix()

    def to_dict(self):
        return {
            'position': [self.position.x, self.position.y, self.position.z],
            'scale': [self.scale.x, self.scale.y, self.scale.z],
            'rotation': [self.rotation.x, self.rotation.y, self.rotation.z],
            'gravity_enabled': self.gravity_enabled
        }

    @classmethod
    def from_dict(cls, data, cube_obj_path):
        rb = cls()
        rb.set_mesh(cube_obj_path)
        rb.position = Vector3(*data['position'])
        rb.scale = Vector3(*data['scale'])
        rb.rotation = Vector3(*data['rotation'])
        rb.gravity_enabled = data['gravity_enabled']
        return rb

def init_opengl(width: int, height: int):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, width/height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.0, 0.0, 0.0, 1.0)

def load_scene_menu(scene_dir):
    """
    Opens a Tkinter window listing all .json scene files, sorted by creation time.
    Returns the filename if selected, or None if cancelled.
    """
    import tkinter as tk
    from tkinter import messagebox

    # Find all JSON files
    files = [
        f for f in os.listdir(scene_dir)
        if f.endswith(".json")
    ]
    if not files:
        messagebox.showinfo("No Scenes", "No scene files found in this folder.")
        return None

    # Sort by creation time (newest first)
    files = sorted(
        files,
        key=lambda f: os.path.getctime(os.path.join(scene_dir, f)),
        reverse=True
    )

    selected = {"value": None}

    def on_select(event):
        index = listbox.curselection()
        if index:
            selected["value"] = files[index[0]]
            root.destroy()

    def on_cancel():
        root.destroy()

    root = tk.Tk()
    root.title("Load Scene")

    label = tk.Label(root, text="Select a scene to load:")
    label.pack(padx=10, pady=5)

    listbox = tk.Listbox(root, width=50, height=15)
    for f in files:
        listbox.insert(tk.END, f)
    listbox.pack(padx=10, pady=5)
    listbox.bind("<Double-Button-1>", on_select)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    load_button = tk.Button(button_frame, text="Load", command=lambda: on_select(None))
    load_button.pack(side=tk.LEFT, padx=5)

    cancel_button = tk.Button(button_frame, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.LEFT, padx=5)

    root.mainloop()

    return selected["value"]

def save_scene_menu(scene_dir, scene_data):
    """
    Opens a separate small Pygame window to get the scene name.
    """
    # Create a new window
    pygame.display.quit()
    pygame.display.init()

    screen = pygame.display.set_mode((500, 200))
    pygame.display.set_caption("Save Scene")

    pygame.font.init()
    font = pygame.font.SysFont("consolas", 24)
    clock = pygame.time.Clock()
    input_text = ""
    message = "Enter scene name and press Enter (ESC to cancel):"
    overwrite_confirm = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if overwrite_confirm:
                    if event.key == pygame.K_y:
                        return input_text + ".json"
                    elif event.key == pygame.K_n:
                        overwrite_confirm = False
                        message = "Enter scene name and press Enter (ESC to cancel):"
                else:
                    if event.key == pygame.K_RETURN:
                        if not input_text.strip():
                            continue
                        filename = input_text.strip() + ".json"
                        path = os.path.join(scene_dir, filename)
                        if os.path.exists(path):
                            message = f"{filename} exists. Overwrite? (Y/N)"
                            overwrite_confirm = True
                        else:
                            return filename
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

        screen.fill((0, 0, 0))
        msg_surf = font.render(message, True, (255, 255, 255))
        input_surf = font.render(input_text, True, (255, 255, 0))
        screen.blit(msg_surf, (20, 60))
        screen.blit(input_surf, (20, 100))

        pygame.display.flip()
        clock.tick(30)
def build_grid_display_list(size, step):
    list_id = glGenLists(1)
    glNewList(list_id, GL_COMPILE)

    glBegin(GL_LINES)
    for x in range(-size, size + 1, step):
        for y in range(-size, size + 1, step):
            glColor4f(0.2, 0.2, 0.2, 0.5)
            glVertex3f(x, y, -size)
            glVertex3f(x, y, size)
    for x in range(-size, size + 1, step):
        for z in range(-size, size + 1, step):
            glColor4f(0.2, 0.2, 0.2, 0.5)
            glVertex3f(x, -size, z)
            glVertex3f(x, size, z)
    for y in range(-size, size + 1, step):
        for z in range(-size, size + 1, step):
            glColor4f(0.2, 0.2, 0.2, 0.5)
            glVertex3f(-size, y, z)
            glVertex3f(size, y, z)
    glEnd()

    glEndList()
    return list_id
def draw_cursor():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glLineWidth(2.0)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    glVertex2f(-0.02, 0)
    glVertex2f(0.02, 0)
    glVertex2f(0, -0.02)
    glVertex2f(0, 0.02)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    


    glDisable(GL_BLEND)   
def draw_grid(size: int, step: int, camera_position: Vector3):
    glBegin(GL_LINES)
    
    # Lines along Z
    for y in range(-size, size + 1, step):
        # Use finer spacing if y == 0
        if y == 0:
            spacing = max(1, step // 4)  # e.g., if step=2, spacing=1
        else:
            spacing = step

        for x in range(-size, size + 1, spacing):
            mid_point = Vector3(x, y, 0)
            fade = compute_fade(mid_point, camera_position, size)
            glColor4f(0.2, 0.2, 0.2, fade)
            glVertex3f(x, y, -size)
            glVertex3f(x, y, size)

    # Lines along X
    for y in range(-size, size + 1, step):
        if y == 0:
            spacing = max(1, step // 2)
        else:
            spacing = step

        for z in range(-size, size + 1, spacing):
            mid_point = Vector3(0, y, z)
            fade = compute_fade(mid_point, camera_position, size)
            glColor4f(0.2, 0.2, 0.2, fade)
            glVertex3f(-size, y, z)
            glVertex3f(size, y, z)

    # Lines along Y (vertical)
    for x in range(-size, size + 1, step):
        for z in range(-size, size + 1, step):
            mid_point = Vector3(x, 0, z)
            fade = compute_fade(mid_point, camera_position, size)
            glColor4f(0.2, 0.2, 0.2, fade)
            glVertex3f(x, -size, z)
            glVertex3f(x, size, z)

    glEnd()
    
    
def compute_fade(point: Vector3, camera_position: Vector3, max_distance: float) -> float:
    """
    Compute alpha fade based on distance to camera.
    """
    dx = point.x - camera_position.x
    dy = point.y - camera_position.y
    dz = point.z - camera_position.z
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    fade = max(0.1, 1.0 - (distance / (max_distance * 1.5)))
    return fade

# Safely normalize
def safe_normalize(v: Vector3) -> Vector3:
    length = math.sqrt(v.x**2 + v.y**2 + v.z**2)
    if length < 1e-6:
        return Vector3(0,0,0)
    return Vector3(v.x/length, v.y/length, v.z/length)    
def ray_cast_select(camera: Camera, rigid_bodies: List[RigidBody]) -> RigidBody:
    # Simple ray casting for object selection
    ray_origin = camera.position
    ray_direction = camera.get_forward_vector()
    
    closest_body = None
    closest_distance = float('inf')
    
    for rb in rigid_bodies:
        if not rb.is_selectable:
            continue
        aabb = rb.get_aabb()
        # Simple AABB-ray intersection check
        t_min = (aabb.min.x - ray_origin.x) / (.001 + ray_direction.x)
        t_max = (aabb.max.x - ray_origin.x) / (.0001+ ray_direction.x)
        if t_min > t_max: t_min, t_max = t_max, t_min
        
        ty_min = (aabb.min.y - ray_origin.y) / (.0001 + ray_direction.y)
        ty_max = (aabb.max.y - ray_origin.y) / (.0001 + ray_direction.y)
        if ty_min > ty_max: ty_min, ty_max = ty_max, ty_min
        
        if (t_min > ty_max) or (ty_min > t_max):
            continue
            
        t_min = max(t_min, ty_min)
        t_max = min(t_max, ty_max)
        
        tz_min = (aabb.min.z - ray_origin.z) / (.0001 + ray_direction.z)
        tz_max = (aabb.max.z - ray_origin.z) / (.0001 + ray_direction.z)
        if tz_min > tz_max: tz_min, tz_max = tz_max, tz_min
        
        if (t_min > tz_max) or (tz_min > t_max):
            continue
            
        t = max(t_min, tz_min)
        if t < 0:  # Behind camera
            continue
            
        if t < closest_distance:
            closest_distance = t
            closest_body = rb
            
    return closest_body
def game_loop():
    pygame.init()
    width, height = 800, 600
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
    init_opengl(width, height)
    
    
    
    

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    camera = Camera()
    obj_dir = os.path.dirname(engine.geometry.objects.__file__)
    cube_obj_path = os.path.join(obj_dir, "cube.obj")
  
    rb = RigidBody()
    rb.set_mesh(cube_obj_path)
    rigid_bodies = [rb, camera.rb]
    
    clock = pygame.time.Clock()
    running = True
    selected_body = None
    preview_cube = None
    creating_cube = False
    scene_dir = os.path.dirname(engine.scene.saved_scenes.__file__)

    
    # Editing modes
    edit_modes = ['move', 'rotate', 'scale']
    current_edit_mode = 0
    can_overwrite_scene = False
    
   

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_g and selected_body:
                    selected_body.gravity_enabled = not selected_body.gravity_enabled
                elif event.key == pygame.K_c and not creating_cube:
                    creating_cube = True
                    preview_cube = RigidBody()
                    preview_cube.set_mesh(cube_obj_path)
                    preview_cube.is_preview = True
                    forward = camera.get_forward_vector()
                    preview_cube.position = Vector3(
                        camera.position.x + forward.x * 5,
                        camera.position.y + forward.y * 5,
                        camera.position.z + forward.z * 5
                    )
                elif event.key == pygame.K_UP and selected_body:
                    current_edit_mode = (current_edit_mode + 1) % len(edit_modes)
                elif event.key == pygame.K_DOWN and selected_body:
                    current_edit_mode = (current_edit_mode - 1) % len(edit_modes)
                elif event.key == pygame.K_p:
                    # Pause the game and get a save name
                    scene_data = {
                        'camera': camera.to_dict(),
                        'objects': [rb.to_dict() for rb in rigid_bodies if (not rb.is_preview and not rb.is_camera)]
                    }
                    filename = save_scene_menu(scene_dir, scene_data)
                    if filename:
                        save_path = os.path.join(scene_dir, filename)
                        with open(save_path, "w") as f:
                            json.dump(scene_data, f)
                        print(f"Scene saved as {filename}")

                    # IMPORTANT: re-create OpenGL context
                    pygame.display.quit()
                    pygame.display.init()
                    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
                    init_opengl(width, height)
                    
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                elif event.key == pygame.K_l:
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                    filename = load_scene_menu(scene_dir)
                    if filename:
                        scene_path = os.path.join(scene_dir, filename)
                        with open(scene_path, "r") as f:
                            scene_data = json.load(f)

                        camera = Camera.from_dict(scene_data["camera"])
                        rigid_bodies.clear()
                        for obj in scene_data["objects"]:
                            rb = RigidBody.from_dict(obj, cube_obj_path)
                            rigid_bodies.append(rb)
                
                        rigid_bodies.append(camera.rb)
                        selected_body = None
                        creating_cube = False
                        preview_cube = None

                        # Recreate OpenGL context
                        pygame.display.quit()
                        pygame.display.init()
                        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
                        init_opengl(width, height)

                        # Re-hide and re-grab mouse
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)

                        print(f"Scene '{filename}' loaded.")
                elif event.key == pygame.K_o:
                    can_overwrite_scene = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if creating_cube and preview_cube:
                    if event.button == 1:
                        preview_cube.is_preview = False
                        rigid_bodies.append(preview_cube)
                        creating_cube = False
                        preview_cube = None
                    elif event.button == 3:
                        creating_cube = False
                        preview_cube = None
                elif event.button == 1:
                    hit_body = ray_cast_select(camera, rigid_bodies)
                    for rb in rigid_bodies:
                        rb.is_selected = False
                    if hit_body and not hit_body.is_preview:
                        hit_body.is_selected = True
                        selected_body = hit_body
                elif event.button == 3 and selected_body:
                    selected_body.is_selected = False
                    selected_body = None

        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        if not selected_body:  # Only allow camera movement when no cube is selected
            camera.handle_mouse(mouse_dx, mouse_dy)

        delta_time = clock.tick(60) / 1000.0
        camera.update(delta_time, not selected_body)
        
        # Handle collisions between all objects

        # Integrate all
        for rb in rigid_bodies:
            rb.integrate(delta_time)

        # Resolve collisions once per pair
        for _ in range(3):   # Repeat a few times to stabilize
            for i, rb1 in enumerate(rigid_bodies):
                for j in range(i + 1, len(rigid_bodies)):
                    rb2 = rigid_bodies[j]
                    rb1.check_aabb_collision_and_resolve(rb2)

        keys = pygame.key.get_pressed()
        target = preview_cube if creating_cube and preview_cube else selected_body
        camera.position = camera.rb.position
        
        if target and not creating_cube:  # Only allow editing for selected cubes
            forward = camera.get_forward_vector()
            right = camera.get_right_vector()
            move_speed = 0.1
            rotate_speed = 2.0
            scale_speed = 0.02
            
            flat_forward = Vector3(forward.x, 0, forward.z)
            flat_right = Vector3(right.x, 0, right.z)

            

            flat_forward = safe_normalize(flat_forward)
            flat_right = safe_normalize(flat_right)

            if edit_modes[current_edit_mode] == 'move':
                if keys[pygame.K_w]:
                    target.position = target.position + (flat_forward * move_speed)
                if keys[pygame.K_s]:
                    target.position = target.position - (flat_forward * move_speed)
                if keys[pygame.K_a]:
                    target.position = target.position - (flat_right * move_speed)
                if keys[pygame.K_d]:
                    target.position = target.position + (flat_right * move_speed)
                if keys[pygame.K_e]:
                    target.position.y += move_speed
                if keys[pygame.K_q]:
                    target.position.y -= move_speed
            elif edit_modes[current_edit_mode] == 'rotate':
                if keys[pygame.K_w]: target.rotation.x += rotate_speed
                if keys[pygame.K_s]: target.rotation.x -= rotate_speed
                if keys[pygame.K_a]: target.rotation.y += rotate_speed
                if keys[pygame.K_d]: target.rotation.y -= rotate_speed
            elif edit_modes[current_edit_mode] == 'scale':
                if keys[pygame.K_w]: target.scale.y += scale_speed
                if keys[pygame.K_s]: target.scale.y = max(0.1, target.scale.y - scale_speed)
                if keys[pygame.K_a]: target.scale.x += scale_speed
                if keys[pygame.K_d]: target.scale.x = max(0.1, target.scale.x - scale_speed)
                if keys[pygame.K_e]: target.scale.z += scale_speed
                if keys[pygame.K_q]: target.scale.z= max(0.1, target.scale.x - scale_speed)

        #for rb in rigid_bodies:
            #rb.update(delta_time)
      #  if preview_cube:
           # preview_cube.update(delta_time)
            
        

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        camera.apply()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        draw_grid(size=30, step=5, camera_position=camera.position)
        glDisable(GL_BLEND)
        
        

        for rb in rigid_bodies:
            rb.render()
        if preview_cube:
            preview_cube.render()

        draw_cursor()
        pygame.display.flip()

    pygame.quit()

