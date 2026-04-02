import customtkinter as ctk

class FlavorImageTab(ctk.CTkFrame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api

        # Chia lam 2 cot: Flavor (Trai) va Image (Phai)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="1. Thống kê Flavor & Image", font=("Roboto", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=10, sticky="w", padx=10)

        self.frame_flavors = ctk.CTkScrollableFrame(self, label_text="Danh sách Flavor (Cấu hình)")
        self.frame_flavors.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.frame_images = ctk.CTkScrollableFrame(self, label_text="Danh sách Image (Hệ điều hành)")
        self.frame_images.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkButton(self, text="Làm mới dữ liệu", command=self.load_data).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Tu dong load data khi khoi tao tab
        self.load_data()

    def load_data(self):
        # Xoa UI cu
        for w in self.frame_flavors.winfo_children(): w.destroy()
        for w in self.frame_images.winfo_children(): w.destroy()

        # Load Flavor
        for f in self.api.get_flavors():
            info = f"Tên: {f['name']} | RAM: {f['ram']}MB | Disk: {f['disk']}GB | vCPU: {f['vcpus']}"
            ctk.CTkLabel(self.frame_flavors, text=info).pack(anchor="w", padx=10, pady=2)
        
        # Load Image
        for i in self.api.get_images():
            info = f"Tên: {i['name']} | Trạng thái: {i['status']} | Size: {int(i.get('size', 0)/1024/1024)}MB"
            ctk.CTkLabel(self.frame_images, text=info).pack(anchor="w", padx=10, pady=2)
