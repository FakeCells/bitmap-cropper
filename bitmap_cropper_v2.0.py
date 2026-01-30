import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel, Canvas
from PIL import Image, ImageTk, ImageDraw

class BitmapCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitmap Font Repacker V2.0")
        self.root.geometry("600x450")  # Increased height for new options
        
        # Variables
        self.source_image_path = None
        self.source_image = None
        self.preview_image = None # To hold the reference for the preview window
        
        # --- UI Layout ---
        
        # 1. File Selection
        self.frame_file = tk.LabelFrame(root, text="1. Import Source Font", padx=10, pady=10)
        self.frame_file.pack(padx=10, pady=5, fill="x")
        
        self.btn_load = tk.Button(self.frame_file, text="Select Image", command=self.load_image)
        self.btn_load.pack(side="left")
        
        self.lbl_file_status = tk.Label(self.frame_file, text="No file selected", fg="gray")
        self.lbl_file_status.pack(side="left", padx=10)

        # 2. Character Size (The "Inner" size)
        self.frame_config = tk.LabelFrame(root, text="2. Character Size (WxH)", padx=10, pady=10)
        self.frame_config.pack(padx=10, pady=5, fill="x")

        tk.Label(self.frame_config, text="Width (px):").grid(row=0, column=0, sticky="e")
        self.entry_char_w = tk.Entry(self.frame_config, width=8)
        self.entry_char_w.insert(0, "8")
        self.entry_char_w.grid(row=0, column=1, padx=5)

        tk.Label(self.frame_config, text="Height (px):").grid(row=0, column=2, sticky="e")
        self.entry_char_h = tk.Entry(self.frame_config, width=8)
        self.entry_char_h.insert(0, "16")
        self.entry_char_h.grid(row=0, column=3, padx=5)

        # 3. Gaps & Offsets (New Feature)
        self.frame_gaps = tk.LabelFrame(root, text="3. Source Gaps & Offsets (The 'Size Over/Under' logic)", padx=10, pady=10)
        self.frame_gaps.pack(padx=10, pady=5, fill="x")

        # Row 1: Starting Offsets
        tk.Label(self.frame_gaps, text="Start Offset Y (Top):", fg="blue").grid(row=0, column=0, sticky="e")
        self.entry_off_y = tk.Entry(self.frame_gaps, width=5)
        self.entry_off_y.insert(0, "0")
        self.entry_off_y.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(self.frame_gaps, text="Start Offset X (Left):", fg="blue").grid(row=0, column=2, sticky="e")
        self.entry_off_x = tk.Entry(self.frame_gaps, width=5)
        self.entry_off_x.insert(0, "0")
        self.entry_off_x.grid(row=0, column=3, padx=5, pady=2)
        
        tk.Label(self.frame_gaps, text="(Use for 'Size Above' or Header)", fg="gray", font=("Arial", 8)).grid(row=0, column=4, sticky="w")

        # Row 2: Spacing
        tk.Label(self.frame_gaps, text="Gap Y (Line Height):", fg="red").grid(row=1, column=0, sticky="e")
        self.entry_gap_y = tk.Entry(self.frame_gaps, width=5)
        self.entry_gap_y.insert(0, "0")
        self.entry_gap_y.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(self.frame_gaps, text="Gap X (Char Space):", fg="red").grid(row=1, column=2, sticky="e")
        self.entry_gap_x = tk.Entry(self.frame_gaps, width=5)
        self.entry_gap_x.insert(0, "0")
        self.entry_gap_x.grid(row=1, column=3, padx=5, pady=2)

        tk.Label(self.frame_gaps, text="(Use for 'Size Under' or Spacing)", fg="gray", font=("Arial", 8)).grid(row=1, column=4, sticky="w")

        # 4. Target Layout
        self.frame_layout = tk.LabelFrame(root, text="4. Output Target Spacing", padx=10, pady=10)
        self.frame_layout.pack(padx=10, pady=5, fill="x")

        self.spacing_options = [
            "320x16 (8x8 ref) -> 20x2 Grid", 
            "320x48 (16x16 ref) -> 20x3 Grid", 
            "320x192 (32x32 ref) -> 10x6 Grid",
            "Custom (Calculate manually)"
        ]
        
        self.combo_spacing = ttk.Combobox(self.frame_layout, values=self.spacing_options, state="readonly", width=40)
        self.combo_spacing.current(1)
        self.combo_spacing.pack(fill="x", pady=5)
        self.combo_spacing.bind("<<ComboboxSelected>>", self.toggle_custom_layout)

        # Custom inputs
        self.frame_custom = tk.Frame(self.frame_layout)
        tk.Label(self.frame_custom, text="Ref Width:").pack(side="left")
        self.entry_ref_w = tk.Entry(self.frame_custom, width=5)
        self.entry_ref_w.pack(side="left", padx=2)
        tk.Label(self.frame_custom, text="Ref Height:").pack(side="left")
        self.entry_ref_h = tk.Entry(self.frame_custom, width=5)
        self.entry_ref_h.pack(side="left", padx=2)
        tk.Label(self.frame_custom, text="Ref Tile:").pack(side="left")
        self.entry_ref_tile = tk.Entry(self.frame_custom, width=5)
        self.entry_ref_tile.pack(side="left", padx=2)

        # 5. Actions
        self.frame_actions = tk.Frame(root)
        self.frame_actions.pack(padx=10, pady=20, fill="x")

        self.btn_preview = tk.Button(self.frame_actions, text="PREVIEW GRID", command=self.show_preview, bg="#fffFA0", height=2, width=15)
        self.btn_preview.pack(side="left", padx=5, fill="x", expand=True)

        self.btn_process = tk.Button(self.frame_actions, text="CROP AND SAVE", command=self.process_image, bg="#A0FFFA", height=2, width=15)
        self.btn_process.pack(side="left", padx=5, fill="x", expand=True)
        
        # Log
        self.lbl_info = tk.Label(root, text="Ready...", fg="blue", wraplength=550)
        self.lbl_info.pack(pady=5)

    def toggle_custom_layout(self, event=None):
        if self.combo_spacing.get().startswith("Custom"):
            self.frame_custom.pack(pady=10)
        else:
            self.frame_custom.pack_forget()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.bmp;*.gif")])
        if file_path:
            self.source_image_path = file_path
            self.lbl_file_status.config(text=file_path.split("/")[-1], fg="green")
            self.source_image = Image.open(file_path)
            w, h = self.source_image.size
            self.lbl_info.config(text=f"Loaded Image: {w}x{h} px")

    def get_grid_config(self):
        """Returns (cols, rows) for TARGET and input params for SOURCE"""
        # Source Params
        char_w = int(self.entry_char_w.get())
        char_h = int(self.entry_char_h.get())
        
        # Gap Params
        off_x = int(self.entry_off_x.get())
        off_y = int(self.entry_off_y.get())
        gap_x = int(self.entry_gap_x.get())
        gap_y = int(self.entry_gap_y.get())

        # Target Params
        selection = self.combo_spacing.get()
        if "Custom" in selection:
            ref_w = int(self.entry_ref_w.get())
            ref_h = int(self.entry_ref_h.get())
            ref_tile = int(self.entry_ref_tile.get())
        else:
            if "8x8 ref" in selection: ref_w, ref_h, ref_tile = 320, 16, 8
            elif "16x16 ref" in selection: ref_w, ref_h, ref_tile = 320, 48, 16
            elif "32x32 ref" in selection: ref_w, ref_h, ref_tile = 320, 192, 32
            else: ref_w, ref_h, ref_tile = 320, 48, 16
            
        cols = ref_w // ref_tile
        rows = ref_h // ref_tile
        
        return {
            'char_w': char_w, 'char_h': char_h,
            'off_x': off_x, 'off_y': off_y,
            'gap_x': gap_x, 'gap_y': gap_y,
            't_cols': cols, 't_rows': rows,
            't_width': cols * char_w,
            't_height': rows * char_h
        }

    def get_glyph_boxes(self, cfg, max_glyphs):
        """Calculates coordinates for source cropping"""
        boxes = []
        if not self.source_image: return []
        
        src_w, src_h = self.source_image.size
        
        # Calculate stride (size + gap)
        step_x = cfg['char_w'] + cfg['gap_x']
        step_y = cfg['char_h'] + cfg['gap_y']
        
        current_y = cfg['off_y']
        
        # We scan rows until we run out of image or hit max glyphs
        while current_y + cfg['char_h'] <= src_h:
            current_x = cfg['off_x']
            
            while current_x + cfg['char_w'] <= src_w:
                if len(boxes) >= max_glyphs:
                    return boxes
                
                # (left, upper, right, lower)
                box = (current_x, current_y, current_x + cfg['char_w'], current_y + cfg['char_h'])
                boxes.append(box)
                
                current_x += step_x
            
            current_y += step_y
            
        return boxes

    def show_preview(self):
        if not self.source_image:
            messagebox.showwarning("Warning", "Load image first.")
            return

        try:
            cfg = self.get_grid_config()
            target_count = cfg['t_cols'] * cfg['t_rows']
            
            # Get boxes
            boxes = self.get_glyph_boxes(cfg, max_glyphs=target_count)
            
            # Create preview image
            preview = self.source_image.copy().convert("RGBA")
            draw = ImageDraw.Draw(preview)
            
            # Draw rectangles
            for b in boxes:
                draw.rectangle(b, outline="red", width=1)
                
            # Show in new window
            top = Toplevel(self.root)
            top.title(f"Preview - Found {len(boxes)} / {target_count} Glyphs")
            
            # Scale for visibility if small
            scale = 1
            if preview.width < 300: scale = 2
            if preview.width < 150: scale = 4
            
            preview = preview.resize((preview.width * scale, preview.height * scale), Image.NEAREST)
            
            # Convert for Tkinter
            self.preview_tk = ImageTk.PhotoImage(preview) # Keep reference
            
            panel = tk.Label(top, image=self.preview_tk)
            panel.pack(padx=10, pady=10)
            
            lbl_instruct = tk.Label(top, text="Red boxes show characters to be cropped.\nAdjust Offsets/Gaps if they don't align.")
            lbl_instruct.pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def process_image(self):
        if not self.source_image:
            messagebox.showwarning("Warning", "Please import an image first.")
            return

        try:
            cfg = self.get_grid_config()
            target_count = cfg['t_cols'] * cfg['t_rows']
            
            # 1. Get Source Boxes
            boxes = self.get_glyph_boxes(cfg, max_glyphs=target_count)
            
            if len(boxes) == 0:
                messagebox.showerror("Error", "No characters found with current settings. Check offsets.")
                return

            # 2. Crop
            glyphs = [self.source_image.crop(b) for b in boxes]
            
            # 3. Create Output
            new_img = Image.new("RGBA", (cfg['t_width'], cfg['t_height']), (0, 0, 0, 0))
            
            curr_idx = 0
            for r in range(cfg['t_rows']):
                for c in range(cfg['t_cols']):
                    if curr_idx < len(glyphs):
                        px = c * cfg['char_w']
                        py = r * cfg['char_h']
                        new_img.paste(glyphs[curr_idx], (px, py))
                        curr_idx += 1
            
            # 4. Save
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
            if save_path:
                new_img.save(save_path)
                messagebox.showinfo("Done", f"Saved to {save_path}\nUsed {curr_idx} characters.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BitmapCropperApp(root)
    root.mainloop()