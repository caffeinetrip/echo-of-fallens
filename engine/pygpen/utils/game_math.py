import math, pygame, random

def normalize(v, amt, target=0):
    if v > target + amt:
        v -= amt
    elif v < target - amt:
        v += amt
    else:
        v = target
    return v

def rectify(p1, p2):
    tl = (min(p1[0], p2[0]), min(p1[1], p2[1]))
    br = (max(p1[0], p2[0]), max(p1[1], p2[1]))
    return pygame.Rect(*tl, br[0] - tl[0] + 1, br[1] - tl[1] + 1)

def box_points(rect):
    points = []
    for y in range(rect.height):
        for x in range(rect.width):
            points.append((rect.x + x, rect.y + y))
    return points

def advance(vec, angle, amt):
    vec[0] += math.cos(angle) * amt
    vec[1] += math.sin(angle) * amt
    return vec

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

def lerp(a, b, t):
    return a + (b - a) * t

def randint_excluding_ranges(start, end, forbidden_ranges):
    while True:
        num = random.randint(start, end)
        if all(not (low <= num <= high) for low, high in forbidden_ranges):
            return num
        
def calculate_angle(pos1, pos2):
    mouse_x, mouse_y = [pos1[0], pos1[1]]
    screen_x, screen_y = pos2
    
    angle_rad = math.atan2((screen_y - mouse_y)*-1, (screen_x - mouse_x)*-1)
    return round(math.degrees(angle_rad))

def scale_mouse_pos(mouse_pos, original_size, target_size):
    mouse_x, mouse_y = mouse_pos
    orig_w, orig_h = original_size
    target_w, target_h = target_size

    scaled_x = mouse_x * (target_w / orig_w)
    scaled_y = mouse_y * (target_h / orig_h)

    return round(scaled_x), round(scaled_y)

def convert_string_to_list(string):

    if not isinstance(string, str):
        raise TypeError("Input must be a string")

    parts = string.split(',')

    numbers = []
    for part in parts:
        try:
            number = float(part.strip())
            if number.is_integer():
                number = int(number)
            numbers.append(number)
        except ValueError:
            raise ValueError(f'Unable to convert "{part}" to a number')
    
    return numbers