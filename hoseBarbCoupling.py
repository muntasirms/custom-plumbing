from build123d import *

# Conversion factor
IN = 25.4

def generate_coupling(left_id_in, right_id_in):
    """
    Generates a parameterized hose barb coupling cleanly in the positive coordinate space.
    """
    id_L = left_id_in * IN
    id_R = right_id_in * IN
    
    # --- Dynamic Ratios & Scaling ---
    max_r_L = (id_L * 1.20) / 2
    max_r_R = (id_R * 1.20) / 2
    
    min_r_L = (id_L * 1.05) / 2
    min_r_R = (id_R * 1.05) / 2
    
    wall_L = max(1.2, id_L * 0.15)
    wall_R = max(1.2, id_R * 0.15)
    
    bore_r_L = max(1.2, min_r_L - wall_L)
    bore_r_R = max(1.2, min_r_R - wall_R)
    
    pitch_L = max(2.5, id_L * 0.5)
    pitch_R = max(2.5, id_R * 0.5)
    
    count_L = max(3, int((id_L * 1.5) / pitch_L))
    count_R = max(3, int((id_R * 1.5) / pitch_R))
    
    tip_L = pitch_L * 0.8
    tip_R = pitch_R * 0.8
    
    center_w = max(3.0, max(id_L, id_R) * 0.25)
    center_r = max(max_r_L, max_r_R) + 2.5
    
    # --- Profile Generation (Strictly Positive Space) ---
    pts = []
    x = 0  
    
    # 1. Start at bottom left (inner bore)
    pts.append((x, bore_r_L))
    
    # 2. Left face of the tip
    pts.append((x, min_r_L))
    
    # 3. Left tip length
    x += tip_L
    pts.append((x, min_r_L))
    
    # 4. Left barbs
    for i in range(count_L):
        x += pitch_L
        pts.append((x, max_r_L)) # Smooth ramp UP
        if i < count_L - 1:
            pts.append((x, min_r_L)) # Sharp drop DOWN to stem
            
    # 5. Left face of the center flange
    pts.append((x, center_r))
    
    # 6. Top of the center flange
    x += center_w
    pts.append((x, center_r))
    
    # 7. Right face of the center flange
    pts.append((x, max_r_R))
    
    # 8. Right barbs
    for i in range(count_R):
        x += pitch_R
        pts.append((x, min_r_R)) # Smooth ramp DOWN
        if i < count_R - 1:
            pts.append((x, max_r_R)) # Sharp step UP to next barb peak
            
    # 9. Right tip length
    x += tip_R
    pts.append((x, min_r_R))
    
    # 10. Right face of the tip (dropping to inner bore)
    pts.append((x, bore_r_R))
    
    # 11. Inner bore back calculation
    right_flange_x = x - tip_R - (count_R * pitch_R)
    left_flange_x = right_flange_x - center_w
    
    # Inner bore right half
    pts.append((right_flange_x, bore_r_R))
    
    # Inner bore transition (sloped for fluid dynamics)
    pts.append((left_flange_x, bore_r_L))
    
    # --- 3D Construction ---
    with BuildPart() as coupling:
        with BuildSketch(Plane.XY):
            with BuildLine():
                Polyline(*pts, close=True)
            make_face()
            
        revolve(axis=Axis.X)
        
        try:
            flange_edges = coupling.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)[-2:]
            chamfer(flange_edges, length=0.5)
        except Exception:
            pass 
        
    return coupling.part

# --- Execution ---
if __name__ == "__main__":
    print("Generating 1/4 to 1/8 coupling...")
    c1 = generate_coupling(1/4, 1/8*1.05)
    export_step(c1, "coupling_1-4_to_1-8.step")
    export_stl(c1, "coupling_1-4_to_1-8.stl")

    print("Generating 3/4 to 1/2 coupling...")
    c2 = generate_coupling(3/4, 1/2)
    export_step(c2, "coupling_3-4_to_1-2.step")
    
    print("Generating 3/8 straight coupling...")
    c3 = generate_coupling(3/8, 3/8)
    export_step(c3, "coupling_3-8_straight.step")

    print("Done! Files exported successfully.")
