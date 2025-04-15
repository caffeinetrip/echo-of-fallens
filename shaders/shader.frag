#version 330
uniform sampler2D surface;
uniform sampler2D ui_surf;
uniform sampler2D bg_surf;
uniform float time;
uniform float tremor;
uniform bool fight;
uniform float noise_gain;
uniform float transition = 0.0; 
uniform float e_transition; 
uniform bool overlay = false;
uniform float scanlines_opacity = 0.0;
uniform float scanlines_width = 0.15;
uniform float grille_opacity = 0.0;
uniform vec2 resolution = vec2(640.0, 480.0);
uniform bool pixelate = false;
uniform bool roll = false;
uniform float roll_speed = 5.0;
uniform float roll_size = 15.0;
uniform float roll_variation = 2.5;
uniform float distort_intensity = 0.08;
uniform float noise_opacity = 0.35;
uniform float noise_speed = 7.0;
uniform float static_noise_intensity = 0.06;
uniform float aberration = 0.02;
uniform float brightness = 1.2;
uniform bool discolor = true;
uniform float warp_amount = 0.0;
uniform bool clip_warp = false;
uniform float vignette_intensity = 0.7;
uniform float vignette_opacity = 0.7;
uniform float grain_strength = 0.06;
uniform float desaturation = 0.5;
uniform float flicker_intensity = 0.05;

out vec4 f_color;
in vec2 uv;



