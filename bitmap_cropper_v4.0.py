import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel, colorchooser
from PIL import Image, ImageTk, ImageDraw
import os

class BitmapCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitmap Font Repacker V4.0 (Ultimate)")
        # Increased size to accommodate new options and tabs
        self.root.geometry("700x650") 
        
        style = ttk.Style()
        style.theme_use('clam')
        
        try:
            self.root.iconbitmap("bmfr.ico")
        except tk.TclError:
            # print("bmfr.ico not found, using built-in app icon.")
            pass
        
        # Data
        self.source_image_path = None
        self.source_image = None # The raw loaded image
        self.mask_color = None # Holds RGB tuple if set
        self.exceptions = {} # Stores { index: {dx, dy, dw, dh} }
        self.relocation_map = {} # Stores { target_index : source_index }

        # --- UI START ---
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=5, fill="both", expand=True)

        # ===========================
        # TAB 1: GENERAL SETTINGS
        # ===========================
        self.tab_general = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_general, text="General Settings")

        # 1.1 Source & Mask
        self.frame_file = ttk.LabelFrame(self.tab_general, text="1. Import Font & Mask Transparency", padding=10)
        self.frame_file.pack(padx=10, pady=5, fill="x")
        
        btn_frame = ttk.Frame(self.frame_file)
        btn_frame.pack(side="left", fill="y")
        ttk.Button(btn_frame, text="Select Image", command=self.load_image).pack(side="top", fill="x", pady=2)
        ttk.Button(btn_frame, text="Set Mask Color", command=self.choose_mask_color).pack(side="bottom", fill="x", pady=2)
        
        info_frame = ttk.Frame(self.frame_file)
        info_frame.pack(side="left", padx=10)
        self.lbl_file_status = ttk.Label(info_frame, text="No file selected", foreground="gray")
        self.lbl_file_status.pack(anchor="w")
        self.lbl_mask_status = ttk.Label(info_frame, text="No mask set (opaque)", foreground="gray")
        self.lbl_mask_status.pack(anchor="w")
        # Small canvas to show selected color
        self.mask_canvas = tk.Canvas(self.frame_file, width=30, height=30, bg="#ccc", highlightthickness=1, highlightbackground="gray")
        self.mask_canvas.pack(side="right", padx=5)

        # 1.2 Base Grid & Orientation
        self.frame_config = ttk.LabelFrame(self.tab_general, text="2. Base Grid Size & Orientation", padding=10)
        self.frame_config.pack(padx=10, pady=5, fill="x")
        ttk.Label(self.frame_config, text="Char W:").grid(row=0, column=0)
        self.entry_char_w = ttk.Entry(self.frame_config, width=5); self.entry_char_w.insert(0, "8"); self.entry_char_w.grid(row=0, column=1, padx=2)
        ttk.Label(self.frame_config, text="Char H:").grid(row=0, column=2)
        self.entry_char_h = ttk.Entry(self.frame_config, width=5); self.entry_char_h.insert(0, "16"); self.entry_char_h.grid(row=0, column=3, padx=2)
        
        ttk.Label(self.frame_config, text="Scan Dir:", foreground="blue").grid(row=0, column=4, padx=(10,2))
        self.combo_orientation = ttk.Combobox(self.frame_config, values=["Horizontal (Z-pattern)", "Vertical (N-pattern)"], state="readonly", width=18)
        self.combo_orientation.current(0)
        self.combo_orientation.grid(row=0, column=5)

        # 1.3 Global Offsets
        self.frame_gaps = ttk.LabelFrame(self.tab_general, text="3. Global Offsets (Margins/Gaps)", padding=10)
        self.frame_gaps.pack(padx=10, pady=5, fill="x")
        ttk.Label(self.frame_gaps, text="Start Off X:").grid(row=0, column=0); self.entry_off_x = ttk.Entry(self.frame_gaps, width=4); self.entry_off_x.insert(0, "0"); self.entry_off_x.grid(row=0, column=1)
        ttk.Label(self.frame_gaps, text="Start Off Y:").grid(row=0, column=2); self.entry_off_y = ttk.Entry(self.frame_gaps, width=4); self.entry_off_y.insert(0, "0"); self.entry_off_y.grid(row=0, column=3)
        ttk.Label(self.frame_gaps, text="Gap X:").grid(row=1, column=0); self.entry_gap_x = ttk.Entry(self.frame_gaps, width=4); self.entry_gap_x.insert(0, "0"); self.entry_gap_x.grid(row=1, column=1)
        ttk.Label(self.frame_gaps, text="Gap Y:").grid(row=1, column=2); self.entry_gap_y = ttk.Entry(self.frame_gaps, width=4); self.entry_gap_y.insert(0, "0"); self.entry_gap_y.grid(row=1, column=3)

        # 1.4 Space Limits (New Feature)
        self.frame_limits = ttk.LabelFrame(self.tab_general, text="4. Source Region Limits (Optional)", padding=10)
        self.frame_limits.pack(padx=10, pady=5, fill="x")
        ttk.Label(self.frame_limits, text="Limit Start X:", foreground="red").grid(row=0, column=0)
        self.entry_lim_sx = ttk.Entry(self.frame_limits, width=5); self.entry_lim_sx.insert(0, "0"); self.entry_lim_sx.grid(row=0, column=1)
        ttk.Label(self.frame_limits, text="Limit Start Y:", foreground="red").grid(row=0, column=2)
        self.entry_lim_sy = ttk.Entry(self.frame_limits, width=5); self.entry_lim_sy.insert(0, "0"); self.entry_lim_sy.grid(row=0, column=3)
        
        ttk.Label(self.frame_limits, text="Limit End X:", foreground="red").grid(row=1, column=0)
        self.entry_lim_ex = ttk.Entry(self.frame_limits, width=5); self.entry_lim_ex.insert(0, "9999"); self.entry_lim_ex.grid(row=1, column=1)
        ttk.Label(self.frame_limits, text="Limit End Y:", foreground="red").grid(row=1, column=2)
        self.entry_lim_ey = ttk.Entry(self.frame_limits, width=5); self.entry_lim_ey.insert(0, "9999"); self.entry_lim_ey.grid(row=1, column=3)
        ttk.Label(self.frame_limits, text="(Defines bounding box to scan)", font=("Arial", 8), foreground="gray").grid(row=0, column=4, rowspan=2, padx=5)

        # 1.5 Output
        self.frame_layout = ttk.LabelFrame(self.tab_general, text="5. Output Spacing & Filling", padding=10)
        self.frame_layout.pack(padx=10, pady=5, fill="x")
        
        self.combo_spacing = ttk.Combobox(self.frame_layout, values=["320x16 (8x8 ref)", "320x48 (16x16 ref)", "320x192 (32x32 ref)", "Custom"], state="readonly")
        self.combo_spacing.current(1)
        self.combo_spacing.pack(fill="x", pady=(0, 5))
        
        fill_frame = ttk.Frame(self.frame_layout)
        fill_frame.pack(fill="x")
        ttk.Label(fill_frame, text="Target Start Index Offset:", foreground="purple").pack(side="left")
        self.entry_start_offset = ttk.Entry(fill_frame, width=5)
        self.entry_start_offset.insert(0, "0")
        self.entry_start_offset.pack(side="left", padx=5)
        ttk.Label(fill_frame, text="(Leaves empty slots at start of output)", font=("Arial", 8), foreground="gray").pack(side="left")

        # ===========================
        # TAB 2: EXCEPTIONS
        # ===========================
        self.tab_ex = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ex, text="Individual Exceptions")

        self.lbl_ex_info = ttk.Label(self.tab_ex, text="Fix characters that are bigger than the grid (e.g., hanging comma).", foreground="gray")
        self.lbl_ex_info.pack(pady=5)

        # Selector
        self.frame_ex_sel = ttk.Frame(self.tab_ex)
        self.frame_ex_sel.pack(fill="x", padx=10)
        ttk.Label(self.frame_ex_sel, text="Select Source Char Index:").pack(side="left")
        
        # Generate ASCII list for spinner
        self.char_list = []
        for i in range(0, 256): 
            char_vis = chr(i + 32) if i + 32 < 127 else "?"
            if i+32 == 32: char_vis = "Space"
            self.char_list.append(f"{i} : [{char_vis}]")
            
        self.combo_char = ttk.Combobox(self.frame_ex_sel, values=self.char_list, state="readonly", width=18)
        self.combo_char.current(12) # Default to comma area
        self.combo_char.pack(side="left", padx=5)

        # Inputs for overrides
        self.frame_ex_opt = ttk.LabelFrame(self.tab_ex, text="Modify Cut Box for this Char", padding=10)
        self.frame_ex_opt.pack(padx=10, pady=10, fill="x")

        # Grid for overrides
        ttk.Label(self.frame_ex_opt, text="Extra Width:", foreground="blue").grid(row=0, column=0)
        self.ex_dw = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dw.insert(0,"0"); self.ex_dw.grid(row=0, column=1)
        ttk.Label(self.frame_ex_opt, text="Extra Height:", foreground="blue").grid(row=0, column=2)
        self.ex_dh = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dh.insert(0,"0"); self.ex_dh.grid(row=0, column=3)
        ttk.Label(self.frame_ex_opt, text="Offset X:", foreground="red").grid(row=1, column=0)
        self.ex_dx = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dx.insert(0,"0"); self.ex_dx.grid(row=1, column=1)
        ttk.Label(self.frame_ex_opt, text="Offset Y:", foreground="red").grid(row=1, column=2)
        self.ex_dy = ttk.Entry(self.frame_ex_opt, width=5); self.ex_dy.insert(0,"0"); self.ex_dy.grid(row=1, column=3)
        
        self.btn_add_ex = ttk.Button(self.frame_ex_opt, text="Set/Update Exception", command=self.add_exception)
        self.btn_add_ex.grid(row=2, column=0, columnspan=4, sticky="we", pady=5)

        # List of active exceptions
        self.tree = ttk.Treeview(self.tab_ex, columns=("ID", "Char", "Mods"), show='headings', height=8)
        self.tree.heading("ID", text="Source ID"); self.tree.column("ID", width=60)
        self.tree.heading("Char", text="Ref Char"); self.tree.column("Char", width=60)
        self.tree.heading("Mods", text="Modifications"); self.tree.column("Mods", width=200)
        self.tree.pack(padx=10, fill="both", expand=True)
        self.btn_del_ex = ttk.Button(self.tab_ex, text="Remove Selected", command=self.remove_exception)
        self.btn_del_ex.pack(pady=5)

        # ===========================
        # TAB 3: RELOCATION (New Feature)
        # ===========================
        self.tab_reloc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reloc, text="Character Relocation")

        ttk.Label(self.tab_reloc, text="Map a Source Index (crop order) to a different Target Index (output position).", foreground="gray", wraplength=600).pack(pady=5)

        self.frame_reloc_input = ttk.LabelFrame(self.tab_reloc, text="Create Mapping", padding=10)
        self.frame_reloc_input.pack(fill="x", padx=10)

        ttk.Label(self.frame_reloc_input, text="Put Source ID:").grid(row=0, column=0)
        self.entry_reloc_src = ttk.Entry(self.frame_reloc_input, width=5)
        self.entry_reloc_src.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.frame_reloc_input, text="Into Target Position:").grid(row=0, column=2)
        self.combo_reloc_target = ttk.Combobox(self.frame_reloc_input, values=self.char_list, state="readonly", width=18)
        self.combo_reloc_target.current(33) # Default somewhere around 'A'
        self.combo_reloc_target.grid(row=0, column=3, padx=5)

        ttk.Button(self.frame_reloc_input, text="Set Mapping", command=self.add_mapping).grid(row=0, column=4, padx=10)

        # Treeview for relocations
        self.tree_reloc = ttk.Treeview(self.tab_reloc, columns=("TID", "TChar", "SID"), show='headings', height=8)
        self.tree_reloc.heading("TID", text="Target ID"); self.tree_reloc.column("TID", width=60)
        self.tree_reloc.heading("TChar", text="Target Char"); self.tree_reloc.column("TChar", width=80)
        self.tree_reloc.heading("SID", text="Uses Source ID"); self.tree_reloc.column("SID", width=80)
        self.tree_reloc.pack(padx=10, pady=10, fill="both", expand=True)

        self.btn_del_reloc = ttk.Button(self.tab_reloc, text="Remove Selected Mapping", command=self.remove_mapping)
        self.btn_del_reloc.pack(pady=5)

        # ===========================
        # TAB 4: ABOUT
        # ===========================
        self.tab_about = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_about, text="About")
        # (Content same as provided code)
        self.frame_auth = ttk.LabelFrame(self.tab_about, text="Authors", padding=10)
        self.frame_auth.pack(padx=10, pady=10, fill="x")
        self.lbl_auth_info = ttk.Label(self.frame_auth, text="FakeCells Software - Lead programming\nKelleesh24 - Script Supervisor\nLord Louvre - Script Contributions\nThird-party - Betatesting and feedback scripting", foreground="black")
        self.lbl_auth_info.pack(pady=5)
        self.frame_libs = ttk.LabelFrame(self.tab_about, text="Software used", padding=10)
        self.frame_libs.pack(padx=10, pady=10, fill="x")
        self.lbl_lib_info = ttk.Label(self.frame_libs, text="Pillow - by Jeffrey A. Clark and others (https://pypi.org/project/pillow/)\nThonny - by Aivar Annamaa (https://thonny.org/)", foreground="black")
        self.lbl_lib_info.pack(pady=5)
        self.frame_src = ttk.LabelFrame(self.tab_about, text="Support methods", padding=10)
        self.frame_src.pack(padx=10, pady=10, fill="x")
        self.lbl_src_info = ttk.Label(self.frame_src, text="You can support our project or contributors through our GitHub pages:\nhttps://github.com/fakecells/bitmap-cropper\nhttps://github.com/Kelleesh24/", foreground="black")
        self.lbl_src_info.pack(pady=5)

        # BOTTOM BUTTONS
        self.frame_actions = ttk.Frame(root)
        self.frame_actions.pack(padx=10, pady=10, fill="x", side="bottom")
        self.btn_preview = ttk.Button(self.frame_actions, text="PREVIEW CUTS & MASK", command=self.show_preview)
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=5)
        self.btn_process = ttk.Button(self.frame_actions, text="SAVE REPACKED FONT", command=self.process_image)
        self.btn_process.pack(side="left", fill="x", expand=True, padx=5)

    # --- LOGIC ---

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.bmp")])
        if file_path:
            self.source_image_path = file_path
            self.source_filename = os.path.splitext(os.path.basename(file_path))[0]
            self.lbl_file_status.config(text=file_path.split("/")[-1], foreground="green")
            # Always convert to RGBA for consistent processing
            self.source_image = Image.open(file_path).convert("RGBA") 

    def choose_mask_color(self):
        color = colorchooser.askcolor(title="Select Color to Make Transparent")
        if color[0]:
            # color is ((r, g, b), '#rrggbb')
            self.mask_color = tuple(map(int, color[0]))
            self.lbl_mask_status.config(text=f"Mask: {self.mask_color}", foreground="blue")
            self.mask_canvas.config(bg=color[1])
        else:
            self.mask_color = None
            self.lbl_mask_status.config(text="No mask set (opaque)", foreground="gray")
            self.mask_canvas.config(bg="#ccc")

    def add_exception(self):
        try:
            sel_str = self.combo_char.get()
            idx = int(sel_str.split(":")[0].strip())
            dx = int(self.ex_dx.get())
            dy = int(self.ex_dy.get())
            dw = int(self.ex_dw.get())
            dh = int(self.ex_dh.get())
            self.exceptions[idx] = {'dx': dx, 'dy': dy, 'dw': dw, 'dh': dh}
            self.refresh_tree()
        except ValueError:
            messagebox.showerror("Error", "Inputs must be integers")

    def remove_exception(self):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])
            idx = int(item['values'][0])
            del self.exceptions[idx]
            self.refresh_tree()

    def refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, val in self.exceptions.items():
            char_vis = chr(idx + 32) if idx+32 < 127 else "?"
            mods = f"X:{val['dx']} Y:{val['dy']} W+{val['dw']} H+{val['dh']}"
            self.tree.insert("", "end", values=(idx, char_vis, mods))

    def add_mapping(self):
        try:
            src_id = int(self.entry_reloc_src.get())
            target_sel = self.combo_reloc_target.get()
            target_id = int(target_sel.split(":")[0].strip())
            self.relocation_map[target_id] = src_id
            self.refresh_reloc_tree()
        except ValueError:
             messagebox.showerror("Error", "Please enter a valid Source ID integer.")

    def remove_mapping(self):
        sel = self.tree_reloc.selection()
        if sel:
            item = self.tree_reloc.item(sel[0])
            tid = int(item['values'][0])
            del self.relocation_map[tid]
            self.refresh_reloc_tree()

    def refresh_reloc_tree(self):
        for i in self.tree_reloc.get_children():
            self.tree_reloc.delete(i)
        # Sort by target ID for easier reading
        sorted_keys = sorted(self.relocation_map.keys())
        for tid in sorted_keys:
            sid = self.relocation_map[tid]
            char_vis = chr(tid + 32) if tid+32 < 127 else "?"
            self.tree_reloc.insert("", "end", values=(tid, char_vis, sid))

    def get_config(self):
        # Gather all inputs
        try:
            return {
                'cw': int(self.entry_char_w.get()), 'ch': int(self.entry_char_h.get()),
                'offx': int(self.entry_off_x.get()), 'offy': int(self.entry_off_y.get()),
                'gapx': int(self.entry_gap_x.get()), 'gapy': int(self.entry_gap_y.get()),
                'lsx': int(self.entry_lim_sx.get()), 'lsy': int(self.entry_lim_sy.get()),
                'lex': int(self.entry_lim_ex.get()), 'ley': int(self.entry_lim_ey.get()),
                'orient': self.combo_orientation.get(),
                'start_offset': int(self.entry_start_offset.get())
            }
        except ValueError:
             messagebox.showerror("Error", "Please ensure all numeric inputs in General Settings are valid integers.")
             return None

    def get_crop_boxes(self):
        if not self.source_image: return [], 0, 0, 0
        cfg = self.get_config()
        if not cfg: return [], 0, 0, 0
        
        # Determine Grid Dimensions
        sel = self.combo_spacing.get()
        # (Simplified grid logic based on previous example)
        if "8x8 ref" in sel: ref_w, ref_h, ref_tile = 320, 16, 8
        elif "32x32 ref" in sel: ref_w, ref_h, ref_tile = 320, 192, 32
        else: ref_w, ref_h, ref_tile = 320, 48, 16 # Default 320x48 (16x16 ref)
            
        cols = ref_w // ref_tile
        rows = ref_h // ref_tile
        total_needed = cols * rows
        
        boxes = []
        
        src_w, src_h = self.source_image.size
        stride_x = cfg['cw'] + cfg['gapx']
        stride_y = cfg['ch'] + cfg['gapy']
        
        count = 0
        
        # --- Scanning Logic with Orientation and Limits ---
        
        if "Horizontal" in cfg['orient']:
            # Standard Z-pattern: Scan Y, then X
            scan_y = cfg['offy']
            while scan_y < src_h and count < total_needed:
                if scan_y > cfg['ley']: break # Limit End Y check

                scan_x = cfg['offx']
                while scan_x < src_w and count < total_needed:
                    if scan_x > cfg['lex']: break # Limit End X check
                    
                    # Limit Start checks (skip if before start point)
                    if scan_y >= cfg['lsy'] and scan_x >= cfg['lsx']:
                        boxes.append(self.calculate_box(scan_x, scan_y, cfg, count))
                        count += 1
                    
                    scan_x += stride_x
                scan_y += stride_y
        else:
             # Vertical N-pattern: Scan X, then Y
            scan_x = cfg['offx']
            while scan_x < src_w and count < total_needed:
                if scan_x > cfg['lex']: break # Limit End X check

                scan_y = cfg['offy']
                while scan_y < src_h and count < total_needed:
                    if scan_y > cfg['ley']: break # Limit End Y check

                    # Limit Start checks
                    if scan_y >= cfg['lsy'] and scan_x >= cfg['lsx']:
                        boxes.append(self.calculate_box(scan_x, scan_y, cfg, count))
                        count += 1
                        
                    scan_y += stride_y
                scan_x += stride_x
            
        return boxes, cols, rows, cfg['start_offset']

    def calculate_box(self, x, y, cfg, count):
        w, h = cfg['cw'], cfg['ch']
        # APPLY EXCEPTION?
        if count in self.exceptions:
            ex = self.exceptions[count]
            x += ex['dx']
            y += ex['dy']
            w += ex['dw']
            h += ex['dh']
        return (x, y, x+w, y+h)

    def get_processed_source_image(self):
        # Applies mask transparency if selected
        img = self.source_image.copy()
        if self.mask_color:
            # Create a mask: True where color matches, False otherwise
            # We need to handle potentially slightly different RGB vs RGBA tuples
            target_rgb = self.mask_color[:3]
            
            data = img.getdata()
            new_data = []
            for item in data:
                # Check RGB values, ignore existing alpha for match
                if item[:3] == target_rgb:
                    new_data.append((0, 0, 0, 0)) # Transparent
                else:
                    new_data.append(item)
            img.putdata(new_data)
        return img

    def show_preview(self):
        try:
            if not self.source_image:
                 messagebox.showwarning("Warning", "Load image first.")
                 return

            boxes, _, _, _ = self.get_crop_boxes()
            
            # Get image with transparency mask applied
            preview = self.get_processed_source_image()
            
            draw = ImageDraw.Draw(preview)
            for b in boxes:
                draw.rectangle(b, outline="red", width=1)
                
            top = Toplevel(self.root)
            top.title("Preview Cuts & Mask")
            
            if preview.width < 300: preview = preview.resize((preview.width*2, preview.height*2), Image.NEAREST)
            
            self.tk_prev = ImageTk.PhotoImage(preview)
            ttk.Label(top, image=self.tk_prev).pack()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def process_image(self):
        try:
            if not self.source_image:
                 messagebox.showwarning("Warning", "Load image first.")
                 return

            boxes, cols, rows, start_offset = self.get_crop_boxes()
            cfg = self.get_config()
            
            # 1. Prepare Source (Apply Mask)
            processed_source = self.get_processed_source_image()

            # 2. Crop all glyphs from source
            source_glyphs = []
            for box in boxes:
                 source_glyphs.append(processed_source.crop(box))
            
            num_source_glyphs = len(source_glyphs)
            if num_source_glyphs == 0:
                 messagebox.showwarning("Warning", "No characters found based on current settings and limits.")
                 return

            # 3. Create Target Canvas
            out_w = cols * cfg['cw']
            out_h = rows * cfg['ch']
            new_img = Image.new("RGBA", (out_w, out_h), (0,0,0,0))
            
            # 4. Paste loop (incorporating Start Offset and Relocation)
            total_target_slots = cols * rows
            
            # We iterate through target slots
            for target_idx in range(total_target_slots):
                
                # A. Apply Space Filling (Start Offset)
                if target_idx < start_offset:
                    continue # Skip slots before the offset

                # Determine the effective 'logical' index for mapping purposes
                logical_idx = target_idx - start_offset

                # B. Apply Relocation Mapping
                # If this target slot is mapped, use the specified source index.
                # Otherwise, use the direct logical index.
                source_idx_to_use = self.relocation_map.get(logical_idx, logical_idx)
                
                # C. Paste if the source index exists
                if source_idx_to_use < num_source_glyphs:
                    glyph = source_glyphs[source_idx_to_use]
                    
                    # Calculate target position
                    r = target_idx // cols
                    c = target_idx % cols
                    px = c * cfg['cw']
                    py = r * cfg['ch']
                    
                    # Paste glyph, using itself as mask for transparency
                    new_img.paste(glyph, (px, py), glyph)
                
            default_name = f"{self.source_filename}-repacked.png" if self.source_image_path else "repacked_font.png"
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[("PNG Image", "*.png")])
            
            if save_path:
                new_img.save(save_path)
                msg = (f"The repacked charset has been saved succesfully!\n\n"
                       f"Grid Layout: {cols} Cols x {rows} Rows\n"
                       f"Output Size: {out_w}x{out_h}\n"
                       f"Mask Applied: {'Yes' if self.mask_color else 'No'}\n"
                       f"Saved to: {save_path}")
                messagebox.showinfo("Done", msg)
                
        except Exception as e:
            # import traceback
            # traceback.print_exc() # Useful for debugging
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = BitmapCropperApp(root)
    root.mainloop()