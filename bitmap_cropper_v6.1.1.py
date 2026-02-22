import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel, colorchooser
from PIL import Image, ImageTk, ImageDraw
import os

class BitmapCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitmap Font Repacker V6.1.1")
        self.root.geometry("640x600") 
        
        style = ttk.Style()
        style.theme_use('clam')
        
        try:
            self.root.iconbitmap("bmfr.ico")
        except tk.TclError:
            pass
        
        # Data
        self.source_image_path = None
        self.source_image = None 
        self.mask_color = None 
        self.exceptions = {} 
        self.relocation_map = {} 
        
        # Preview State
        self.preview_window = None
        self.preview_canvas = None
        self.preview_zoom = 1.0
        self.preview_image_ref = None # Keep reference to avoid GC
        self.preview_boxes = [] # Store current boxes for click detection

        # Toggles
        self.var_use_mask = tk.BooleanVar(value=False)
        self.var_use_limits = tk.BooleanVar(value=False)
        self.var_use_mask.trace_add("write", lambda *args: self.refresh_preview_if_open())
        self.var_use_limits.trace_add("write", lambda *args: self.refresh_preview_if_open())

        # --- UI START ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=5, fill="both", expand=True)

        # TAB 1: GENERAL SETTINGS
        self.tab_general = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_general, text="General Settings")

        # 1.1 Source & Mask
        self.frame_file = ttk.LabelFrame(self.tab_general, text="1. Import Font & Properties", padding=10)
        self.frame_file.pack(padx=10, pady=5, fill="x")
        
        btn_frame = ttk.Frame(self.frame_file)
        btn_frame.pack(side="left", fill="y")
        ttk.Button(btn_frame, text="Select Image", command=self.load_image).pack(side="top", fill="x", pady=2)
        ttk.Button(btn_frame, text="Magic Wand", command=self.auto_detect_grid).pack(side="bottom", fill="x", pady=2)
        
        mask_frame = ttk.Frame(self.frame_file)
        mask_frame.pack(side="left", padx=10, fill="y")
        ttk.Button(mask_frame, text="Set Mask Color", command=self.choose_mask_color).pack(side="top", fill="x")
        ttk.Checkbutton(mask_frame, text="Active", variable=self.var_use_mask).pack(side="bottom")

        self.mask_canvas = tk.Canvas(self.frame_file, width=30, height=30, bg="#ccc", highlightthickness=1, highlightbackground="gray")
        self.mask_canvas.pack(side="right", padx=5)
        
        self.lbl_file_status = ttk.Label(self.frame_file, text="No file selected", foreground="gray")
        self.lbl_file_status.pack(side="left", padx=10)

        # 1.2 Base Grid
        self.frame_config = ttk.LabelFrame(self.tab_general, text="2. Base Grid Size & Orientation", padding=10)
        self.frame_config.pack(padx=10, pady=5, fill="x")
        
        # We bind KeyRelease to update preview in real-time
        ttk.Label(self.frame_config, text="Char W:").grid(row=0, column=0)
        self.entry_char_w = ttk.Entry(self.frame_config, width=5); self.entry_char_w.insert(0, "8"); self.entry_char_w.grid(row=0, column=1, padx=2)
        self.entry_char_w.bind("<KeyRelease>", self.refresh_preview_if_open)
        
        ttk.Label(self.frame_config, text="Char H:").grid(row=0, column=2)
        self.entry_char_h = ttk.Entry(self.frame_config, width=5); self.entry_char_h.insert(0, "16"); self.entry_char_h.grid(row=0, column=3, padx=2)
        self.entry_char_h.bind("<KeyRelease>", self.refresh_preview_if_open)

        ttk.Label(self.frame_config, text="Scan Dir:", foreground="blue").grid(row=0, column=4, padx=(10,2))
        self.combo_orientation = ttk.Combobox(self.frame_config, values=["Horizontal (Z-pattern)", "Vertical (N-pattern)"], state="readonly", width=18)
        self.combo_orientation.current(0); self.combo_orientation.grid(row=0, column=5)
        self.combo_orientation.bind("<<ComboboxSelected>>", self.refresh_preview_if_open)

        # 1.3 Global Offsets
        self.frame_gaps = ttk.LabelFrame(self.tab_general, text="3. Global Offsets & Gaps", padding=10)
        self.frame_gaps.pack(padx=10, pady=5, fill="x")
        
        # Bindings for real-time update
        def bind_entry(entry): entry.bind("<KeyRelease>", self.refresh_preview_if_open); return entry

        ttk.Label(self.frame_gaps, text="Start Off X:").grid(row=0, column=0); self.entry_off_x = bind_entry(ttk.Entry(self.frame_gaps, width=4)); self.entry_off_x.insert(0, "0"); self.entry_off_x.grid(row=0, column=1)
        ttk.Label(self.frame_gaps, text="Start Off Y:").grid(row=0, column=2); self.entry_off_y = bind_entry(ttk.Entry(self.frame_gaps, width=4)); self.entry_off_y.insert(0, "0"); self.entry_off_y.grid(row=0, column=3)
        ttk.Label(self.frame_gaps, text="Gap X:").grid(row=1, column=0); self.entry_gap_x = bind_entry(ttk.Entry(self.frame_gaps, width=4)); self.entry_gap_x.insert(0, "0"); self.entry_gap_x.grid(row=1, column=1)
        ttk.Label(self.frame_gaps, text="Gap Y:").grid(row=1, column=2); self.entry_gap_y = bind_entry(ttk.Entry(self.frame_gaps, width=4)); self.entry_gap_y.insert(0, "0"); self.entry_gap_y.grid(row=1, column=3)

        # 1.4 Limits
        self.frame_limits = ttk.LabelFrame(self.tab_general, text="4. Source Region Limits (Optional)", padding=10)
        self.frame_limits.pack(padx=10, pady=5, fill="x")
        ttk.Checkbutton(self.frame_limits, text="Enable", variable=self.var_use_limits).grid(row=0, column=0, rowspan=2, padx=5)
        
        ttk.Label(self.frame_limits, text="Start X/Y:", foreground="red").grid(row=0, column=1)
        self.entry_lim_sx = bind_entry(ttk.Entry(self.frame_limits, width=5)); self.entry_lim_sx.insert(0, "0"); self.entry_lim_sx.grid(row=0, column=2)
        self.entry_lim_sy = bind_entry(ttk.Entry(self.frame_limits, width=5)); self.entry_lim_sy.insert(0, "0"); self.entry_lim_sy.grid(row=0, column=3)
        
        ttk.Label(self.frame_limits, text="End X/Y:", foreground="red").grid(row=1, column=1)
        self.entry_lim_ex = bind_entry(ttk.Entry(self.frame_limits, width=5)); self.entry_lim_ex.insert(0, "9999"); self.entry_lim_ex.grid(row=1, column=2)
        self.entry_lim_ey = bind_entry(ttk.Entry(self.frame_limits, width=5)); self.entry_lim_ey.insert(0, "9999"); self.entry_lim_ey.grid(row=1, column=3)

        # 1.5 Output
        self.frame_layout = ttk.LabelFrame(self.tab_general, text="5. Output Config", padding=10)
        self.frame_layout.pack(padx=10, pady=5, fill="x")
        
        # Row 1: Spacing Mode + Custom Grid inputs
        r1 = ttk.Frame(self.frame_layout)
        r1.pack(fill="x")
        
        self.combo_spacing = ttk.Combobox(r1, values=["320x16 (8x8 ref)", "320x48 (16x16 ref)", "320x192 (32x32 ref)", "Custom Grid"], state="readonly", width=18)
        self.combo_spacing.current(1)
        self.combo_spacing.pack(side="left")
        
        # New Custom Inputs
        self.frame_custom_grid = ttk.Frame(r1)
        self.frame_custom_grid.pack(side="left", padx=10)
        
        ttk.Label(self.frame_custom_grid, text="Cols:", foreground="blue").pack(side="left")
        self.entry_cust_cols = ttk.Entry(self.frame_custom_grid, width=4)
        self.entry_cust_cols.insert(0, "20") # Default 20
        self.entry_cust_cols.pack(side="left", padx=2)
        
        ttk.Label(self.frame_custom_grid, text="Rows:", foreground="blue").pack(side="left")
        self.entry_cust_rows = ttk.Entry(self.frame_custom_grid, width=4)
        self.entry_cust_rows.insert(0, "6") # Default 6
        self.entry_cust_rows.pack(side="left", padx=2)
        
        # Bind toggle event
        self.combo_spacing.bind("<<ComboboxSelected>>", self.toggle_custom_grid_inputs)

        # Row 2: Scale, Padding, Offset
        r2 = ttk.Frame(self.frame_layout)
        r2.pack(fill="x", pady=5)
        
        ttk.Label(r2, text="Scale:").pack(side="left")
        self.combo_scale = ttk.Combobox(r2, values=["0.5x", "1.0x", "2.0x", "3.0x", "4.0x"], state="readonly", width=5)
        self.combo_scale.current(1)
        self.combo_scale.pack(side="left", padx=(0,10))

        ttk.Label(r2, text="Pad X/Y:", foreground="green").pack(side="left")
        self.entry_pad_x = ttk.Entry(r2, width=4); self.entry_pad_x.insert(0,"0"); self.entry_pad_x.pack(side="left")
        self.entry_pad_y = ttk.Entry(r2, width=4); self.entry_pad_y.insert(0,"0"); self.entry_pad_y.pack(side="left", padx=(2,10))
        
        ttk.Label(r2, text="Idx Offset:", foreground="purple").pack(side="left")
        self.entry_start_offset = ttk.Entry(r2, width=4); self.entry_start_offset.insert(0,"0"); self.entry_start_offset.pack(side="left")

        # Initialize state
        self.toggle_custom_grid_inputs()

        # TAB 2: EXCEPTIONS
        self.tab_ex = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ex, text="Individual Exceptions")
        self.lbl_ex_info = ttk.Label(self.tab_ex, text="Fix characters that are bigger than the grid.", foreground="gray")
        self.lbl_ex_info.pack(pady=5)

        self.frame_ex_sel = ttk.Frame(self.tab_ex)
        self.frame_ex_sel.pack(fill="x", padx=10)
        ttk.Label(self.frame_ex_sel, text="Select Source Char Index:").pack(side="left")
        
        self.char_list = []
        for i in range(0, 256): 
            char_vis = chr(i + 32) if i + 32 < 127 else "?"
            if i+32 == 32: char_vis = "Space"
            self.char_list.append(f"{i} : [{char_vis}]")
            
        self.combo_char = ttk.Combobox(self.frame_ex_sel, values=self.char_list, state="readonly", width=18)
        self.combo_char.current(12) 
        self.combo_char.pack(side="left", padx=5)

        self.frame_ex_opt = ttk.LabelFrame(self.tab_ex, text="Modify Cut Box for this Char", padding=10)
        self.frame_ex_opt.pack(padx=10, pady=10, fill="x")
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
        self.tree = ttk.Treeview(self.tab_ex, columns=("ID", "Char", "Mods"), show='headings', height=8)
        self.tree.heading("ID", text="Source ID"); self.tree.column("ID", width=60)
        self.tree.heading("Char", text="Ref Char"); self.tree.column("Char", width=60)
        self.tree.heading("Mods", text="Modifications"); self.tree.column("Mods", width=200)
        self.tree.pack(padx=10, fill="both", expand=True)
        self.btn_del_ex = ttk.Button(self.tab_ex, text="Remove Selected", command=self.remove_exception)
        self.btn_del_ex.pack(pady=5)

        # TAB 3: RELOCATION
        self.tab_reloc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reloc, text="Character Relocation")
        ttk.Label(self.tab_reloc, text="Map a Source Index to a different Target Index.", foreground="gray").pack(pady=5)
        self.frame_reloc_input = ttk.LabelFrame(self.tab_reloc, text="Create Mapping", padding=10)
        self.frame_reloc_input.pack(fill="x", padx=10)
        ttk.Label(self.frame_reloc_input, text="Put Source ID:").grid(row=0, column=0)
        self.entry_reloc_src = ttk.Entry(self.frame_reloc_input, width=5); self.entry_reloc_src.grid(row=0, column=1, padx=5)
        ttk.Label(self.frame_reloc_input, text="Into Target Position:").grid(row=0, column=2)
        self.combo_reloc_target = ttk.Combobox(self.frame_reloc_input, values=self.char_list, state="readonly", width=18)
        self.combo_reloc_target.current(33)
        self.combo_reloc_target.grid(row=0, column=3, padx=5)
        ttk.Button(self.frame_reloc_input, text="Set Mapping", command=self.add_mapping).grid(row=0, column=4, padx=10)
        self.tree_reloc = ttk.Treeview(self.tab_reloc, columns=("TID", "TChar", "SID"), show='headings', height=8)
        self.tree_reloc.heading("TID", text="Target ID"); self.tree_reloc.column("TID", width=60)
        self.tree_reloc.heading("TChar", text="Target Char"); self.tree_reloc.column("TChar", width=80)
        self.tree_reloc.heading("SID", text="Uses Source ID"); self.tree_reloc.column("SID", width=80)
        self.tree_reloc.pack(padx=10, pady=10, fill="both", expand=True)
        self.btn_del_reloc = ttk.Button(self.tab_reloc, text="Remove Selected Mapping", command=self.remove_mapping)
        self.btn_del_reloc.pack(pady=5)

        # TAB 4: ABOUT
        self.tab_about = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_about, text="About")
        try:
            self.about_icon_pil = Image.open("bmfr.ico").resize((128, 128), Image.Resampling.NEAREST)
            self.about_icon_tk = ImageTk.PhotoImage(self.about_icon_pil)
            icon_label = ttk.Label(self.tab_about, image=self.about_icon_tk)
            icon_label.pack(pady=0)
        except Exception as e:
            print(f"Failed to load icon: {e}")
            ttk.Label(self.tab_about, text="Icon not available", foreground="gray").pack(pady=0)
        self.frame_program = ttk.LabelFrame(self.tab_about, text="Program info", padding=3)
        self.frame_program.pack(padx=10, pady=3, fill="x")
        self.lbl_program_info = ttk.Label(self.frame_program, text="Bitmap Font Cropper/Repacker v6.1.1\nIntended to be used in OldSkool DemoMaker or CODEF projects.\nPlease use charsets that have the ASCII character order format in order to reduce repacking mismatches\n(ex: From The Spriters Resource or bmf.wz.cz).", foreground="black")
        self.lbl_program_info.pack(pady=3)
        self.frame_auth = ttk.LabelFrame(self.tab_about, text="Authors", padding=3)
        self.frame_auth.pack(padx=10, pady=3, fill="x")
        self.lbl_auth_info = ttk.Label(self.frame_auth, text="FakeCells Software - Lead programming\nKelleesh24 - Script Supervisor\nLord Louvre - Script Contributions\nThird-party - Betatesting and feedback scripting", foreground="black")
        self.lbl_auth_info.pack(pady=3)
        self.frame_libs = ttk.LabelFrame(self.tab_about, text="Software used", padding=3)
        self.frame_libs.pack(padx=10, pady=3, fill="x")
        self.lbl_lib_info = ttk.Label(self.frame_libs, text="Pillow - by Jeffrey A. Clark and others (https://pypi.org/project/pillow/)\nThonny - by Aivar Annamaa (https://thonny.org/)", foreground="black")
        self.lbl_lib_info.pack(pady=3)
        self.frame_src = ttk.LabelFrame(self.tab_about, text="Support methods", padding=3)
        self.frame_src.pack(padx=10, pady=3, fill="x")
        self.lbl_src_info = ttk.Label(self.frame_src, text="You can support our project or contributors through our GitHub pages:\nhttps://github.com/FakeCells/bitmap-cropper\nhttps://github.com/Kelleesh24/", foreground="black")
        self.lbl_src_info.pack(pady=3)

        # BOTTOM BUTTONS
        self.frame_actions = ttk.Frame(root)
        self.frame_actions.pack(padx=10, pady=10, fill="x", side="bottom")
        self.btn_preview = ttk.Button(self.frame_actions, text="PREVIEW CUTS", command=self.open_preview_window)
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=5)
        self.btn_process = ttk.Button(self.frame_actions, text="SAVE REPACKED FONT", command=self.process_image)
        self.btn_process.pack(side="left", fill="x", expand=True, padx=5)
        
    def toggle_custom_grid_inputs(self, event=None):
        if "Custom" in self.combo_spacing.get():
            self.entry_cust_cols.config(state="normal")
            self.entry_cust_rows.config(state="normal")
        else:
            self.entry_cust_cols.config(state="disabled")
            self.entry_cust_rows.config(state="disabled")
        # Refresh preview because grid changed
        self.refresh_preview_if_open()

    # --- LOGIC ---

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.bmp")])
        if path:
            self.source_image_path = path
            self.source_filename = os.path.splitext(os.path.basename(path))[0]
            self.lbl_file_status.config(text=path.split("/")[-1], foreground="green")
            self.source_image = Image.open(path).convert("RGBA")
            self.refresh_preview_if_open()

    def choose_mask_color(self):
        c = colorchooser.askcolor()
        if c[0]:
            self.mask_color = tuple(map(int, c[0]))
            self.mask_canvas.config(bg=c[1])
            self.refresh_preview_if_open()

    def auto_detect_grid(self):
        """ Scans for the first character by checking against the background color (0,0) """
        if not self.source_image: return
        
        img = self.source_image
        w, h = img.size
        pixels = img.load()
        
        # 1. Determine Background Color (Assume top-left pixel is background)
        bg = pixels[0, 0] 
        # If mask is active, use that instead
        if self.var_use_mask.get() and self.mask_color:
            target = self.mask_color[:3]
        else:
            target = bg[:3] # Use RGB part

        def is_ink(x, y):
            # Returns True if pixel is NOT the background
            p = pixels[x, y]
            if len(p) == 4 and p[3] == 0: return False # Transparent
            if p[:3] == target: return False # Matches Background
            return True

        # 2. Scan for Top Margin (Start Y)
        start_y = 0
        found_y = False
        for y in range(h):
            for x in range(w):
                if is_ink(x, y):
                    start_y = y
                    found_y = True
                    break
            if found_y: break
            
        if not found_y: 
            messagebox.showinfo("Auto-Detect", "Image appears to be blank or fully background color."); return

        # 3. Scan for Left Margin (Start X) at the specific Start Y line
        start_x = 0
        found_x = False
        for x in range(w):
            # Scan a vertical strip of 5 pixels to be safe against thin characters
            for sample_y in range(start_y, min(start_y + 5, h)):
                if is_ink(x, sample_y):
                    start_x = x
                    found_x = True
                    break
            if found_x: break

        # 4. Measure Width (Scan Right until we hit background again)
        char_w = 0
        # Start scanning from the first ink pixel found
        for x in range(start_x, w):
            col_is_ink = False
            # Check the vertical strip again
            for sample_y in range(start_y, min(start_y + 5, h)):
                if is_ink(x, sample_y):
                    col_is_ink = True
                    break
            
            if not col_is_ink:
                # We hit a gap!
                char_w = x - start_x
                break
        if char_w == 0: char_w = w - start_x

        # 5. Measure Height (Scan Down until we hit background again)
        char_h = 0
        for y in range(start_y, h):
            row_is_ink = False
            # Check horizontal strip
            for sample_x in range(start_x, min(start_x + char_w, w)):
                if is_ink(sample_x, y):
                    row_is_ink = True
                    break
            
            if not row_is_ink:
                # We hit a gap!
                char_h = y - start_y
                break
        if char_h == 0: char_h = h - start_y

        # Update UI Inputs
        self.entry_off_x.delete(0, tk.END); self.entry_off_x.insert(0, str(start_x))
        self.entry_off_y.delete(0, tk.END); self.entry_off_y.insert(0, str(start_y))
        self.entry_char_w.delete(0, tk.END); self.entry_char_w.insert(0, str(char_w))
        self.entry_char_h.delete(0, tk.END); self.entry_char_h.insert(0, str(char_h))
        
        self.refresh_preview_if_open()
        messagebox.showinfo("Auto-Detect", f"Detected Glyph:\nStart: {start_x}, {start_y}\nSize: {char_w}x{char_h}")

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
        try:
            return {
                'cw': int(self.entry_char_w.get()), 'ch': int(self.entry_char_h.get()),
                'offx': int(self.entry_off_x.get()), 'offy': int(self.entry_off_y.get()),
                'gapx': int(self.entry_gap_x.get()), 'gapy': int(self.entry_gap_y.get()),
                'lsx': int(self.entry_lim_sx.get()), 'lsy': int(self.entry_lim_sy.get()),
                'lex': int(self.entry_lim_ex.get()), 'ley': int(self.entry_lim_ey.get()),
                'orient': self.combo_orientation.get(),
                'padx': int(self.entry_pad_x.get()), 'pady': int(self.entry_pad_y.get()),
                'start_offset': int(self.entry_start_offset.get()),
                'scale': float(self.combo_scale.get().replace("x",""))
            }
        except: return None

    def get_crop_data(self):
        if not self.source_image: return None
        cfg = self.get_config()
        if not cfg: return None
        
        proc_img = self.source_image.copy()
        if self.mask_color and self.var_use_mask.get():
            trgb = self.mask_color[:3]
            data = proc_img.getdata()
            new_data = [(0,0,0,0) if item[:3] == trgb else item for item in data]
            proc_img.putdata(new_data)
            
        # Calc boxes
        boxes = []
        w, h = proc_img.size
        
        # Grid settings
        sel = self.combo_spacing.get()
        
        if "Custom" in sel:
            # --- NEW CUSTOM LOGIC ---
            try:
                cols = int(self.entry_cust_cols.get())
                rows = int(self.entry_cust_rows.get())
            except ValueError:
                cols, rows = 20, 6 # Fallback
        else:
            # --- PRESET LOGIC ---
            if "8x8" in sel: t_w, t_h, t_tile = 320, 16, 8
            elif "32x32" in sel: t_w, t_h, t_tile = 320, 192, 32
            else: t_w, t_h, t_tile = 320, 48, 16 # Default 16x16 ref
            cols = t_w // t_tile
            rows = t_h // t_tile
            
        needed = cols * rows
        
        stride_x = cfg['cw'] + cfg['gapx']
        stride_y = cfg['ch'] + cfg['gapy']
        count = 0
        use_limits = self.var_use_limits.get()
        
        if "Horizontal" in cfg['orient']:
            cy = cfg['offy']
            while cy < h and count < needed:
                if use_limits and cy > cfg['ley']: break
                cx = cfg['offx']
                while cx < w and count < needed:
                    if use_limits and cx > cfg['lex']: break
                    valid = True
                    if use_limits and (cy < cfg['lsy'] or cx < cfg['lsx']): valid = False
                    
                    if valid:
                        boxes.append(self.calculate_box(cx, cy, cfg, count))
                        count += 1
                    cx += stride_x
                cy += stride_y
        else: # Vertical
            cx = cfg['offx']
            while cx < w and count < needed:
                if use_limits and cx > cfg['lex']: break
                cy = cfg['offy']
                while cy < h and count < needed:
                    if use_limits and cy > cfg['ley']: break
                    valid = True
                    if use_limits and (cy < cfg['lsy'] or cx < cfg['lsx']): valid = False
                    
                    if valid:
                        boxes.append(self.calculate_box(cx, cy, cfg, count))
                        count += 1
                    cy += stride_y
                cx += stride_x
                
        return proc_img, boxes, cols, rows, cfg

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

    # --- PREVIEW LOGIC ---

    def open_preview_window(self):
        if not self.source_image: messagebox.showwarning("Warning!", "Load image first in order to preview."); return
        if self.preview_window is not None:
             try: self.preview_window.destroy()
             except: pass

        top = Toplevel(self.root)
        top.title("Charset cuts preview")
        top.geometry("560x420")
        self.preview_window = top
        
        # --- 1. Info Panel ---
        info_panel = ttk.Frame(top, padding=5, relief="ridge")
        info_panel.pack(side="top", fill="x")
        
        # Ridge frame to update.
        self.preview_info_label = ttk.Label(info_panel, text="Initializing...", font=("Arial", 9))
        self.preview_info_label.pack(anchor="w")
        # -----------------------------------------
        
        # 2. Controls
        ctl = ttk.Frame(top); ctl.pack(fill="x", pady=2)
        ttk.Label(ctl, text="Zoom:").pack(side="left", padx=5)
        for z in [1.0, 2.0, 3.0, 4.0]:
            ttk.Button(ctl, text=f"{z}x", width=4, command=lambda zz=z: self.set_zoom(zz)).pack(side="left")
            
        # 3. Canvas
        container = ttk.Frame(top); container.pack(fill="both", expand=True)
        self.preview_canvas = tk.Canvas(container, bg="#222")
        vs = ttk.Scrollbar(container, orient="vertical", command=self.preview_canvas.yview)
        hs = ttk.Scrollbar(container, orient="horizontal", command=self.preview_canvas.xview)
        self.preview_canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side="right", fill="y"); hs.pack(side="bottom", fill="x")
        self.preview_canvas.pack(fill="both", expand=True)
        
        # 4. Status Bar
        status_frame = ttk.Frame(top, padding=5, relief="sunken")
        status_frame.pack(side="bottom", fill="x")
        self.lbl_coords = ttk.Label(status_frame, text="X: 0 | Y: 0", font=("Consolas", 10, "bold"))
        self.lbl_coords.pack(side="left")
        ttk.Label(status_frame, text=" | Red: Source Cuts | Magenta: Relocated | Blue: Limits", foreground="gray").pack(side="left")
        
        # Bindings
        self.preview_canvas.bind("<Button-1>", self.on_preview_click)
        self.preview_canvas.bind("<Motion>", self.on_preview_mouse_move) 
        
        self.refresh_preview_if_open()
        
    def on_preview_mouse_move(self, event):
        # Calculate real coordinates based on current zoom
        cx = self.preview_canvas.canvasx(event.x)
        cy = self.preview_canvas.canvasy(event.y)
        real_x = int(cx / self.preview_zoom)
        real_y = int(cy / self.preview_zoom)
        self.lbl_coords.config(text=f"X: {real_x} | Y: {real_y}")

    def set_zoom(self, z):
        self.preview_zoom = z
        self.refresh_preview_if_open()

    def refresh_preview_if_open(self, event=None):
        if self.preview_window is None or not tk.Toplevel.winfo_exists(self.preview_window):
            return
        
        data = self.get_crop_data()
        if not data: return
        img, boxes, cols, rows, cfg = data
        self.preview_boxes = boxes 
        
        # --- Update Info Label Text ---
        i_text = f"Char: {cfg['cw']}x{cfg['ch']} | Gaps: {cfg['gapx']},{cfg['gapy']} | Offsets: {cfg['offx']},{cfg['offy']} | Target: {cols}x{rows} grid"
        if cfg['padx'] or cfg['pady']: 
            i_text += f" | Padding: {cfg['padx']},{cfg['pady']}"
        
        # Update the label inside the ridge frame
        self.preview_info_label.config(text=i_text)
        # --------------------------------------------------
        
        # Draw boxes on copy
        prev = img.copy()
        draw = ImageDraw.Draw(prev)
        relocs = self.relocation_map.values() 
        
        for i, b in enumerate(boxes):
            col = "magenta" if i in relocs else "red"
            draw.rectangle(b, outline=col)
            
        if self.var_use_limits.get():
            draw.rectangle((cfg['lsx'], cfg['lsy'], cfg['lex'], cfg['ley']), outline="blue", width=2)
            
        # Resize for zoom
        w, h = prev.size
        nw, nh = int(w * self.preview_zoom), int(h * self.preview_zoom)
        prev_zoomed = prev.resize((nw, nh), Image.Resampling.NEAREST)
        
        self.preview_image_ref = ImageTk.PhotoImage(prev_zoomed)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, image=self.preview_image_ref, anchor="nw")
        self.preview_canvas.config(scrollregion=(0,0,nw,nh))

    def on_preview_click(self, event):
        # Translate canvas click to image coordinates
        cx = self.preview_canvas.canvasx(event.x)
        cy = self.preview_canvas.canvasy(event.y)
        real_x = int(cx / self.preview_zoom)
        real_y = int(cy / self.preview_zoom)
        
        # Hit test boxes
        found_idx = -1
        for i, b in enumerate(self.preview_boxes):
            if b[0] <= real_x <= b[2] and b[1] <= real_y <= b[3]:
                found_idx = i
                break
        
        if found_idx != -1:
            # Switch tab and fill entry
            self.notebook.select(self.tab_reloc)
            self.entry_reloc_src.delete(0, tk.END)
            self.entry_reloc_src.insert(0, str(found_idx))
            # Optional: Visual feedback
            self.root.bell()

    # --- PROCESSING --- (Same as V5.0)
    def process_image(self):
        try:
            if not self.source_image: messagebox.showwarning("!", "Load image first"); return
            data = self.get_crop_data()
            if not data: return
            img, boxes, cols, rows, cfg = data
            
            src_glyphs = [img.crop(b) for b in boxes]
            if not src_glyphs: messagebox.showwarning("!", "No chars found"); return
            
            cw, ch = cfg['cw'] + cfg['padx'], cfg['ch'] + cfg['pady']
            out_w = cols * cfg['cw']
            out_h = rows * cfg['ch']
            out_img = Image.new("RGBA", (cols*cw, rows*ch))
            
            for t_idx in range(cols*rows):
                if t_idx < cfg['start_offset']: continue
                l_idx = t_idx - cfg['start_offset']
                s_idx = self.relocation_map.get(l_idx, l_idx)
                
                if s_idx < len(src_glyphs):
                    g = src_glyphs[s_idx]
                    r, c = divmod(t_idx, cols)
                    px = c * cw + cfg['padx']//2
                    py = r * ch + cfg['pady']//2
                    out_img.paste(g, (px, py), g)
            
            if cfg['scale'] != 1.0:
                ow, oh = out_img.size
                out_img = out_img.resize((int(ow*cfg['scale']), int(oh*cfg['scale'])), Image.Resampling.NEAREST)
                
            default_name = f"{self.source_filename}-repacked.png" if self.source_image_path else "repacked.png"
            path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=default_name, filetypes=[("PNG", "*.png")])
            if path:
                out_img.save(path)
                msg = (f"The repacked charset has been saved succesfully!\n\n"
                       f"Grid Layout: {cols} Cols x {rows} Rows\n"
                       f"Output Size: {out_w}x{out_h}\n"
                       f"Mask Applied: {'Yes' if self.mask_color else 'No'}\n"
                       f"Saved to: {path}")
                messagebox.showinfo("Done", msg)
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = BitmapCropperApp(root)
    root.mainloop()