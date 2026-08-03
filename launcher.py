import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import threading
import sys
import random

class TronLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Tron AI - Match Launcher")
        self.root.geometry("650x550") 
        self.root.configure(bg="#1e1e2e")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12, "bold"), background="#89b4fa", foreground="#11111b")
        
        left_frame = tk.Frame(root, bg="#1e1e2e")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)
        
        ttk.Label(left_frame, text="Select Map:").pack(anchor=tk.W)
        self.map_listbox = tk.Listbox(left_frame, bg="#313244", fg="#cdd6f4", selectbackground="#89b4fa", font=("Arial", 11), width=22, height=15)
        self.map_listbox.pack(pady=5)
        self.map_listbox.bind('<<ListboxSelect>>', self.on_map_select)
        
        self.gen_btn = ttk.Button(left_frame, text="✨ Generate Map", command=self.generate_map)
        self.gen_btn.pack(fill=tk.X, pady=10)
        
        right_frame = tk.Frame(root, bg="#1e1e2e")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(right_frame, text="Map Preview:").pack(anchor=tk.W)
        
        self.preview_canvas = tk.Canvas(right_frame, width=280, height=280, bg="#11111b", highlightthickness=1, highlightbackground="#45475a")
        self.preview_canvas.pack(pady=10)
        
        ttk.Label(right_frame, text="Number of Agents:").pack(anchor=tk.W, pady=(10, 0))
        self.agents_var = tk.StringVar(value="4")
        agents_combo = ttk.Combobox(right_frame, textvariable=self.agents_var, values=["2", "4", "6", "8"], state="readonly", width=10)
        agents_combo.pack(anchor=tk.W, pady=5)
        
        self.launch_btn = ttk.Button(right_frame, text="LAUNCH MATCH", command=self.start_pipeline)
        self.launch_btn.pack(fill=tk.X, pady=20)

        self.load_maps()

    def generate_map(self):
        if not os.path.exists("maps"):
            os.makedirs("maps")
            
        W = random.randint(15, 25)
        H = random.randint(15, 25)
        
        grid = [['.' for _ in range(W)] for _ in range(H)]

        num_walls_half = int((W * H) * 0.1 / 2)

        for _ in range(num_walls_half):
            rx = random.randint(0, W - 1)
            ry = random.randint(0, H // 2 - 1)
            grid[ry][rx] = '#'
            
            sym_x = W - 1 - rx
            sym_y = H - 1 - ry
            grid[sym_y][sym_x] = '#'
            
        base_name = f"{W}x{H}"
        filename = f"maps/{base_name}.txt"
        counter = 1
        
        while os.path.exists(filename):
            filename = f"maps/{base_name}_{counter}.txt"
            counter += 1
            
        with open(filename, 'w') as f:
            f.write(f"{W} {H}\n")
            for row in grid:
                f.write("".join(row) + "\n")
                
        map_display_name = os.path.basename(filename)
        self.map_listbox.insert(tk.END, map_display_name)
        
        last_idx = self.map_listbox.size() - 1
        self.map_listbox.selection_clear(0, tk.END)
        self.map_listbox.selection_set(last_idx)
        self.on_map_select(None)

    def load_maps(self):
        if not os.path.exists("maps"):
            os.makedirs("maps")
            
        maps = [f for f in os.listdir("maps") if f.endswith('.txt')]
        self.map_listbox.delete(0, tk.END)
        for m in maps:
            self.map_listbox.insert(tk.END, m)
            
        if maps:
            self.map_listbox.selection_set(0)
            self.on_map_select(None)

    def on_map_select(self, event):
        selection = self.map_listbox.curselection()
        if not selection: return
        
        map_name = self.map_listbox.get(selection[0])
        map_path = os.path.join("maps", map_name)
        
        self.preview_canvas.delete("all")
        try:
            with open(map_path, 'r') as f:
                lines = f.readlines()
                w, h = map(int, lines[0].split())
                
                cell_w = 280 / w
                cell_h = 280 / h
                
                for y in range(h):
                    row = lines[y+1].strip()
                    for x in range(w):
                        if row[x] == '#':
                            self.preview_canvas.create_rectangle(x*cell_w, y*cell_h, (x+1)*cell_w, (y+1)*cell_h, fill="#7f849c", outline="")
        except Exception as e:
            print(f"Error loading preview: {e}")

    def start_pipeline(self):
        selection = self.map_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a map first!")
            return
            
        map_path = os.path.join("maps", self.map_listbox.get(selection[0]))
        num_agents = self.agents_var.get()
        
        self.launch_btn.config(text="⏳ COMPILING...", state=tk.DISABLED)
        threading.Thread(target=self.run_engine, args=(map_path, num_agents), daemon=True).start()

    def run_engine(self, map_path, num_agents):
        try:
            
            self.root.after(0, lambda: self.launch_btn.config(text="⚔️ PLAYING MATCH..."))
            subprocess.run(["./tron", map_path, num_agents], check=True)
            
            self.root.after(0, lambda: self.launch_btn.config(text="🎬 LAUNCHING REPLAY..."))
            subprocess.Popen([sys.executable, "vis.py", "replays/latest.txt"])
            
            self.root.after(0, lambda: self.launch_btn.config(text="LAUNCH MATCH", state=tk.NORMAL))
            
        except subprocess.CalledProcessError as e:
            self.root.after(0, lambda: messagebox.showerror("Engine Error", f"C++ crashed!\n{e}"))
            self.root.after(0, lambda: self.launch_btn.config(text="LAUNCH MATCH", state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = TronLauncher(root)
    root.mainloop()