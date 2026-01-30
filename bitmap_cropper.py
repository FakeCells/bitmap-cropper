import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import re

class BitmapCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitmap Font Repacker")
        self.root.geometry("500x550")
        
        # Variables
        self.source_image_path = None
        self.source_image = None
        
        # --- UI Layout ---
        
        # 1. File Selection
        self.frame_file = tk.LabelFrame(root, text="1. Import Font Image", padx=10, pady=10)
        self.frame_file.pack(padx=10, pady=5, fill="x")
        
        self.btn_load = tk.Button(self.frame_file, text="Select Image", command=self.load_image)
        self.btn_load.pack(side="left")
        
        self.lbl_file_status = tk.Label(self.frame_file, text="No file selected", fg="gray")
        self.lbl_file_status.pack(side="left", padx=10)

        # 2. Source Character Configuration
        self.frame_config = tk.LabelFrame(root, text="2. Character Configuration", padx=10, pady=10)
        self.frame_config.pack(padx=10, pady=5, fill="x")

        # Grid for inputs
        tk.Label(self.frame_config, text="Char Width (px):").grid(row=0, column=0, sticky="e")
        self.entry_char_w = tk.Entry(self.frame_config, width=10)
        self.entry_char_w.insert(0, "8")
        self.entry_char_w.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.frame_config, text="Char Height (px):").grid(row=0, column=2, sticky="e")
        self.entry_char_h = tk.Entry(self.frame_config, width=10)
        self.entry_char_h.insert(0, "16")
        self.entry_char_h.grid(row=0, column=3, padx=5, pady=5)

        # 3. Charset Spacing / Grid Layout
        self.frame_layout = tk.LabelFrame(root, text="3. Target Charset Spacing", padx=10, pady=10)
        self.frame_layout.pack(padx=10, pady=5, fill="x")

        tk.Label(self.frame_layout, text="Select Standard:").pack(anchor="w")
        
        # Options as requested + a way to type custom
        self.spacing_options = [
            "320x16 (8x8 ref)", 
            "320x48 (16x16 ref)", 
            "320x192 (32x32 ref)",
            "Custom (Calculate manually)"
        ]
        
        self.combo_spacing = ttk.Combobox(self.frame_layout, values=self.spacing_options, state="readonly")
        self.combo_spacing.current(1) # Default to second option
        self.combo_spacing.pack(fill="x", pady=5)
        self.combo_spacing.bind("<<ComboboxSelected>>", self.toggle_custom_layout)

        # Custom manual override inputs (hidden by default)
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

        # 4. Process
        self.btn_process = tk.Button(root, text="CROP AND SAVE", command=self.process_image, bg="#dddddd", height=2)
        self.btn_process.pack(padx=10, pady=20, fill="x")
        
        # 5. Output Log
        self.lbl_info = tk.Label(root, text="Ready...", fg="blue", wraplength=480)
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
            try:
                self.source_image = Image.open(file_path)
                w, h = self.source_image.size
                self.lbl_info.config(text=f"Loaded Image: {w}x{h} px")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def get_grid_dimensions(self):
        """Calculates Columns and Rows based on selection"""
        selection = self.combo_spacing.get()
        
        ref_w, ref_h, ref_tile = 0, 0, 0

        if "Custom" in selection:
            try:
                ref_w = int(self.entry_ref_w.get())
                ref_h = int(self.entry_ref_h.get())
                ref_tile = int(self.entry_ref_tile.get())
            except ValueError:
                raise ValueError("Please enter valid integers for Custom Layout.")
        else:
            # Parse string like "320x48 (16x16 ref)"
            # Regex to find numbers. Expected format: WxH (TxT
            parts = re.findall(r'\d+', selection)
            if len(parts) >= 3:
                ref_w = int(parts[0])
                ref_h = int(parts[1])
                ref_tile = int(parts[2]) # The first number in parenthesis
            else:
                raise ValueError("Could not parse preset format.")

        cols = ref_w // ref_tile
        rows = ref_h // ref_tile
        
        return cols, rows

    def process_image(self):
        if not self.source_image:
            messagebox.showwarning("Warning", "Please import an image first.")
            return

        try:
            # 1. Get Inputs
            char_w = int(self.entry_char_w.get())
            char_h = int(self.entry_char_h.get())
            
            # 2. Calculate Grid (Cols x Rows)
            cols, rows = self.get_grid_dimensions()
            
            total_slots = cols * rows
            
            # 3. Calculate Output Size
            out_w = cols * char_w
            out_h = rows * char_h
            
            # 4. Slice Source Image
            # We assume the source image is packed left-to-right, top-to-bottom
            src_w, src_h = self.source_image.size
            
            glyphs = []
            
            # Scan source image
            for y in range(0, src_h, char_h):
                for x in range(0, src_w, char_w):
                    if len(glyphs) >= total_slots:
                        break
                    
                    # Define crop box (left, upper, right, lower)
                    box = (x, y, x + char_w, y + char_h)
                    crop = self.source_image.crop(box)
                    glyphs.append(crop)
                if len(glyphs) >= total_slots:
                    break
            
            # 5. Create New Image
            new_img = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0)) # Transparent background
            
            # 6. Paste Glyphs into New Grid
            current_glyph_index = 0
            for r in range(rows):
                for c in range(cols):
                    if current_glyph_index < len(glyphs):
                        paste_x = c * char_w
                        paste_y = r * char_h
                        new_img.paste(glyphs[current_glyph_index], (paste_x, paste_y))
                        current_glyph_index += 1
            
            # 7. Save
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
            if save_path:
                new_img.save(save_path)
                msg = (f"Success!\n"
                       f"Grid Layout: {cols} Cols x {rows} Rows\n"
                       f"Output Size: {out_w}x{out_h}")
                self.lbl_info.config(text=msg, fg="green")
                messagebox.showinfo("Done", msg)
                
        except ValueError as ve:
            messagebox.showerror("Input Error", f"Invalid numbers: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            print(e)

if __name__ == "__main__":
    root = tk.Tk()
    app = BitmapCropperApp(root)
    root.mainloop()