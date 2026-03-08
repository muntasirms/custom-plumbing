from build123d import *

# Conversion factor
IN = 25.4

def generate_coupling(left_id_in, right_id_in, angle=180):
    """
    Generates a parameterized hose barb coupling cleanly.
    Includes support for angled couplings (e.g., 90-degree elbows).
    Default angle is 180 (straight coupling).
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
    
    # --- Helper: Generate a single barb section ---
    # Builds locally with base at X=0, tip extending into +X
    def create_barb_part(bore_r, max_r, min_r, pitch, count, tip):
        pts = []
        x = 0
        # Base attaching to center flange
        pts.append((x, bore_r))
        pts.append((x, max_r)) 
        
        # Barb ramps (smooth ramp down toward tip, sharp step back up)
        for i in range(count):
            x += pitch
            pts.append((x, min_r))
            if i < count - 1:
                pts.append((x, max_r))
                
        # Tip length and drop to inner bore
        x += tip
        pts.append((x, min_r))
        pts.append((x, bore_r))
        
        with BuildPart() as barb:
            with BuildSketch(Plane.XY):
                with BuildLine():
                    Polyline(*pts, close=True)
                make_face()
            revolve(axis=Axis.X)
        return barb.part

    # --- 1. Center Elbow/Flange Generation ---
    with BuildPart() as elbow:
        with BuildLine() as path:
            if angle == 180:
                # Straight line path
                Line((0, 0, 0), (center_w, 0, 0))
            else:
                # Circular arc path for elbow
                bend_angle = 180 - angle
                bend_r = max(id_L, id_R) * 1.5 + center_r
                CenterArc((0, bend_r, 0), bend_r, start_angle=-90, arc_size=bend_angle)
                
        # Extract starting and ending vectors of the path
        path_edge = path.edges()[0]
        p_start = path_edge @ 0
        t_start = path_edge % 0
        p_end = path_edge @ 1
        t_end = path_edge % 1
        
        # Create planes normal to the start and end of the path
        plane1 = Plane(origin=p_start, z_dir=t_start)
        plane2 = Plane(origin=p_end, z_dir=t_end)
        
        # Sweep multisection: Naturally handles transitioning inner bore sizes!
        with BuildSketch(plane1) as sk1:
            Circle(center_r)
            Circle(bore_r_L, mode=Mode.SUBTRACT)
        with BuildSketch(plane2) as sk2:
            Circle(center_r)
            Circle(bore_r_R, mode=Mode.SUBTRACT)
            
        sweep([sk1.sketch, sk2.sketch], path=path_edge, multisection=True)
        
        # Apply chamfer to outer edges before assembling
        try:
            flange_edges = elbow.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)[-2:]
            chamfer(flange_edges, length=0.5)
        except Exception:
            pass

    # --- 2. Final Assembly ---
    with BuildPart() as coupling:
        add(elbow.part)
        
        # Build Left Barb and map it exactly to the start of the elbow pointing outwards
        left_barb = create_barb_part(bore_r_L, max_r_L, min_r_L, pitch_L, count_L, tip_L)
        left_plane = Plane(origin=p_start, x_dir=-t_start, z_dir=(0, 0, 1))
        with Locations(Location(left_plane)):
            add(left_barb)
            
        # Build Right Barb and map it exactly to the end of the elbow pointing outwards
        right_barb = create_barb_part(bore_r_R, max_r_R, min_r_R, pitch_R, count_R, tip_R)
        right_plane = Plane(origin=p_end, x_dir=t_end, z_dir=(0, 0, 1))
        with Locations(Location(right_plane)):
            add(right_barb)
            
    return coupling.part

# --- Execution ---
if __name__ == "__main__":
    print("Generating 1/4 to 1/8 straight coupling...")
    c1 = generate_coupling(1/4, 1/8*1.05, angle=90)
    export_step(c1, "coupling_1-4_to_1-8_straight.step")

    print("Generating 3/4 to 1/2 90-degree elbow coupling...")
    c2 = generate_coupling(3/4, 1/2, angle=90)
    export_step(c2, "coupling_3-4_to_1-2_90deg.step")
    
    print("Generating 3/8 straight coupling...")
    c3 = generate_coupling(3/8, 3/8, angle=180)
    export_step(c3, "coupling_3-8_straight.step")

    print("Done! Files exported successfully.")
