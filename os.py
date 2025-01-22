import tkinter as tk
from tkinter import messagebox, simpledialog


class VirtualFileSystem:
    def __init__(self, disk_size, block_size):
        self.disk_size = disk_size  # Total size of the disk in bytes
        self.block_size = block_size  # Size of each block in bytes
        self.num_blocks = disk_size // block_size  # Total number of blocks
        self.fat = [-1] * self.num_blocks  # File Allocation Table (-1 = free block)
        self.directory = {}  # Directory to store file metadata {filename: [start_block, size, pointer]}
        self.disk = [""] * self.num_blocks  # Simulated disk storage (list of block data)

    def create_file(self, filename, size):
        if filename in self.directory:
            return f"File '{filename}' already exists."

        blocks_needed = -(-size // self.block_size)  # Ceiling division for required blocks
        free_blocks = [i for i, v in enumerate(self.fat) if v == -1]

        if len(free_blocks) < blocks_needed:
            return f"Not enough space to create file '{filename}'."

        # Allocate blocks
        allocated_blocks = free_blocks[:blocks_needed]
        for i in range(len(allocated_blocks) - 1):
            self.fat[allocated_blocks[i]] = allocated_blocks[i + 1]
        self.fat[allocated_blocks[-1]] = -2  # End of file marker

        # Update directory
        self.directory[filename] = [allocated_blocks[0], size, 0]  # Pointer starts at position 0
        return f"File '{filename}' created successfully."

    def delete_file(self, filename):
        if filename not in self.directory:
            return f"File '{filename}' does not exist."

        start_block = self.directory[filename][0]
        while start_block != -2:
            next_block = self.fat[start_block]
            self.fat[start_block] = -1  # Free the block
            start_block = next_block

        del self.directory[filename]
        return f"File '{filename}' deleted successfully."

    def fseek(self, filename, position):
        if filename not in self.directory:
            return f"File '{filename}' does not exist."

        _, size, _ = self.directory[filename]
        if position < 0 or position >= size:
            return f"Position {position} is out of bounds for file '{filename}'."

        self.directory[filename][2] = position
        return f"File pointer moved to position {position} in file '{filename}'."

    def read_file(self, filename):
        if filename not in self.directory:
            return f"File '{filename}' does not exist."

        start_block, size, pointer = self.directory[filename]
        remaining_size = size - pointer
        read_data = []

        current_block = start_block
        block_offset = pointer // self.block_size

        # Traverse blocks to reach the pointer position
        for _ in range(block_offset):
            current_block = self.fat[current_block]

        # Read data
        while remaining_size > 0 and current_block != -2:
            data = self.disk[current_block] or ""
            read_data.append(data[:remaining_size])
            remaining_size -= len(data)
            current_block = self.fat[current_block]

        return f"Data read from '{filename}': {''.join(read_data)}"

    def write_file(self, filename, data):
        if filename not in self.directory:
            return f"File '{filename}' does not exist."

        start_block, size, pointer = self.directory[filename]
        remaining_size = size - pointer

        if len(data) > remaining_size:
            return f"Insufficient space to write data in '{filename}'."

        current_block = start_block
        block_offset = pointer // self.block_size

        # Traverse blocks to reach the pointer position
        for _ in range(block_offset):
            current_block = self.fat[current_block]

        # Write data
        write_pointer = pointer
        for char in data:
            if write_pointer % self.block_size == 0 and write_pointer != pointer:
                current_block = self.fat[current_block]
            self.disk[current_block] += char
            write_pointer += 1

        self.directory[filename][2] = write_pointer
        return f"Data written to '{filename}' successfully."

    def show_fat(self):
        return self.fat

    def show_directory(self):
        return self.directory


class VFSApp:
    def __init__(self, root, vfs):
        self.root = root
        self.vfs = vfs
        self.root.title("Virtual File System with FAT")
        self.root.geometry("800x650")
        self.root.config(bg="#f0f0f0")

        # File operations
        self.create_button = self.create_button_widget(root, "Create File", self.create_file)
        self.delete_button = self.create_button_widget(root, "Delete File", self.delete_file)
        self.read_button = self.create_button_widget(root, "Read File", self.read_file)
        self.write_button = self.create_button_widget(root, "Write to File", self.write_file)
        self.fseek_button = self.create_button_widget(root, "Seek (fseek)", self.fseek)
        self.fat_button = self.create_button_widget(root, "Show FAT", self.show_fat)
        self.dir_button = self.create_button_widget(root, "Show Directory", self.show_directory)

        # Output display
        self.output = tk.Text(root, height=7, width=80, font=("Courier", 12), wrap=tk.WORD)
        self.output.pack(pady=1)

        # Memory block visualization
        self.block_canvas = tk.Canvas(root, width=800, height=100, bg="#e6e6e6", bd=0)
        self.block_canvas.pack(pady=10)
        self.block_rects = []
        self.draw_blocks()

    def create_button_widget(self, root, text, command):
        """Helper function to create a styled button."""
        button = tk.Button(root, text=text, command=command, height=2, width=20, font=("Arial", 12, "bold"),
                           bg="#4CAF50", fg="white", relief="flat", padx=1, pady=1)
        button.pack(pady=1)
        return button

    def draw_blocks(self):
        """Draw blocks representing the memory."""
        self.block_canvas.delete("all")
        block_width = 800 // self.vfs.num_blocks
        for i in range(self.vfs.num_blocks):
            color = "green" if self.vfs.fat[i] == -1 else "red"
            rect = self.block_canvas.create_rectangle(
                i * block_width,
                50,
                (i + 1) * block_width,
                100,
                fill=color,
                outline="black"
            )
            self.block_canvas.create_text(
                i * block_width + block_width // 2,
                120,
                text=f"B{i}",
                font=("Arial", 10)
            )
            self.block_rects.append(rect)

    def create_file(self):
        details = simpledialog.askstring("Create File", "Enter file name and size (e.g., file1 200):")
        if details:
            try:
                filename, size = details.split()
                size = int(size)
                result = self.vfs.create_file(filename, size)
                self.output.insert(tk.END, result + "\n")
                self.draw_blocks()
            except ValueError:
                messagebox.showerror("Error", "Invalid input format. Use: filename size")

    def delete_file(self):
        filename = simpledialog.askstring("Delete File", "Enter file name:")
        if filename:
            result = self.vfs.delete_file(filename)
            self.output.insert(tk.END, result + "\n")
            self.draw_blocks()

    def fseek(self):
        # Prompt user for file name and new pointer position
        filename = simpledialog.askstring("Seek (fseek)", "Enter file name:")
        if filename:
            # Prompt for new pointer position
            position = simpledialog.askinteger("Seek (fseek)", "Enter position to move pointer:")
            if position is not None:
                # Call fseek method in VFS with filename and new pointer position
                result = self.vfs.fseek(filename, position)
                self.output.insert(tk.END, result + "\n")

    def read_file(self):
        filename = simpledialog.askstring("Read File", "Enter file name:")
        if filename:
            result = self.vfs.read_file(filename)
            self.output.insert(tk.END, result + "\n")

    def write_file(self):
        filename = simpledialog.askstring("Write to File", "Enter file name:")
        data = simpledialog.askstring("Write to File", "Enter data to write:")
        if filename and data:
            result = self.vfs.write_file(filename, data)
            self.output.insert(tk.END, result + "\n")

    def show_fat(self):
        fat = self.vfs.show_fat()
        self.output.insert(tk.END, f"FAT Table: {fat}\n")

    def show_directory(self):
        directory = self.vfs.show_directory()
        self.output.insert(tk.END, f"Directory: {directory}\n")


if __name__ == "__main__":
    disk_size = 2048 # 1 KB virtual disk
    block_size = 64   # 64 bytes per block
    vfs = VirtualFileSystem(disk_size, block_size)

    root = tk.Tk()
    app = VFSApp(root, vfs)
    root.mainloop()