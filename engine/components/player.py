from .. import pygpen as pp

class Player(pp.PhysicsEntity):
    def __init__(self, *args, room=None):
        super().__init__(*args)
        self.room = room
        self.gravity = 500
        self.acceleration[1] = self.gravity
        self.velocity_cap = 330
        self.velocity_caps = [self.velocity_cap, self.velocity_cap]
        self.speed = 150
        self.autoflip = 1
        self.bounce = 0
        self.outline = (40, 35, 40)
        self.z = -5.5
        self.moves = [0, 0, 0, 0] 
        self.rm = self.e['RoomSystem']
        self.transition_cooldown = 0 
        
        self.max_hp = 160
        self.hp = 160

        self.run_sound_timer = 0
        self.climb_sound_timer = 0

    def update(self, dt):
        super().update(dt)

        self._update_sound_timers(dt)
        
        dialogue = self.e['DialogueSystem'].active
        if self.e['DialogueSystem'].post_battle_mode:
            dialogue = False
            
        if not self.e['BattleSystem'].is_battling and not dialogue:
            self._handle_room_transitions(dt)
            
            if sum(self.moves) == 0:
                self._handle_movement_input()
            else:
                self._handle_active_movement()

        self._update_animation_state()
        self.physics_update(self.e['Game'].tilemap)
    
    def _update_sound_timers(self, dt):
        if self.run_sound_timer > 0:
            self.run_sound_timer -= dt
        if self.climb_sound_timer > 0:
            self.climb_sound_timer -= dt
    
    def _handle_room_transitions(self, dt):
        if self.transition_cooldown > 0:
            self.transition_cooldown = round(self.transition_cooldown-0.01, 3)
    
    def _handle_movement_input(self):
        current_room = self.rm.rooms[self.rm.current_room_id]
        
        if self.e['Input'].pressed('left') and current_room.ways['left']:
            self.moves[0] = 1
            self.transition_cooldown = 0.5

        if self.e['Input'].pressed('right') and current_room.ways['right']:
            self.moves[1] = 1
            self.transition_cooldown = 0.5
            
        if self.e['Input'].pressed('up') and current_room.ways['up']:
            self.moves[2] = 1
            self.transition_cooldown = 0.5

        if self.e['Input'].pressed('down') and current_room.ways['down']:
            self.moves[3] = 1
            self.transition_cooldown = 0.5
    
    def _handle_active_movement(self):
        if self.moves[0] != 0:
            self._move_left()
                
        if self.moves[1] != 0:
            self._move_right()
                
        if self.moves[2] != 0:
            self._move_up()
                
        if self.moves[3] != 0:
            self._move_down()
    
    def _move_left(self):
        self.apply_force((-1 * self.speed, 0))

        if self.run_sound_timer <= 0:
            self.e['Sounds'].play('run', volume=0.25)
            self.run_sound_timer = 0.25

        if self.pos[0] < 5:
            self.rm.move_to_room('left', self.e['Game'].tilemap)
            self.pos[0] += 340
            
        if self.pos[0] > 178 and self.pos[0] < 182 and self.transition_cooldown <= 0:
            self.moves[0] = 0
    
    def _move_right(self):
        self.apply_force((self.speed, 0))

        if self.run_sound_timer <= 0:
            self.e['Sounds'].play('run', volume=0.25)
            self.run_sound_timer = 0.25

        if self.pos[0] > 340:
            self.rm.move_to_room('right', self.e['Game'].tilemap)
            self.pos[0] -= 340

        if self.pos[0] > 178 and self.pos[0] < 182 and self.transition_cooldown <= 0:
            self.moves[1] = 0
    
    def _move_up(self):
        self.velocity = [0, -1*self.speed]
        self.off_colide = True

        if self.climb_sound_timer <= 0:
            self.e['Sounds'].play('climb', volume=0.025)
            self.climb_sound_timer = 0.3

        if self.pos[1] < 25:
            self.rm.move_to_room('up', self.e['Game'].tilemap)
            self.pos[1] += 220  
            
        if self.pos[1] > 156 and self.pos[1] < 160 and self.transition_cooldown <= 0:
            self.moves[2] = 0
            self.off_colide = False
    
    def _move_down(self):
        self.velocity = [0, self.speed]
        self.off_colide = True

        if self.climb_sound_timer <= 0:
            self.e['Sounds'].play('climb', volume=0.025)
            self.climb_sound_timer = 0.3

        if self.pos[1] > 220:
            self.rm.move_to_room('down', self.e['Game'].tilemap)
            self.pos[1] -= 220
            
        if self.pos[1] > 130 and self.pos[1] < 134 and self.transition_cooldown <= 0:
            self.moves[3] = 0
            self.off_colide = False
    
    def _update_animation_state(self):
        if self.next_movement[0]:
            self.set_action('run')
        elif self.off_colide:
            self.set_action('climb')
        else:
            self.set_action('idle')
            
    def tkd(self, dmg):
        self.hp -= dmg
        self.e['Sounds'].play('damage', volume=0.5)