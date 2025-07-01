import numpy as np

def normalize(v):
    return v / np.linalg.norm(v)

def look_at(eye, target, up):
    f = normalize(target - eye)
    s = normalize(np.cross(f, up))
    u = np.cross(s, f)

    result = np.eye(4, dtype='f4')
    result[0, :3] = s
    result[1, :3] = u
    result[2, :3] = -f
    result[:3, 3] = -np.dot(result[:3, :3], eye)
    return result

class Camera:
    def __init__(self, position=(0, 0, 0), fov=45.0, near=0.1, far=100.0):
        self.position = np.array(position, dtype='f4')  # Camera position (x, y, z)
        self.direction = np.array([0, 0, -1], dtype='f4')  # Default forward direction
        self.up = np.array([0, 1, 0], dtype='f4')  # Up direction
        self.aspect = 800 / 600  # Default aspect ratio
        self.fov = fov
        self.near = near
        self.far = far

        # Panning variables
        self.velocity = np.array([0.0, 0.0, 0.0], dtype='f4')  # Current velocity
        self.target_velocity = np.array([0.0, 0.0, 0.0], dtype='f4')  # Desired velocity
        self.max_speed = 5.0  # Units per second
        self.acceleration = 20.0  # Units per second^2
        self.spring_constant = 10.0  # Elastic pull-back
        self.damping = 0.95  # Velocity decay (0 to 1)

    def pan(self, dt, target_velocity):
        """Update camera position with smooth, elastic panning."""
        # Accelerate towards target velocity
        accel = (target_velocity - self.velocity) * self.acceleration
        self.velocity += accel * dt - self.spring_constant * self.velocity * dt
        # Apply damping
        self.velocity *= self.damping
        # Update position
        self.position += self.velocity * dt

    def look_at(self, target):
        """Orient camera to look at a target point."""
        target = np.array(target, dtype='f4')
        self.direction = target - self.position
        if np.linalg.norm(self.direction) > 0:
            self.direction /= np.linalg.norm(self.direction)
        # Compute right vector (cross product of global up and direction)
        right = np.cross(np.array([0, 1, 0], dtype='f4'), self.direction)
        if np.linalg.norm(right) > 0:
            right /= np.linalg.norm(right)
        # Recompute up vector
        self.up = np.cross(self.direction, right)

    def get_view_matrix(self):
        """Compute view matrix using position, direction, and up."""
        # Look-at matrix: translate to -position, rotate to align axes
        forward = self.direction
        right = np.cross(np.array([0, 1, 0], dtype='f4'), forward)
        if np.linalg.norm(right) > 0:
            right /= np.linalg.norm(right)
        up = np.cross(forward, right)
        view = np.array([
            [right[0], right[1], right[2], -np.dot(right, self.position)],
            [up[0], up[1], up[2], -np.dot(up, self.position)],
            [-forward[0], -forward[1], -forward[2], -np.dot(forward, self.position)],
            [0, 0, 0, 1]
        ], dtype='f4').T
        return view

    def get_proj_matrix(self):
        """Compute perspective projection matrix."""
        f = 1.0 / np.tan(np.radians(self.fov) / 2.0)
        q = self.far / (self.far - self.near)
        proj = np.array([
            [f / self.aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, q, -q * self.near],
            [0, 0, 1, 0]
        ], dtype='f4').T
        return proj

class Camera0:
    def __init__(self, target=(0, 0, 0), distance=10.0):
        self.target = np.array(target, dtype='f4')
        self.distance = distance
        self.yaw = 0.0
        self.pitch = 0.0
        self.aspect = 4/3
        self.fov = np.radians(45)
        self.near = 0.1
        self.far = 100.0

    def get_view_matrix(self):
        yaw_rad = np.radians(self.yaw)
        pitch_rad = np.radians(self.pitch)

        # Orbiting camera around the target
        direction = np.array([
            np.cos(pitch_rad) * np.sin(yaw_rad),
            np.sin(pitch_rad),
            np.cos(pitch_rad) * np.cos(yaw_rad),
        ], dtype='f4')

        position = self.target - direction * self.distance
        up = np.array([0, 1, 0], dtype='f4')
        return look_at(position, self.target, up)

    def get_proj_matrix(self):
        f = 1.0 / np.tan(self.fov / 2)
        proj = np.zeros((4, 4), dtype='f4')
        proj[0, 0] = f / self.aspect
        proj[1, 1] = f
        proj[2, 2] = (self.far + self.near) / (self.near - self.far)
        proj[2, 3] = (2 * self.far * self.near) / (self.near - self.far)
        proj[3, 2] = -1
        return proj