vec2 random(vec2 uv) {
    uv = vec2(dot(uv, vec2(127.1, 311.7)), dot(uv, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(uv) * 43758.5453123);
}

float noise(vec2 uv) {
    vec2 uv_index = floor(uv);
    vec2 uv_fract = fract(uv);
    vec2 blur = smoothstep(0.0, 1.0, uv_fract);
    return mix(mix(dot(random(uv_index + vec2(0.0, 0.0)), uv_fract - vec2(0.0, 0.0)),
                   dot(random(uv_index + vec2(1.0, 0.0)), uv_fract - vec2(1.0, 0.0)), blur.x),
               mix(dot(random(uv_index + vec2(0.0, 1.0)), uv_fract - vec2(0.0, 1.0)),
                   dot(random(uv_index + vec2(1.0, 1.0)), uv_fract - vec2(1.0, 1.0)), blur.x), blur.y) * 0.5 + 0.5;
}

float fbm(vec2 uv) {
    float value = 0.0;
    float amplitude = 0.4;
    float frequency = 3.0;
    for (int i = 0; i < 4; i++) {
        value += amplitude * noise(uv * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

float grain(vec2 uv, float time) {
    return fract(sin(dot(uv, vec2(12.9898, 78.233) * time)) * 43758.5453);
}

vec2 warp(vec2 uv) {
    vec2 delta = uv - 0.5;
    float delta2 = dot(delta.xy, delta.xy);
    float delta_offset = delta2 * delta2 * warp_amount;
    delta_offset += sin(time * 0.5) * 0.01;
    return uv + delta * delta_offset;
}

vec2 apply_tremor(vec2 uv, float intensity) {
    float tremor_x = sin(time * 25.0) * cos(time * 13.0) * intensity;
    float tremor_y = cos(time * 17.0) * sin(time * 23.0) * intensity;
    return uv + vec2(tremor_x, tremor_y);
}

float border(vec2 uv) {
    float radius = min(warp_amount, 0.08);
    radius = max(min(min(abs(radius * 2.0), abs(1.0)), abs(1.0)), 1e-5);
    vec2 abs_uv = abs(uv * 2.0 - 1.0) - vec2(1.0, 1.0) + radius;
    float dist = length(max(vec2(0.0), abs_uv)) / radius;
    float square = smoothstep(0.96, 1.0, dist);
    return clamp(1.0 - square, 0.0, 1.0);
}

float vignette(vec2 uv, float time) {
    uv *= 1.0 - uv.xy;
    float vig = uv.x * uv.y * 15.0;
    float pulse = sin(time * 0.5) * 0.03;
    return pow(vig, vignette_intensity * vignette_opacity + pulse);
}

float sega_vignette(vec2 uv) {
    uv = uv * 2.0 - 1.0;
    float vig = 1.0 - dot(uv, uv) * 0.45;
    return clamp(pow(vig, 1.8), 0.0, 1.0);
}

float arcade_bars(vec2 uv) {
    float bar_size = 0.08;
    return (uv.y < bar_size || uv.y > 1.0 - bar_size) ? 0.0 : 1.0;
}

float dither_pattern(vec2 uv) {
    int x = int(mod(floor(uv.x * resolution.x), 2.0));
    int y = int(mod(floor(uv.y * resolution.y), 2.0));
    return ((x == 0 && y == 0) || (x == 1 && y == 1)) ? 0.9 : 1.0;
}

float toGrayscale(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

void main() {
    vec2 warped_uv = uv;
    vec2 tex_uv;
    
    if (tremor > 0.0) {
        warped_uv = apply_tremor(warped_uv, tremor * 0.02);
    }
    
    float border_mask = 1.0;
    if (clip_warp) {
        border_mask = border(warped_uv);
        warped_uv = mix(uv, warped_uv, border_mask);
    }
    
    vec4 base_color = texture(bg_surf, warped_uv);
    vec4 src_color = texture(surface, warped_uv);
    
    if (src_color.a > 0.5) {
        base_color = src_color;
    }
    
    vec4 ui_color = texture(ui_surf, warped_uv);
    if (ui_color.r > 0.0) {
        base_color += ui_color;
    }
    
    tex_uv = warped_uv;
    if (pixelate) {
        tex_uv = floor(tex_uv * resolution + 0.5) / resolution;
    }
    
    float roll_line = 0.0;
    if (roll || noise_opacity > 0.0) {
        roll_line = smoothstep(0.3, 0.9, sin(tex_uv.y * roll_size - (time * roll_speed)));
        roll_line *= roll_line * smoothstep(0.3, 0.9, sin(tex_uv.y * roll_size * roll_variation - (time * roll_speed * roll_variation)));
    }
    
    vec2 roll_uv = vec2((roll_line * distort_intensity * (1.0 - tex_uv.x)), 0.0);
    vec4 tex;
    
    if (roll) {
        tex.r = texture(bg_surf, tex_uv + roll_uv * 0.8 + vec2(aberration, 0.0) * 0.1).r;
        tex.g = texture(bg_surf, tex_uv + roll_uv * 1.2 - vec2(aberration, 0.0) * 0.1).g;
        tex.b = texture(bg_surf, tex_uv + roll_uv).b;
        tex.a = 1.0;
    } else {
        tex.r = texture(bg_surf, tex_uv + vec2(aberration, 0.0) * 0.1).r;
        tex.g = texture(bg_surf, tex_uv - vec2(aberration, 0.0) * 0.1).g;
        tex.b = texture(bg_surf, tex_uv).b;
        tex.a = 1.0;
    }
    
    tex = mix(tex, base_color, 0.6);
    
    if (grille_opacity > 0.0) {
        float g_r = smoothstep(0.85, 0.95, abs(sin(tex_uv.x * (resolution.x * 3.14159265))));
        tex.r = mix(tex.r, tex.r * g_r, grille_opacity);
        float g_g = smoothstep(0.85, 0.95, abs(sin(1.05 + tex_uv.x * (resolution.x * 3.14159265))));
        tex.g = mix(tex.g, tex.g * g_g, grille_opacity);
        float b_b = smoothstep(0.85, 0.95, abs(sin(2.1 + tex_uv.x * (resolution.x * 3.14159265))));
        tex.b = mix(tex.b, tex.b * b_b, grille_opacity);
    }
    
    float noise_val = fbm(tex_uv * 2.5 + time * 0.01);
    float static_noise = grain(tex_uv, time * noise_speed);
    tex.rgb += static_noise * static_noise_intensity * noise_gain;
    
    float gray = toGrayscale(tex.rgb);
    tex.rgb = mix(tex.rgb, vec3(gray), desaturation);
    float flicker = 1.0 + sin(time * 7.5) * flicker_intensity;
    
    tex.rgb *= flicker;
    tex.rgb = clamp(tex.rgb * brightness, 0.0, 1.0);
    
    if (!fight) {
        tex.rgb *= vignette(tex_uv, time);
    }
    
    if (fight) {
        tex.rgb *= arcade_bars(tex_uv);
        tex.rgb *= sega_vignette(tex_uv);
        
        float shadow_dist = 0.002;
        vec4 shadow_sample = texture(surface, tex_uv + vec2(shadow_dist, shadow_dist));
        if (shadow_sample.a > 0.01 && src_color.a < 0.5) {
            tex.rgb = mix(tex.rgb, vec3(0.0, 0.0, 0.0), 0.5);
        }
        
        tex.rgb = pow(tex.rgb, vec3(1.1));
    } else {
        tex.rgb = mix(tex.rgb, vec3(tex.r, tex.g, tex.b), 0.35); 
        tex.rgb *= 0.9;
    }

    if (transition < 1.0) {
        // Apply only darkness based on transition progress (no swirl)
        tex.rgb *= transition;
    }

    if (e_transition < 1.0) {
        float block = floor(tex_uv.y * 10.0) + floor(tex_uv.x * 10.0);
        float noise = grain(tex_uv, time * 5.0);
        
        float t = e_transition * 1.2;
        float appear = step(1.0 - t, noise + sin(block) * 0.2);
        
        if (appear < 0.5) {
            float displace = (1.0 - e_transition) * 0.05 * sin(tex_uv.y * 50.0 + time * 5.0);
            vec2 glitch_uv = tex_uv + vec2(displace, 0.0);
            
            float split = (1.0 - e_transition) * 0.1;
            tex.r = texture(bg_surf, tex_uv + vec2(split, 0.0)).r;
            tex.g = texture(bg_surf, tex_uv).g;
            tex.b = texture(bg_surf, tex_uv - vec2(split, 0.0)).b;
            
            if (noise > 0.95) {
                tex.rgb = vec3(noise);
            }
            
            if (noise > 0.8 && sin(time * 10.0) > 0.0) {
                tex.rgb = 1.0 - tex.rgb;
            }
        }
    }

    f_color = tex;
}