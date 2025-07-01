import pygame
import moderngl
import numpy as np
from engine.core.renderer import Renderer
from engine.core.camera import Camera

class InputManager:
    def __init__(self):
        self.actions = {}
        self.key_states = {}

    def register_action(self, action_name, key, callback, trigger_on='press'):
        self.actions[action_name] = {
            'key': key,
            'callback': callback,
            'trigger_on': trigger_on
        }

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            for action, config in self.actions.items():
                if event.key == config['key'] and config['trigger_on'] == 'press':
                    config['callback']()
            self.key_states[event.key] = True
        elif event.type == pygame.KEYUP:
            for action, config in self.actions.items():
                if event.key == config['key'] and config['trigger_on'] == 'release':
                    config['callback']()
            self.key_states[event.key] = False

    def process_held_keys(self):
        for action, config in self.actions.items():
            if config['trigger_on'] == 'hold' and self.key_states.get(config['key'], False):
                config['callback']()

class App:
    def __init__(self, width=800, height=600, title="Don't Put That in the Microwave"):
        pygame.init()
        pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption(title)

        self.ctx = moderngl.create_context()
        self.clock = pygame.time.Clock()
        self.running = True
        self.width = width
        self.height = height
        self.renderer = Renderer(self.ctx)
        self.camera = Camera(position=(0, 0, 2))  # Start 2 units in front of cube
        self.angle = 0
        self.rotate_enabled = True
        self.game_state = 'menu'
        self.selected_object = None
        self.door_open = False
        self.cube_position = np.array([0, 0, -5], dtype='f4')  # Cube position from model matrix

        self.input_manager = InputManager()
        self.setup_inputs()
    def set_camera_velocity(self, axis, value):
        self.camera.target_velocity[axis] = value

    def setup_inputs(self):
        self.input_manager.register_action(
            'quit',
            pygame.K_ESCAPE,
            self.quit_game,
            trigger_on='press'
        )
        self.input_manager.register_action(
            'toggle_rotation',
            pygame.K_SPACE,
            self.toggle_rotation,
            trigger_on='press'
        )
        self.input_manager.register_action(
            'start_game',
            pygame.K_RETURN,
            self.start_game,
            trigger_on='press'
        )
        self.input_manager.register_action(
            'choose_object',
            pygame.K_c,
            self.choose_object,
            trigger_on='press'
        )
        self.input_manager.register_action(
            'open_door',
            pygame.K_o,
            self.open_door,
            trigger_on='press'
        )
        self.input_manager.register_action(
            'microwave',
            pygame.K_m,
            self.microwave_object,
            trigger_on='press'
        )
        self.input_manager.register_action(
            'look_at_cube',
            pygame.K_l,
            self.look_at_cube,
            trigger_on='press'
        )
        # Panning actions
        self.input_manager.register_action(
            'pan_left',
            pygame.K_LEFT,
            lambda: self.set_camera_velocity(0, -self.camera.max_speed),
            trigger_on='hold'
        )
        self.input_manager.register_action(
            'pan_right',
            pygame.K_RIGHT,
            lambda: self.set_camera_velocity(0, self.camera.max_speed),
            trigger_on='hold'
        )
        self.input_manager.register_action(
            'pan_up',
            pygame.K_UP,
            lambda: self.set_camera_velocity(1, self.camera.max_speed),
            trigger_on='hold'
        )
        self.input_manager.register_action(
            'pan_down',
            pygame.K_DOWN,
            lambda: self.set_camera_velocity(1, -self.camera.max_speed),
            trigger_on='hold'
        )
        self.input_manager.register_action(
            'stop_pan_x_left',
            pygame.K_LEFT,
            lambda: self.set_camera_velocity(0, 0.0),
            trigger_on='release'
        )
        self.input_manager.register_action(
            'stop_pan_x_right',
            pygame.K_RIGHT,
            lambda: self.set_camera_velocity(0, 0.0),
            trigger_on='release'
        )
        self.input_manager.register_action(
            'stop_pan_y_up',
            pygame.K_UP,
            lambda: self.set_camera_velocity(1, 0.0),
            trigger_on='release'
        )
        self.input_manager.register_action(
            'stop_pan_y_down',
            pygame.K_DOWN,
            lambda: self.set_camera_velocity(1, 0.0),
            trigger_on='release'
        )

    def look_at_cube(self):
        """Make camera look at the cube."""
        self.camera.look_at(self.cube_position)
        print("Camera looking at cube.")

    def quit_game(self):
        self.running = False

    def toggle_rotation(self):
        self.rotate_enabled = not self.rotate_enabled
        print("Rotation enabled:", self.rotate_enabled)

    def start_game(self):
        if self.game_state == 'menu':
            self.game_state = 'playing'
            print("Game started! Press C to choose an object, O to open/close door, M to microwave, L to look at cube.")
        else:
            print("Game already started or in progress.")

    def choose_object(self):
        if self.game_state == 'playing':
            objects = ['fork', 'egg', 'sponge']
            self.selected_object = objects[(objects.index(self.selected_object) + 1) % len(objects) if self.selected_object else 0]
            print(f"Selected object: {self.selected_object}")
        else:
            print("Cannot choose object: Game not in playing state. Press Enter to start.")

    def open_door(self):
        if self.game_state == 'playing':
            self.door_open = not self.door_open
            print(f"Microwave door {'open' if self.door_open else 'closed'}")
        else:
            print("Cannot open door: Game not in playing state. Press Enter to start.")

    def microwave_object(self):
        if self.game_state == 'playing' and self.selected_object and not self.door_open:
            self.game_state = 'exploded'
            print(f"Microwaving {self.selected_object}... BOOM!")
        else:
            print("Cannot microwave: No object selected, door open, or game not in playing state. Press Enter to start.")

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            self.handle_events()
            self.camera.pan(dt, self.camera.target_velocity)  # Update camera panning
            self.render()
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.input_manager.process_event(event)
        self.input_manager.process_held_keys()

    def render(self):
        self.ctx.clear(0.1, 0.1, 0.1)
        self.camera.aspect = self.width / self.height

        angle_rad = np.radians(self.angle)
        model = np.array([
            [ np.cos(angle_rad), 0, np.sin(angle_rad), 0],
            [ 0,                 1, 0,                 0],
            [-np.sin(angle_rad), 0, np.cos(angle_rad), 0],
            [ 0,                 0, -5,                1],
        ], dtype='f4').T

        view = self.camera.get_view_matrix()
        proj = self.camera.get_proj_matrix()
        mvp = (proj @ view @ model).T
        self.renderer.render(mvp)

        if self.game_state == 'playing' and self.rotate_enabled:
            self.angle += 1

        # Print camera position for debugging
        print(f"Camera position: {self.camera.position}", end='\r')