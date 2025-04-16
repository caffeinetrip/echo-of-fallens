import time
import math

import pygame

from ..utils.game_math import distance
from ..utils.elements import Element

class Rope(Element):
    def __init__(self, points, color=(255, 255, 255), hz=60):
        super().__init__()
        self.update_timer = time.time()
        self.hz = hz
        self.color = color
        self.points = points
        self.last_points = [[p[0], p[1]] for p in self.points]
        self.handles = [i for i, p in enumerate(self.points) if not p[2]]
        self.connections = []
        self.stretch = 1.0
        for i in range(len(self.points) - 1):
            dis = distance(self.points[i], self.points[i + 1])
            self.connections.append([i, i + 1, dis])
            
    @property
    def natural_length(self):
        return sum([conn[2] for conn in self.connections])
    
    @property
    def length(self):
        return sum([conn[2] * self.stretch for conn in self.connections])
            
    def point_info(self, index):
        if index < 0:
            index = len(self.points) + index
        if index < len(self.points):
            parent = index - 1
            if parent != -1:
                angle = math.atan2(self.points[parent][1] - self.points[index][1], self.points[parent][0] - self.points[index][0])
            else:
                angle = math.atan2(self.points[index + 1][1] - self.points[index][1], self.points[index + 1][0] - self.points[index][0]) + math.pi
            return (self.points[index][:2], angle)
        return None
            
    def shift_handles(self, amount, handles=None):
        if not handles:
            handles = range(len(self.handles))
        for handle in handles:
            self.points[self.handles[handle]][0] += amount[0]
            self.points[self.handles[handle]][1] += amount[1]
            
    def place_handles(self, pos, handles=None, reduce_pull=0):
        if not handles:
            handles = range(len(self.handles))
        pull_dis = None
        handle_ids = []
        for handle in handles:
            if not pull_dis:
                pull_dis = (pos[0] - self.points[self.handles[handle]][0], pos[1] - self.points[self.handles[handle]][1])
            self.points[self.handles[handle]][0] = pos[0]
            self.points[self.handles[handle]][1] = pos[1]
            handle_ids.append(self.handles[handle])
        if reduce_pull and pull_dis:
            for i, point in enumerate(self.points):
                if i not in handle_ids:
                    point[0] += pull_dis[0] * reduce_pull
                    point[1] += pull_dis[1] * reduce_pull
                    self.last_points[i][0] += pull_dis[0] * reduce_pull
                    self.last_points[i][1] += pull_dis[1] * reduce_pull
            
    def update_constraints(self):
        for conn in self.connections:
            dis = distance(self.points[conn[0]], self.points[conn[1]])
            dis_dif = conn[2] * self.stretch - dis
            if dis == 0:
                dis = 0.001
            movement_ratio = dis_dif / dis * 0.5
            dx = self.points[conn[1]][0] - self.points[conn[0]][0]
            dy = self.points[conn[1]][1] - self.points[conn[0]][1]
            if self.points[conn[0]][2]:
                self.points[conn[0]][0] -= dx * movement_ratio * 0.95
                self.points[conn[0]][1] -= dy * movement_ratio * 0.95
            if self.points[conn[1]][2]:
                self.points[conn[1]][0] += dx * movement_ratio * 0.95
                self.points[conn[1]][1] += dy * movement_ratio * 0.95
                
    def impulse(self, index, force):
        self.last_points[index][0] -= force[0]
        self.last_points[index][1] -= force[1]
        
    def toggle_handle(self, index, enabled=True):
        if enabled and (index not in self.handles):
            self.handles.append(index)
            self.points[index][2] = 0
            
        if (not enabled) and (index in self.handles):
            self.handles.remove(index)
            self.points[index][2] = 1
        
    def update(self, forces=[0, 0.2], restricted=False):
        updates = 1
        if restricted:
            updates = 0
            while (self.update_timer + (1 / self.hz)) < self.e['Window'].time:
                self.update_timer += (1 / self.hz)
                updates += 1
        for j in range(updates):
            for i, point in enumerate(self.points):
                vel = (point[0] - self.last_points[i][0], point[1] - self.last_points[i][1])
                self.last_points[i][0] = point[0]
                self.last_points[i][1] = point[1]
                if point[2]:
                    point[0] += vel[0] + forces[0]
                    point[1] += vel[1] + forces[1]
            
            self.update_constraints()
    
    def render(self, surf, offset=(0, 0), show_points=False):
        points = [(p[0] - offset[0], p[1] - offset[1]) for p in self.points]
        pygame.draw.lines(surf, self.color, False, points)
        if show_points:
            for p in points:
                pygame.draw.circle(surf, (255, 0, 0), p, 5, 1)